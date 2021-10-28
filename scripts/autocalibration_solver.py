""" 
@file: autocalibration_solver.py
@description:   python module autocalibrate anchor position based on inter-anchor ranging data
                This process takes an initial anchors coords guess as starting point of the iterative
                optimization.
@author: Esau Ortiz
@date: october 2021
@usage: python autocalibration_solver.py 
"""

import matplotlib.pyplot as plt
import numpy as np

def rotate_points(points, pitch = 0, roll = 0, yaw = 0):
    n_points = points.shape[0]

    cosa = np.cos(yaw)
    sina = np.sin(yaw)

    cosb = np.cos(pitch)
    sinb = np.sin(pitch)

    cosc = np.cos(roll)
    sinc = np.sin(roll)

    Axx = cosa*cosb
    Axy = cosa*sinb*sinc - sina*cosc
    Axz = cosa*sinb*cosc + sina*sinc

    Ayx = sina*cosb
    Ayy = sina*sinb*sinc + cosa*cosc
    Ayz = sina*sinb*cosc - cosa*sinc

    Azx = -sinb
    Azy = cosb*sinc
    Azz = cosb*cosc

    rotated_points = np.empty(points.shape)
    for idx in range(n_points):
        x, y, z = points[idx]

        x_r = Axx*x + Axy*y + Axz*z
        y_r = Ayx*x + Ayy*y + Ayz*z
        z_r = Azx*x + Azy*y + Azz*z
    
        rotated_points[idx] = [x_r, y_r, z_r]
    return rotated_points

def angle_bet_vectors(vector_1, vector_2):
    unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
    unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
    dot_product = np.dot(unit_vector_1, unit_vector_2)
    return np.arccos(dot_product)

def normL2(P, Q, params = None):
    """ Compute the euclidean distance bet two matrices
    Parameters
    ----------
    P: (N, M) array
    Q: (L, M) array
    params: Ignored
        Not used, present here for consistency
    Returns
    -------
    distance: (N, L) array
        distance between each element in P and all elements
        in Q as rows
    """
    return np.sqrt(np.einsum("ijk->ij", (P[:, None, :] - Q) ** 2))

def optimizedTagCoords(anchors_coords, anchors_distances):
        # build A matrix
        A = 2 * np.copy(anchors_coords)
        for i in range(A.shape[0] - 1): A[i] = A[-1] - A[i]
        A = A[:-1] # remove last row

        # build B matrix
        B = np.copy(anchors_distances)**2
        B = B[:-1] - B[-1] - np.sum(anchors_coords**2, axis = 1)[:-1] + np.sum(anchors_coords[-1]**2, axis = 0)

        return np.dot(np.linalg.pinv(A), B)    

def main():

    MAX_ITERS = 2500
    TERMINATION_THRESH = 0.001
    PATH_TO_DATA = '/media/esau/hdd_at_ubuntu/autocalibration_ranges'

    # retrieve from list of anchors from nodes cfg
    anchor_id_list = ['009A', '4984', '2D9C', '4806', '4848', '4814', '47FC', '43EB', '0038', '1632']
    data = []
    for anchor_id in anchor_id_list:
        anchor_data = np.loadtxt(PATH_TO_DATA + 'DW' + anchor_id + '_ranging_data.txt')
        data.append(anchor_data)
    n_anchors, n_samples = data[0].shape

    # initial guess (manually)
    anchors_coords_array = np.array([ [0.0, 0.0, 0.0],
                                [0.0, 1.2, 0.0],
                                [0.0, 2.4, 0.0],
                                [0.0, 3.6, 0.0],
                                [1.0, 1.0, 0.0],
                                [1.0, 2.0, 0.0],
                                [2.0, 0.0, 0.0],
                                [2.0, 1.0, 0.0],
                                [2.0, 2.0, 0.0],
                                [2.4, 3.6, 0.0]])

    for sample_idx in range(n_samples):

        for _ in range(MAX_ITERS):
            # save previous anchors coords for termination condition
            anchors_coords_old = np.copy(anchors_coords_array)

            # update anchors coords
            for anchor_idx in range(n_anchors):
                current_data = data[anchor_idx]
                #if anchor_id in ['009A', '4984', '2D9C', '4806']: continue
                for _anchor_idx in range(n_anchors):
                    if current_data[sample_idx, _anchor_idx] < 0: # range for anchor has not been received
                        continue
                    anchors_coords.append(anchors_coords_array[_anchor_idx])
                    anchors_distances.append(current_data[sample_idx, _anchor_idx])

                anchors_coords = np.array(anchors_coords)
                anchors_distances = np.array(anchors_distances)
                # update anchor_id coord
                anchors_coords_array[anchor_idx] = optimizedTagCoords(anchors_coords, anchors_distances)

            # termination condition -> distances between anchors have not been modified significantly
            if np.abs(np.linalg.norm(normL2(anchors_coords_array, anchors_coords_array) - normL2(anchors_coords_old, anchors_coords_old))) < TERMINATION_THRESH:
                break
        
        # rotation and translation based on anchor distribution previous knowledge
        a = anchors_coords_array[0,0] - anchors_coords_array[3,0]
        b = anchors_coords_array[0,1] - anchors_coords_array[3,1]
        theta = np.arctan(a/b)

        anchors_coords = rotate_points(anchors_coords, yaw = theta)
        anchors_coords -= anchors_coords[0]
        
        while anchors_coords_array[3,0] > 0.00001 or anchors_coords_array[3,1] < 0:
            anchors_coords = rotate_points(anchors_coords, yaw = np.radians(90))

        for idx in range(n_anchors):
            plt.scatter(anchors_coords[idx,0], anchors_coords[idx,1], color = 'black')

    anchors_coords_gt = np.array([ [0.0, 0.0, 0.0],
                                [0.0, 1.2, 0.0],
                                [0.0, 2.4, 0.0],
                                [0.0, 3.6, 0.0],
                                [1.2, 1.2, 0.0],
                                [1.2, 2.4, 0.0],
                                [2.4, 0.0, 0.0],
                                [2.4, 1.2, 0.0],
                                [2.4, 2.4, 0.0],
                                [2.4, 3.6, 0.0]])

    for idx in range(n_anchors):
        plt.scatter(anchors_coords_gt[idx,0], anchors_coords_gt[idx,1], label = anchor_id_list[idx])

    plt.legend(loc='best')
    plt.axis('equal')
    plt.show()    

if __name__ == '__main__':
    main()