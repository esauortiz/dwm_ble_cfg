""" 
@file: autocalibration_solver.py
@description:   python module autocalibrate anchor position based on inter-anchor ranging data
                This process takes an initial anchors coords guess as starting point of the iterative
                optimization.
@author: Esau Ortiz
@date: october 2021
@usage: python autocalibration_solver.py 
"""

from locale import nl_langinfo
from matplotlib import colors
import matplotlib.pyplot as plt
from numpy.lib.ufunclike import fix
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import sys, yaml
from pathlib import Path
from scipy.optimize import fmin

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

def costOptimization(anchors_coords, ranges, fixed_anchors):
    def _my_opt_func(Theta, *args):
        """optimize target function
        Theta: (3, N)
            current array of anchors coordinates (x,y,z)
        args:
            ranges: array (N, N) inter anchor ranges (median of n_samples)
            n_anchors: total number of anchors
        """
        ranges_ij, n_anchors, fixed_anchors, Theta_init = args
        Theta = Theta.reshape(n_anchors, 3)
        Theta[fixed_anchors] = Theta_init[fixed_anchors]
        invalid_ranges_mask = ranges < 0

        distances_ij = np.einsum("ijk->ij", (Theta[:, None, :] - Theta) ** 2)
        mask = distances_ij == 0 # to remove j = i cost
        cost_ij = (distances_ij - ranges_ij ** 2) ** 2
        cost_ij[mask] = 0 # remove j = i costs
        cost_ij[invalid_ranges_mask] = 0 # remove costs computed with invalid ranges
        return np.sum(np.einsum("ij->i", cost_ij))

    anchors_coords = anchors_coords.T.reshape(-1,3)
    print(anchors_coords)
    Theta_init = np.copy(anchors_coords)
    n_anchors = anchors_coords.shape[0]
    args = ranges, n_anchors, fixed_anchors, Theta_init
    
    print(f'Before optimization: Cost = {_my_opt_func(anchors_coords, *args)}')
    Theta_opt = fmin(_my_opt_func, anchors_coords, args = args, disp=False)#, xtol = 0.000001, ftol = 0.000001)    
    print(f'After optimization: Cost = {_my_opt_func(Theta_opt, *args)}')
    Theta_opt = Theta_opt.reshape(anchors_coords.shape)
    Theta_opt[fixed_anchors] = Theta_init[fixed_anchors]

    return Theta_opt

def main():

    # load nodes configuration label
    try: nodes_configuration_label = sys.argv[1]
    except: nodes_configuration_label = 'default'

    MAX_ITERS = 2500
    TERMINATION_THRESH = 0.001
    PATH_TO_DATA = '/home/esau/catkin_ws/src/uwb_pkgs/dwm1001_drivers/ranging_uart_3D_distribution'

    # load anchors cfg
    current_path = Path(__file__).parent.resolve()
    dwm1001_drivers_path = str(current_path.parent.parent)
    nodes_cfg = readYaml(dwm1001_drivers_path + "/params/nodes_cfg/" + nodes_configuration_label + ".yaml")

    # set some node variables
    n_networks = nodes_cfg['n_networks']
    anchor_id_list = [] # single level list
    anchor_coords_list = [] # initial guess
    anchor_coords_gt = []
    for i in range(n_networks):
        network_cfg = nodes_cfg['network' + str(i)]
        n_anchors = network_cfg['n_anchors']
        anchors_in_network_list = [network_cfg['anchor' + str(i) + '_id'] for i in range(n_anchors)]
        anchors_coords_in_network_list = [network_cfg['anchor' + str(i) + '_coordinates'] for i in range(n_anchors)]
        anchors_coords_gt_in_network_list = [network_cfg['gt']['anchor' + str(i) + '_coordinates'] for i in range(n_anchors)]
        anchor_id_list += anchors_in_network_list
        anchor_coords_list = anchor_coords_list + anchors_coords_in_network_list
        anchor_coords_gt = anchor_coords_gt + anchors_coords_gt_in_network_list

    # read anchor_data (i.e. (n_samples, n_anchors) ranges array)
    data = []
    for anchor_id in anchor_id_list:
        try:
            anchor_data = np.loadtxt(PATH_TO_DATA + '/' + anchor_id + '_ranging_data.txt')
            anchor_data = anchor_data.T
            #anchor_data = np.array([anchor_data[idx] for idx in idxs])
            anchor_data = anchor_data.T
            anchor_data = anchor_data[1:] # discard first sample, usually filled with bad lectures (i.e. -1 values)
            median_list = []
            for ranges in anchor_data.T:
                median_list.append(np.median(ranges))
            anchor_data = np.array(median_list).reshape(1,-1)
        except:
            anchor_data = None
        data.append(anchor_data)
    n_samples, n_anchors = data[0].shape
    
    # plot instance
    fig = plt.figure()
    ax = ax = Axes3D(fig)
    estimated_coords = np.empty((3,n_samples,n_anchors))

    for sample_idx in range(n_samples):
        autocalibrated_coords = np.copy(anchor_coords_list)
        sampled_ranges = []

        for anchor_idx in range(n_anchors):
            ranges = data[anchor_idx]
            sampled_ranges.append(ranges[sample_idx])
        sampled_ranges = np.array(sampled_ranges)

        for _ in range(MAX_ITERS):
            # save previous anchors coords for termination condition
            anchors_coords_old = np.copy(autocalibrated_coords)

            # update anchors coords
            for anchor_idx in range(n_anchors):
                ranges = data[anchor_idx]
                anchor_id = anchor_id_list[anchor_idx]
                if anchor_id in ['DW009A', 'DW4984', 'DW4848', 'DW47FC'] : continue # avoid anchor_id pcmap = plt.get_cmap('viridis')ose update if position is known
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
        
        # save estimated anchor coords
        estimated_coords[:,sample_idx,:] = autocalibrated_coords.T

    # plot gt and estimation
    cmap = plt.get_cmap('gist_rainbow')
    my_colors = cmap(np.linspace(0,1,n_anchors))

    anchors_coords_gt = np.array(anchor_coords_gt)
    ax.scatter([],[],[], label = 'estimation (fmin)', marker = 'x', color = 'black')
    ax.scatter([],[],[], label = 'ground truth', color = 'black')
    fixed_anchors = np.array([1,0,1,1,0,1,0,0,0,0], dtype=bool)
    data = np.array(data).reshape(n_anchors, n_anchors)
    optimizedCoords = costOptimization(estimated_coords, data, fixed_anchors)
    for idx in range(n_anchors):
        estimated_anchor_coords = estimated_coords[:,:,idx].T
        centroid = np.mean(estimated_anchor_coords, axis = 0)
        #ax.scatter(centroid[0], centroid[1], centroid[2], color = my_colors[idx], marker = 'x')
        ax.scatter(optimizedCoords[idx,0], optimizedCoords[idx,1], optimizedCoords[idx,2], color = my_colors[idx], marker = 'x')
        ax.scatter(anchors_coords_gt[idx,0], anchors_coords_gt[idx,1], anchors_coords_gt[idx,2], color = my_colors[idx], label = anchor_id_list[idx])
        print(anchor_id_list[idx], ' pose estimation error: ', float(normL2(np.array([optimizedCoords[idx]]), np.array([anchors_coords_gt[idx]]))))

    plt.legend(loc='best')
    plt.axis('auto')
    plt.show()   


if __name__ == '__main__':
    main()