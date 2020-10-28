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
    'protocolName': 'Extracción cruda tubo',
    'author': 'Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.3',
    'description': 'Extraccion para minitubos'
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
reagent_name = 'Sample'                    # Selected buffer for this protocol
num_samples = 32                           # total number of samples
tube_type_source = 'criotubo'             # Selected source tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
volume_to_be_transfered = 15              # volume in uL to be moved from 1 source to 1 destination
#tube_type_destination = 'minitubo'             # Selected source tube for this protocol


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
#(_, _, _, dispense_height, _) = lab_stuff.tubes(tube_type_destination)

dispense_height = -10


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20µl filter tiprack') for slot in ['11']]

    # Pipette
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    # Modules
    temp_hot = ctx.load_module('temperature module gen2', '1')
    temp_hot.set_temperature(98)

    # Source
    rack_num = math.ceil(num_samples / NUM_OF_SOURCES_PER_RACK) if num_samples < MAX_NUM_OF_SOURCES else MIN_NUM_OF_SOURCES
    source_racks = [ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', slot,
        'Tuberack 24 tubos normales' + str(i + 1)) for i, slot in enumerate(['8', '9', '5'][:rack_num])
    ]
    reagents = common.generate_source_table(source_racks)
    sample_sources = reagents[0:num_samples]

    # Destination (in this case 96 well plate)
    dest_plate = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '3', 'Tubos individuales en placa pcr aluminio')
    destinations0 = dest_plate.wells()[:8]
    destinations1 = dest_plate.wells()[24:32]
    destinations2 = dest_plate.wells()[48:56]
    destinations3 = dest_plate.wells()[72:80]
    
    # Aplanamos tupla de posicions
    flat_list = []
    flat_list.extend(destinations0)
    flat_list.extend(destinations1)
    flat_list.extend(destinations2)
    flat_list.extend(destinations3)
    mov = zip(sample_sources, flat_list)

    # ------------------
    # Protocol
    # ------------------
    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    for s, d in mov:
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        # Calculate pickup_height based on remaining volume and shape of container
        common.move_vol_multichannel(ctx, p20, reagent=sample, source=s, dest=d,
                                     vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p20.drop_tip()

    # Notify users
    # common.notify_finish_process()
