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
    'protocolName': 'Seroteca',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'Dispense samples from 4 x 96 aliminum block to 4 x 96 x tube rack'
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
buffer_name = 'Lisis'                           # Selected buffer for this protocol
tube_type_source = 'f_redondo2'                      # Selected destination tube for this protocol


# ------------------------
# Volúmenes
# ------------------------
volume_sample_fredondo = 0
volume_sample_alicuota = 0
volume_sample = 995                             # final volume of sample


# ------------------------
# Protocol parameters  (OUTPUTS)
# ------------------------
num_samples = 96                                # num of samples
tube_type_dest = 'criotubo'                      # Selected destination tube for this protocol


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 5
x_offset = [0, 0]


# ----------------------------
# Main
# ----------------------------
(_, _, _, _, pickup_height) = lab_stuff.tubes(tube_type_source)
(_, _, _, dispense_height, _) = lab_stuff.tubes(tube_type_dest)
(sample) = lab_stuff.buffer(buffer_name)


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000µl filter tiprack') for slot in ['11']]

    # Pipette
    p1000 = ctx.load_instrument('p1000_single_gen2', 'right', tip_racks=tips)

    # Source
    source_rack_num = math.ceil(num_samples / NUM_OF_SOURCES_PER_RACK) if num_samples < MAX_NUM_OF_SOURCES else MIN_NUM_OF_SOURCES
    source_racks = [ctx.load_labware(
        'opentrons_24_aluminumblock_generic_2ml_screwcap', slot,
        'Bloque Aluminio opentrons 24 screwcaps 2000 µL' + str(i + 1)) for i, slot in enumerate(['10', '7', '4', '1'][:source_rack_num])
    ]
    source_racks = common.generate_source_table(source_racks)
    sources = source_racks[:num_samples]

    # Destination
    rack_num = math.ceil(num_samples / NUM_OF_SOURCES_PER_RACK) if num_samples < MAX_NUM_OF_SOURCES else MIN_NUM_OF_SOURCES
    dest_racks = [ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', slot,
        'source tuberack with screwcap' + str(i + 1)) for i, slot in enumerate(['5', '6', '2', '3'][:rack_num])
    ]
    dest_racks = common.generate_source_table(dest_racks)
    destinations = dest_racks[:num_samples]

    # ------------------
    # Protocol
    # ------------------
    if not p1000.hw_pipette['has_tip']:
        common.pick_up(p1000)

    for s, d in zip(sources, destinations):
        if not p1000.hw_pipette['has_tip']:
            common.pick_up(p1000)

        # Calculate pickup_height based on remaining volume and shape of container
        common.move_vol_multichannel(ctx, p1000, reagent=sample, source=s, dest=d,
                              vol=volume_sample, air_gap_vol=air_gap_vol_sample,
                              pickup_height=pickup_height, disp_height=dispense_height,
                              x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p1000.drop_tip()

    # Notify users
    # common.notify_finish_process()
