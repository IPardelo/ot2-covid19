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
    'protocolName': 'Dispensar muestras a Deepwell',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'Dispense samples from 4 x 96 x tube rack in 96 Well Plate'
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
reagent_name = 'Sample'                     # Selected buffer for this protocol
num_samples = 96                            # total number of samples
tube_type_source = 'criotubo'               # Selected source tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
num_destinations = 96                      # total number of destinations
volume_to_be_transfered = 200              # volume in uL to be moved from 1 source to 1 destination
dispense_height = -10


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 5
x_offset = [0, 0]


# ----------------------------
# Main
# ----------------------------
(sample) = lab_stuff.buffer(reagent_name)
(_, _, _, _, pickup_height) = lab_stuff.tubes(tube_type_source)


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000µl filter tiprack') for slot in ['11']]

    # Pipette
    p1000 = ctx.load_instrument('p1000_single_gen2', 'right', tip_racks=tips)

    # Source
    rack_num = math.ceil(num_samples / NUM_OF_SOURCES_PER_RACK) if num_samples < MAX_NUM_OF_SOURCES else MIN_NUM_OF_SOURCES
    source_racks = [ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', slot,
        'source tuberack with screwcap' + str(i + 1)) for i, slot in enumerate(['5', '6', '2', '3'][:rack_num])
    ]
    sample_sources_full = common.generate_source_table(source_racks)
    sample_sources = sample_sources_full[:num_samples]

    # Destination (in this case 96 well plate)
    dest_plate = ctx.load_labware('abgene_96_wellplate_800ul', '9', 'ABGENE 96 Well Plate 800 µL')
    destinations = dest_plate.wells()[:num_destinations]

    # ------------------
    # Protocol
    # ------------------
    if not p1000.hw_pipette['has_tip']:
        common.pick_up(p1000)

    for s, d in zip(sample_sources, destinations):
        if not p1000.hw_pipette['has_tip']:
            common.pick_up(p1000)

        # Calculate pickup_height based on remaining volume and shape of container
        common.move_vol_multichannel(ctx, p1000, reagent=sample, source=s, dest=d,
                                     vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p1000.drop_tip()

    # Notify users
    # common.notify_finish_process()
