# -*- coding: utf-8 -*-

import math
import importlib
from opentrons import protocol_api

# Load library
LIBRARY_PATH = '/root/ot2-covid19/library/'
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
    'protocolName': 'C1',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'Custom mix protocol'
}

# ------------------------
# Tuberack parameters (CONSTANTS)
# ------------------------
MAX_NUM_OF_SOURCES = 96
MIN_NUM_OF_SOURCES = 4
NUM_OF_SOURCES_PER_RACK = 24


# ------------------------
# Buffer specific parameters (INPUTS)
# ------------------------
buffer_name = 'Lisis'                       # Selected buffer for this protocol
sources = 5                                 # Number of sources
tube_type_source = 'criotubo'               # Selected source tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
volume_to_be_moved = 10                     # volume in uL to be moved
tube_type_dest = 'eppendorf'                # Selected destination tube for this protocol


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 1
x_offset = [0, 0]
rounds = 20


# ----------------------------
# Main
# ----------------------------
buffer = lab_stuff.buffer(buffer_name)
_, _, _, _, pickup_height = lab_stuff.tubes(tube_type_source)
_, _, _, dispense_height, _ = lab_stuff.tubes(tube_type_dest)


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200µl filter tiprack') for slot in ['11']]

    # Pipette
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips)

    # Source
    source = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '4', 'Tuberack')
    source_racks = source.wells()[:sources]

    # Destination
    dest = ctx.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap', '1', 'Aluminum tuberack')
    dest_rack = dest.wells()[0]

    # ------------------
    # Protocol
    # ------------------
    for s in source_racks:
        if not p300.hw_pipette['has_tip']:
            common.pick_up(p300)

        common.move_vol_multichannel(ctx, p300, reagent=buffer, source=s, dest=dest_rack,
                                     vol=volume_to_be_moved, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)

        # Drop pipette tip
        p300.drop_tip()

    if not p300.hw_pipette['has_tip']:
        common.pick_up(p300)

    common.custom_mix(p300, reagent=buffer, location=dest_rack, vol=volume_to_be_moved,
                      rounds=rounds, blow_out=True, mix_height=dispense_height, x_offset=x_offset, source_height=dispense_height)

    p300.drop_tip()
