import asyncio
from bleak import BleakClient

address = "CE:29:20:9C:5B:43"
MODEL_NBR_UUID = "1e63b1eb-d4ed-444e-af54-c1e965192501"

async def run(address):
    async with BleakClient(address) as client:
        model_number = await client.read_gatt_char(MODEL_NBR_UUID)
        print("Model Number: {0}".format("".join(map(chr, model_number))))

loop = asyncio.get_event_loop()
loop.run_until_complete(run(address))