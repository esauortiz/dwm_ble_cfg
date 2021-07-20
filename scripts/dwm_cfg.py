#!/usr/bin python3.6

import yaml
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
    
    # read BT devs
    devices = ble_handler.getDevices()
    devices_found = {}
    for dev in devices:
        devices_found[dev.name] = dev.address

    # load anchors cfg
    anchors_cfg = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/anchors.yaml")
    # load anchors operation mode
    anchor_operation_mode = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/anchor_operation_mode.yaml")
    # load tag operation mode
    tag_operation_mode = readYaml("/home/nuc/Documents/dwm_ble_cfg/params/tag_operation_mode.yaml")

    # set some anchor variables
    n_anchors = anchors_cfg['n_anchors']
    initiator_id = anchors_cfg['initiator_id']

    # do stuff with found devices
    for i in range(n_anchors):
        anchor_name = anchors_cfg[f'anchor{i}_id']
    
        if anchor_name in devices_found:
            print(f'Anchor {anchor_name} found')
            anchor_pose = anchors_cfg[f'anchor{i}_coordinates'].split(', ')
            print(f'Setting anchor {anchor_name} pose to [X: {anchor_pose[0]} Y: {anchor_pose[1]} Z: {anchor_pose[2]}]')
            anchor_pose_msg = PersistedPositionMsg(anchor_pose)
            ble_handler.send(devices_found[anchor_name], anchor_pose_msg)
            operation_mode_msg = OperationModeMsg()
            data = ble_handler.readFromDevice(devices_found[anchor_name], operation_mode_msg.UUID)
            print(data)
        else:
            print(f'{anchor_name} not found')
