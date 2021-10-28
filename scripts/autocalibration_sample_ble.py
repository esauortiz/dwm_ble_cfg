#!/usr/bin python3.6

""" 
@file: autocalibration_sample_ble.py
@description: python module to configure anchor as tag, retrieve ranges and configure module as anchor back
              using BLE API from https://www.decawave.com/dwm1001/api/
@author: Esau Ortiz
@date: october 2021
@usage: python autocalibration_sample_ble.py <module> <nodes_configuration_label> <n_samples>

        # where <module> is the module id with DW1234 format
                <nodes_configuration_label> is a yaml file which includes nets, 
                tag ids, anchor ids and anchor coords
                <n_samples> samples to save when retrieving ranges
"""

import yaml
import sys
import bleak
from pathlib import Path
from dwm1001_apiBle import BleConnectionHandler
from dwm1001_apiBle import OperationModeMsg, NetworkIdMsg
from dwm1001_apiBle import LocationDataMsg, LocationDataModeMsg

def readYaml(file):
    with open(file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

def main():
    # target module from which retrieve ranges
    target_dwm_module = sys.argv[1]
    # load nodes configuration label
    try: nodes_configuration_label = sys.argv[2]
    except: nodes_configuration_label = 'default'
    # load nodes configuration label
    try: n_samples = int(sys.argv[2])
    except: n_samples = 10

    # load anchors cfg
    current_path = Path(__file__).parent.resolve()
    dwm1001_drivers_path = str(current_path.parent.parent)
    nodes_cfg = readYaml(dwm1001_drivers_path + "/params/nodes_cfg/" + nodes_configuration_label + ".yaml")
    # load anchors operation mode
    anchor_operation_mode = readYaml(dwm1001_drivers_path + "/params/anchor_operation_mode.yaml")
    # load tag operation mode
    tag_operation_mode = readYaml(dwm1001_drivers_path + "/params/tag_operation_mode.yaml")

    # set some node variables
    n_networks = nodes_cfg['n_networks']
    network_id_list = []
    anchor_id_list = [] # single level list
    anchor_id_list_by_network = [] # grouped by networks
    for i in range(n_networks):
        network_cfg = nodes_cfg['network' + str(i)]
        network_id_list.append(network_cfg['network_id'])
        n_anchors = network_cfg['n_anchors']
        anchors_in_network_list = [network_cfg['anchor' + str(i) + '_id'] for i in range(n_anchors)]
        anchor_id_list_by_network.append(anchors_in_network_list)
        anchor_id_list += anchors_in_network_list


    # BLE connection handler
    ble_handler = BleConnectionHandler()
    
    # read BT devices
    devices = ble_handler.getDevices()
    devices_found_id = {}
    for dev in devices:
        devices_found_id[dev.name] = dev.address # e.g. {'DW2020' : '00:11:22:33:FF:EE'}

    # msgs to send through BLE
    operation_mode_msg = OperationModeMsg()
    network_id_msg = NetworkIdMsg()
    location_data_mode_msg = LocationDataModeMsg(1)
    location_data_msg = LocationDataMsg()

    try:
        anchor_address = devices_found_id[target_dwm_module]
        print(f'{target_dwm_module} has been found')
    except KeyError:
        print(f'Module {target_dwm_module} not found')
        return False

    # configure as tag
    print(f'Anchor -> tag. Setting operation mode ...')
    operation_mode_msg.setData(tag_operation_mode)
    ble_handler.send(anchor_address, operation_mode_msg)
    
    print(f'Setting location data mode mode ...')
    ble_handler.send(anchor_address, location_data_mode_msg)
    
    for network_id in network_id_list:
        print(f'Setting tag {target_dwm_module} network id to {network_id}')
        network_id_msg.setData(network_id)
        ble_handler.send(anchor_address, network_id_msg)

        # read ranges
        for i in range(n_samples):
            print(f'Retrieving ranges')
            try:
                ranges = ble_handler.read(anchor_address, location_data_msg, verbose=False, decode_msg=True)
                print(ranges)
            except bleak.exc.BleakDBusError:
                print(f'Connection failed. Retrying ... ')
    
    # back to anchor
    anchor_operation_mode['initiator_enable'] = 1
    network_id = None
    for i in range(n_networks):
        if target_dwm_module in anchor_id_list_by_network[i]:
            network_id = network_id_list[i]

    print(f'Setting anchor {target_dwm_module} network id to {network_id}')
    network_id_msg.setData(network_id)
    ble_handler.send(anchor_address, network_id_msg)
    print(f'Setting anchor {target_dwm_module} operation mode')
    operation_mode_msg.setData(anchor_operation_mode)
    ble_handler.send(anchor_address, operation_mode_msg)

    print('Autocalibration sample has been taken successfully')

if __name__ == "__main__":
    main()