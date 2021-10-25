#!/usr/bin python3.6

""" 
@file: dmw_cfg.py
@description: python module to configure tag and anchors
              using BLE API from https://www.decawave.com/dwm1001/api/
@author: Esau Ortiz
@date: july 2021
@usage: python dwm_cfg.py 'cfg_description' # where 'cfg_description' is an optional
        label for nodes_cfg_'cfg_description'.yaml file. If label is not provided is
        set to 'default'.
"""

import yaml
import sys
from os.path import expanduser
from pprint import pprint
from dwm1001_apiBle import BleConnectionHandler
from dwm1001_apiBle import PersistedPositionMsg, OperationModeMsg, NetworkIdMsg
from dwm1001_apiBle import LocationDataMsg, LocationDataModeMsg

def readYaml(file):
    with open(file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

if __name__ == "__main__":

    # BLE connection handler
    ble_handler = BleConnectionHandler()
    
    # read BT devices
    devices = ble_handler.getDevices()
    devices_found_id = {}
    for dev in devices:
        devices_found_id[dev.name] = dev.address # e.g. {'DW2020' : '00:11:22:33:FF:EE'}

    # load anchors cfg
    try:
        nodes_cfg_description = sys.argv[1]
    except:
        nodes_cfg_description = 'default'
    # load anchors cfg
    nodes_cfg = readYaml(expanduser("~") + "/catkin_ws/src/dwm1001_drivers/dwm_ble_cfg/params/nodes_cfg_" + nodes_cfg_description + ".yaml")
    # load anchors operation mode
    anchor_operation_mode = readYaml(expanduser("~") + "/catkin_ws/src/dwm1001_drivers/dwm_ble_cfg/params/anchor_operation_mode.yaml")
    # load tag operation mode
    tag_operation_mode = readYaml(expanduser("~") + "/catkin_ws/src/dwm1001_drivers/dwm_ble_cfg/params/tag_operation_mode.yaml")

    # set some node variables
    network_id = nodes_cfg['network_id']
    tag_id = nodes_cfg['tag0_id']
    n_anchors = nodes_cfg['n_anchors']
    anchors_expected_id = []
    for i in range(n_anchors):
        # append expected anchor_id (e.g. DW2020)
        anchors_expected_id.append(nodes_cfg[f'anchor{i}_id'])
    initiator_id = nodes_cfg['initiator_id']

    # msgs to send through BLE
    anchor_pose_msg = PersistedPositionMsg()
    operation_mode_msg = OperationModeMsg()
    network_id_msg = NetworkIdMsg(network_id)

    for i in range(n_anchors):
        anchor_id = nodes_cfg[f'anchor{i}_id']
        try:
            anchor_address = devices_found_id[anchor_id]
        except KeyError:
            print(f'Anchor {anchor_id} not found')
            continue
        if anchor_id in devices_found_id:
            if anchor_id == initiator_id:
                anchor_operation_mode['initiator_enable'] = 1
                str_is_initiator = ' as initiator'
            else:
                anchor_operation_mode['initiator_enable'] = 0 
                str_is_initiator = ''

            print(f'Anchor {anchor_id} found. Do you want to configure it? (y/n)' )
            if input() == 'n':
                print('\n')
                continue
            anchor_pose = nodes_cfg[f'anchor{i}_coordinates'] #.split(', ') # not as list

            print(f'Setting anchor {anchor_id} network id to {network_id}')
            ble_handler.send(anchor_address, network_id_msg)

            print(f'Setting anchor {anchor_id} operation mode' + str_is_initiator + ' ...')
            operation_mode_msg.setData(anchor_operation_mode)
            ble_handler.send(anchor_address, operation_mode_msg)

            print(f'Setting anchor {anchor_id} pose to [X: {anchor_pose[0]} Y: {anchor_pose[1]} Z: {anchor_pose[2]}] ...\n')
            anchor_pose_msg.setData(anchor_pose)
            ble_handler.send(anchor_address, anchor_pose_msg)
        else:
            print(f'{anchor_id} not found\n')

    print("Found anchors's mode are set as follows:")
    pprint(anchor_operation_mode)
    print("\n")

    # set tag operation mode
    if tag_id in devices_found_id:
        tag_address = devices_found_id[tag_id]
        print(f'Tag {tag_id} found. Do you want to configure it? (y/n)' )
        if input() == 'y':
            print(f'Setting tag {tag_id} operation mode ...')
            operation_mode_msg.setData(tag_operation_mode)
            ble_handler.send(tag_address, operation_mode_msg)

            print(f'Found tag {tag_id} mode are set as follows:')
            pprint(tag_operation_mode)
        print("\n")
    else:
        print(f'Tag {tag_id} not found\n')

    print('Configuration finished')
