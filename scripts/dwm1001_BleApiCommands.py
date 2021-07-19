#!/usr/bin python3.6

""" For more info on the documentation go to https://www.decawave.com/sites/default/files/dwm1001-api-guide.pdf
"""

class DWM1001_BLE_API_COMMANDS:
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
