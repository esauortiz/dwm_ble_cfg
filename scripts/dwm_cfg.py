#!/usr/bin python3.6

import yaml
from pprint import pprint
from dwm1001_BleApi import BleConnectionHandler
from dwm1001_BleApi import PersistedPositionMsg
from dwm1001_BleApi import OperationModeMsg

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
    anchors_cfg = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/anchors.yaml")
    # load anchors operation mode
    anchor_operation_mode = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/anchor_operation_mode.yaml")
    # load tag operation mode
    tag_operation_mode = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/tag_operation_mode.yaml")

    # set some node variables
    tag_id = anchors_cfg['tag_id']
    n_anchors = anchors_cfg['n_anchors']
    anchors_expected_id = []
    for i in range(n_anchors):
        # append expected anchor_id (e.g. DW2020)
        anchors_expected_id.append(anchors_cfg[f'anchor{i}_id'])
    initiator_id = anchors_cfg['initiator_id']

    # msgs to send through BLE
    anchor_pose_msg = PersistedPositionMsg()
    operation_mode_msg = OperationModeMsg()

    # set anchor pose and operation mode
    for i in range(n_anchors):
        anchor_id = anchors_cfg[f'anchor{i}_id']
        if anchor_id in devices_found_id:
            if devices_found_id[anchor_id] not in anchors_expected_id:
                continue
            print(f'Anchor {anchor_id} found')
            anchor_pose = anchors_cfg[f'anchor{i}_coordinates'].split(', ')
            print(f'Setting anchor {anchor_id} pose to [X: {anchor_pose[0]} Y: {anchor_pose[1]} Z: {anchor_pose[2]}]')
            anchor_pose_msg.setData(anchor_pose)
            operation_mode_msg.setData(anchor_operation_mode)
            ble_handler.send(devices_found_id[anchor_id], anchor_pose_msg)
            ble_handler.send(devices_found_id[anchor_id], operation_mode_msg)
        else:
            print(f'{anchor_id} not found')

    print("Found anchors's mode are set as follows:")
    pprint(anchor_operation_mode)

    # set tag operation mode
    if tag_id in devices_found_id:
        operation_mode_msg.setData(tag_operation_mode)
        ble_handler.send(devices_found_id[anchor_id], operation_mode_msg)
        print("Found tag {tag_id} mode are set as follows:")
        pprint(tag_operation_mode)
    else:
        print('Tag {tag_id} not found')