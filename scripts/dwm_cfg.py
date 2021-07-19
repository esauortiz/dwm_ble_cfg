#!/usr/bin python3.6

import asyncio
import yaml
from bleak import discover, BleakClient
from dwm1001_BleApiCommands import DWM1001_BLE_API_COMMANDS

async def getDevices():
    print('Searching BT devices ...')
    devices = await discover()
    return devices

async def readFromDevice(address, UUID):
    async with BleakClient(address) as client:
        model_number = await client.read_gatt_char(UUID)
        print("Model Number: {0}".format(model_number))

async def writeToDevice(address, UUID, data):
    async with BleakClient(address) as client:
        success = await client.write_gatt_char(UUID, data)
         
def setNodePose(loop, address, pose):
    pose = b'0000000000000'
    loop.run_until_complete(writeToDevice(address, DWM1001_BLE_API_COMMANDS.PERSISTED_POSITION, pose))
         
if __name__ == "__main__":

    # read BT devs
    loop = asyncio.get_event_loop()
    devs = loop.run_until_complete(getDevices())
    devs_found = {}
    for dev in devs:
        devs_found[dev.name] = dev.address

    # load anchors cfg
    with open("/home/nuc/Documents/dwm_ble_cfg/params/anchors.yaml", 'r') as stream:
        try:
            anchors_cfg = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    # set some anchor variables
    n_anchors = anchors_cfg['n_anchors']

    # devs found info
    for i in range(n_anchors):
        anchor_name = anchors_cfg[f'anchor{i}_id']
        if anchor_name in devs_found:
            print(f'{anchor_name} found')
            print(f'setting configuration ...')
            anchor_pose = anchors_cfg[f'anchor{i}_coordinates'].split(', ')
            #setNodePose(loop, devs_found[anchor_name], 0)
            #pose = b'\x00\xe8\x03\x00\x00\xd0\x07\x00\x00\xb8\x0b\x00\x00d'
            loop.run_until_complete(readFromDevice(devs_found[anchor_name], "003bbdf2-c634-4b3d-ab56-7ec889b89a37"))
            #setNodePose(loop, devs_found[anchor_name], pose)
        else:
            print(f'{anchor_name} not found')
            #bytearray(b'\x00\x808\x01\x00\x808\x01\x00\x808\x01\x00d')
            #[f'{i:02x}' for i in data]
            #['00', '80', '38', '01', '00', '80', '38', '01', '00', '80', '38', '01', '00', '64']
