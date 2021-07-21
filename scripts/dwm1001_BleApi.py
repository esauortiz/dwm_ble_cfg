#!/usr/bin python3.6

""" For more info on the documentation go to https://www.decawave.com/sites/default/files/dwm1001-api-guide.pdf
"""
import asyncio
from bitstring import Bits
from textwrap import wrap
from bleak import discover, BleakClient

class DWM1001_BLE_API_COMMANDS:
        # Network Node Characteristics
        LABEL                   = '0x2A00' # RW
        OPERATION_MODE          = '3f0afd88-7770-46b0-b5e7-9fc099598964' # RW
        NETWORK_ID              = '80f9d8bc-3bff-45bb-a181-2d6a37991208' # RW
        LOCATION_DATA_MODE      = 'a02b947e-df97-4516-996a-1882521e0ead' # RW
        LOCATION_DATA           = '003bbdf2-c634-4b3d-ab56-7ec889b89a37' # RO
        PROXY_POSITIONS         = 'f4a67d7d-379d-4183-9c03-4b6ea5103291' # RO
        DEVICE_INFO             = '1e63b1eb-d4ed-444e-af54-c1e965192501' # RO
        STATISTICS              = '0eb2bc59-baf1-4c1c-8535-8a0204c69de5' # 
        FW_UPDATE_PUSH          = '5955aa10-e085-4030-8aa6-bdfac89ac32b' # WO
        FW_UPDATE_POLL          = '9eed0e27-09c0-4d1c-bd92-7c441daba850' # RO
        DISCONNECT              = 'ed83b848-da03-4a0a-a2dc-8b401080e473' # WO
        # Anchor-specific Characteristics
        OPERATION_MODE          = '3f0afd88-7770-46b0-b5e7-9fc099598964' # RW
        DEVICE_INFO             = '1e63b1eb-d4ed-444e-af54-c1e965192501' # RO
        PERSISTED_POSITION      = 'f0f26c9b-2c8c-49ac-ab60-fe03def1b40c' # WO
        MAC_STATS               = '28d01d60-89de-4bfa-b6e9-651ba596232c' # RO
        CLUSTER_INFO            = '17b1613e-98f2-4436-bcde-23af17a10c72' # RO
        ANCHOR_LIST             = '5b10c428-af2f-486f-aee1-9dbd79b6bccb' # RO
        # Tag-specific Characteristics
        OPERATION_MODE          = '3f0afd88-7770-46b0-b5e7-9fc099598964' # RO
        UPDATE_RATE             = '7bd47f30-5602-4389-b069-8305731308b6' # RO

class BleConnectionHandler(object):
        def __init__(self):
                self.loop = asyncio.get_event_loop()

        def getDevices(self):
                async def asyncGetDevices():
                        print('Searching BT devices ...\n')
                        devices = await discover()
                        return devices

                devices = self.loop.run_until_complete(asyncGetDevices())
                return devices

        def readFromDevice(self, address, UUID):
                async def asyncReadFromDevice(address, UUID):
                        async with BleakClient(address) as client:
                                data = await client.read_gatt_char(UUID)
                        return data

                data = self.loop.run_until_complete(asyncReadFromDevice(address, UUID))
                return data

        def writeToDevice(self, address, UUID, data):
                async def asyncWriteToDevice(address, UUID, data):
                        async with BleakClient(address) as client:
                                await client.write_gatt_char(UUID, data)
                self.loop.run_until_complete(asyncWriteToDevice(address, UUID, data))

        def send(self, address, msg_object, debug = False):
                """ send message over BLE
                Parameters
                ----------
                msg_object : BleMsg
                address: string
                        BLE address
                Returns
                -------
                """
                if msg_object.is_data_ble_encoded == False:
                        msg_object.encodeBle()
                if debug == False:
                        self.writeToDevice(address, msg_object.UUID, msg_object.data)
                else:
                        print(msg_object.data)

        def read(self, address, msg_object):
                """ read message over BLE
                Parameters
                ----------
                msg_object : BleMsg
                address: string
                        BLE address
                Returns
                -------
                """
                # read returns raw bytearray, TODO: decode read data
                return self.readFromDevice(address, msg_object.UUID)

class BleMsg(object):
        def __init__(self, api_command, data = None):
                self.UUID  = api_command
                self.data = data
                self.is_data_ble_encoded = False

        def setData(self, data):
                self.data = data
                self.is_data_ble_encoded = False

        def encodeBle(self):
                """ Encode BLE msg, bytes slots are encoded 
                as little endian as BLE spec suggests.
                Parameters
                ----------
                data : (N,) array
                Returns
                -------
                encoded_msg : bytearray
                """                
                return

        def codeLittleEndian(self, bits):
                """ Encode/decode bits as little endian bytes
                Parameters
                ----------
                bits : (N,) Bits in hexadecimal
                Returns
                -------
                encoded_msg : (N/8) array of bytes
                """
                bits = str(bits)
                # assert bits in hexadecimal
                if bits[0:2] != '0x':
                        raise ValueError
                # slice msg in pieces of 1 byte
                wrapped_bits = wrap(str(bits)[2:], 2)
                wrapped_bits.reverse()
                return wrapped_bits

        def listToByteArray(self, list):
                """ set
                Parameters
                ----------
                bits : (2, N) list of bytes
                Returns
                -------
                encoded_msg : bitearray
                """
                # flatten list
                # list = [item for sublist in list for item in sublist]
                return bytearray(bytes.fromhex(''.join(list)))

class PersistedPositionMsg(BleMsg):
        def __init__(self, data = None):
                """
                Parameters
                ----------
                data : (3,) array
                        x, y, z as signed int
                """
                BleMsg.__init__(self, DWM1001_BLE_API_COMMANDS.PERSISTED_POSITION, data)

        def encodeBle(self):
                """ Encode BLE msg, bytes slots are encoded 
                as little endian as BLE spec suggests.
                Parameters
                ----------
                Returns
                -------
                """
                result = []
                for coord in self.data:
                        # 4 byte coord in mm
                        coord = self.codeLittleEndian(Bits(int = int(float(coord) * 1000), length = 32))
                        for element in coord:
                                result.append(element)
                # quality factor (1 byte, value 1 - 100 DEC)
                result.append('64')
                self.data = self.listToByteArray(result)
                self.is_data_ble_encoded = True

class OperationModeMsg(BleMsg):
        def __init__(self, data = None):
                """
                Parameters
                ----------
                data : dictionary
                """
                BleMsg.__init__(self, DWM1001_BLE_API_COMMANDS.OPERATION_MODE, data)

        def encodeBle(self):
                """ Encode BLE msg, bytes slots are encoded 
                as little endian as BLE spec suggests.
                Parameters
                ----------
                Returns
                -------
                """
                result = []
                first_byte = ''
                first_byte += format(self.data['node_type'],'01b')
                first_byte += format(self.data['UWB'],'02b')
                first_byte += format(self.data['firmware'],'01b')
                first_byte += format(self.data['accelerometer_enable'],'01b')
                first_byte += format(self.data['LED_indication_enabled'],'01b')
                first_byte += format(self.data['firmware_update_enable'],'01b')
                first_byte += format(1,'01b')
                # append just hex(byte) without '0x'
                result.append(format(int(first_byte, 2), '02x'))

                second_byte = ''
                second_byte += format(self.data['initiator_enable'],'01b')
                second_byte += format(self.data['low_power_mode_enable'],'01b')
                second_byte += format(self.data['location_engine_enable'],'01b')
                second_byte += format(0,'05b')
                result.append(format(int(second_byte, 2), '02x'))

                # 2 bytes non little endian, see API documentation
                self.data = self.listToByteArray(result)
                self.is_data_ble_encoded = True

        def decodeBle(self):
                """ TODO decode msg
                Parameters
                ----------
                Returns
                -------
                """
