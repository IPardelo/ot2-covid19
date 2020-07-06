# -*- coding: utf-8 -*-

import math
import importlib
from opentrons import protocol_api

LIBRARY_PATH = '/root/ot2-covid19/library/'

# Load library
spec = importlib.util.spec_from_file_location("library.protocols.common_functions",
                                              "{}protocols/common_functions.py".format(LIBRARY_PATH))
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

# Load Brands & other stuff
spec2 = importlib.util.spec_from_file_location("library.protocols.lab_stuff",
                                              "{}protocols/lab_stuff.py".format(LIBRARY_PATH))
lab_stuff = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(lab_stuff)


metadata = {
    'protocolName': 'Pooling a Deepwell',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.2',
    'description': 'PCR Index'
}


# ------------------------
# Tuberack parameters (CONSTANTS)
# ------------------------
MAX_NUM_OF_SOURCES = 96
MIN_NUM_OF_SOURCES = 4
NUM_OF_SOURCES_PER_RACK = 24


# ------------------------
# Sample specific parameters (INPUTS)
# ------------------------
reagent_name = 'Sample'                         # Selected buffer for this protocol
tube_type_source = 'eppendorf'                  # Selected destination tube for this protocol



# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
volume_to_be_transfered = 10                   # volume in uL to be moved
num_destinations = 96


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 5
x_offset = [0, 0]


# ----------------------------
# Main
# ----------------------------

_, _, _, _, pickup_height = lab_stuff.tubes(tube_type_source)
sample = lab_stuff.buffer(reagent_name)

num_cols = math.ceil(num_destinations / 8)
num_rows = math.ceil(num_destinations / 12)
final_vol = (volume_to_be_transfered * 10) / 12

def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------

    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, 'Tiprack') for slot in ['11']]

    # Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tips)

    # Source
    source_plate = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '7', 'Tuberack')
    source_1 = source_plate.wells()[0]

    # Destination 1 (and source for the 2nd destination)
    dest_plate1 = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '4', 'PCR plate')
    dest_1 = dest_plate1.columns()[0][:num_rows]
    source_2 = dest_plate1.wells()[0]

    # Destination 2 (destination of 'dest_plate1')
    dest_plate2 = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '1', 'PCR plate')
    dest_2 = dest_plate2.rows()[0][:num_cols]

    # ------------------
    # Protocol
    # ------------------

    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    for i in range(10):
        for d in dest_1:
            common.move_vol_multichannel(ctx, p20, reagent=sample, source=source_1, dest=d,
                                         vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                         x_offset=x_offset, pickup_height=1, disp_height=-10,
                                         blow_out=True, touch_tip=True)

    p20.return_tip()

    if not m20.hw_pipette['has_tip']:
        common.pick_up(m20)

    for d in dest_2:
        common.move_vol_multichannel(ctx, m20, reagent=sample, source=source_2, dest=d,
                                     vol=final_vol, air_gap_vol=air_gap_vol_sample,
                                     x_offset=x_offset, pickup_height=1, disp_height=-10,
                                     blow_out=True, touch_tip=True)

    m20.drop_tip()

    # Notify users
    # common.notify_finish_process()