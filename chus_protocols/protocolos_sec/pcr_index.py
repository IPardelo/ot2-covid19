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
tube_type_source = 'eppendorf'                    # Selected destination tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
volume_to_be_transfered = 100                   # volume in uL to be moved from 1 source to 1 destination
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

def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------

    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, 'Tiprack') for slot in ['10', '11']]

    # Pipette
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips)

    # Source (in this case X opentrons 24 tube rack 2ml)
    source_plate = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '4', 'Tuberack 1')
    source1 = source_plate.wells()[:8]
    source2 = source_plate.wells()[8:20]

    # Destination (in this case Xs well plate)
    dest_plate = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '1', 'PCR')
    num_dest_1 = dest_plate.rows()[:num_rows]
    num_dest_2 = dest_plate.columns()[:num_cols]

    mov_1 = zip(source1, num_dest_1)
    mov_2 = zip(source2, num_dest_2)

    # ------------------
    # Protocol
    # ------------------

    if not p300.hw_pipette['has_tip']:
        common.pick_up(p300)

    for source, destinations in mov_1:
        if not p300.hw_pipette['has_tip']:
            common.pick_up(p300)
        for destination in destinations:
            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p300, reagent=sample, source=source, dest=destination,
                                            vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                            pickup_height=pickup_height, disp_height=0,
                                            x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p300.drop_tip()

    if not p300.hw_pipette['has_tip']:
        common.pick_up(p300)

    for source, destinations in mov_2:
        if not p300.hw_pipette['has_tip']:
            common.pick_up(p300)
        for destination in destinations:
            if not p300.hw_pipette['has_tip']:
                common.pick_up(p300)
            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p300, reagent=sample, source=source, dest=destination,
                                            vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                            pickup_height=pickup_height, disp_height=0,
                                            x_offset=x_offset, blow_out=True, touch_tip=True)
            # Drop pipette tip
            p300.drop_tip()

    # Notify users
    # common.notify_finish_process()