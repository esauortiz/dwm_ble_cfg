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
import sys, yaml
from pathlib import Path

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

def normL2(P, Q):
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

def readYaml(file):
    with open(file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def main():

    # load nodes configuration label
    try: nodes_configuration_label = sys.argv[1]
    except: nodes_configuration_label = 'default'

    MAX_ITERS = 100
    TERMINATION_THRESH = 0.1
    PATH_TO_DATA = '/home/esau/catkin_ws/src/uwb_pkgs/dwm1001_drivers'

    # load anchors cfg
    current_path = Path(__file__).parent.resolve()
    dwm1001_drivers_path = str(current_path.parent.parent)
    nodes_cfg = readYaml(dwm1001_drivers_path + "/params/nodes_cfg/" + nodes_configuration_label + ".yaml")

    # set some node variables
    n_networks = nodes_cfg['n_networks']
    anchor_id_list = [] # single level list
    anchor_coords_list = []
    for i in range(n_networks):
        network_cfg = nodes_cfg['network' + str(i)]
        n_anchors = network_cfg['n_anchors']
        anchors_in_network_list = [network_cfg['anchor' + str(i) + '_id'] for i in range(n_anchors)]
        anchors_coords_in_network_list = [network_cfg['anchor' + str(i) + '_coordinates'] for i in range(n_anchors)]
        anchor_id_list += anchors_in_network_list
        anchor_coords_list = anchor_coords_list + anchors_coords_in_network_list

    # retrieve from list of anchors from nodes cfg
    data = []
    for anchor_id in anchor_id_list:
        anchor_data = np.loadtxt(PATH_TO_DATA + '/' + anchor_id + '_ranging_data.txt')
        data.append(anchor_data)
    n_samples, n_anchors = data[0].shape

    """
    for ranges, anchor_id in zip(data[4].T, anchor_id_list):
        print(anchor_id)
        ranges = ranges[ranges > 0]
        if len(ranges) == 0: continue
        print(np.std(ranges))
        print(np.mean(ranges))
        print(np.median(ranges))
    """
    
    for sample_idx in range(n_samples):
        autocalibrated_coords = np.array(anchor_coords_list)

        for _ in range(MAX_ITERS):
            # save previous anchors coords for termination condition
            anchors_coords_old = np.copy(autocalibrated_coords)

            # update anchors coords
            for anchor_idx in range(n_anchors):
                ranges = data[anchor_idx]
                anchor_id = anchor_id_list[anchor_idx]
                if anchor_id in [''] : continue # avoid anchor_id pose update if position is known
                anchors_coords = []
                anchors_distances = []
                # initial guess (manually)
                for _anchor_idx in range(n_anchors):
                    if ranges[sample_idx, _anchor_idx] < 0.0: # range for anchor has not been received
                        continue
                    anchors_coords.append(autocalibrated_coords[_anchor_idx])
                    anchors_distances.append(ranges[sample_idx, _anchor_idx])

                if len(anchors_coords) >= 4:
                    anchors_coords = np.array(anchors_coords)
                    anchors_distances = np.array(anchors_distances)
                    # update anchor_id coord
                    autocalibrated_coords[anchor_idx] = optimizedTagCoords(anchors_coords, anchors_distances)

            # termination condition -> distances between anchors have not been modified significantly
            if np.abs(np.linalg.norm(normL2(autocalibrated_coords, autocalibrated_coords) - normL2(anchors_coords_old, anchors_coords_old))) < TERMINATION_THRESH:
                break
        
        # rotation and translation based on anchor distribution previous knowledge
        a = autocalibrated_coords[0,0] - autocalibrated_coords[1,0]
        b = autocalibrated_coords[0,1] - autocalibrated_coords[1,1]
        theta = np.arctan(a/b)

        autocalibrated_coords = rotate_points(autocalibrated_coords, yaw = theta)
        autocalibrated_coords -= autocalibrated_coords[0]
        
        while autocalibrated_coords[1,0] > 0.00001 or autocalibrated_coords[1,1] < 0:
            autocalibrated_coords = rotate_points(autocalibrated_coords, yaw = np.radians(90))

        # plot estimated anchor coords
        for i in range(n_anchors):
            plt.scatter(autocalibrated_coords[i,0], autocalibrated_coords[i,1], color = 'black')

    # TODO: read gt from other file
    anchors_coords_gt = np.array(anchor_coords_list)

    for idx in range(n_anchors):
        plt.scatter(anchors_coords_gt[idx,0], anchors_coords_gt[idx,1], s = 0.5, label = anchor_id_list[idx])

    plt.legend(loc='best')
    plt.axis('equal')
    plt.show()    

if __name__ == '__main__':
    main()