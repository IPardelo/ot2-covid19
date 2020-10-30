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
    'protocolName': 'Dispensacion de agua',
    'author': 'Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.3',
    'description': 'Paso previo a extraccion para minitubos'
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
reagent_name = 'Sample'                   # Selected buffer for this protocol
tube_type_source = 'criotubo'             # Selected source tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
num_destinations = 22                     # total number of destinations
volume_to_be_transfered = 45              # volume in uL to be moved from 1 source to 1 destination
#tube_type_destination = 'minitubo'       # Selected source tube for this protocol


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
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, '200µl filter tiprack') for slot in ['11']]

    # Pipette
    p200 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips)

    # Source
    reagents = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '6', 'Buffer tuberack in Falcon tube')
    source0 = reagents.wells()[0]
    source1 = reagents.wells()[1]
   

    # Destination (in this case 96 well plate)
    dest_plate = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '3', 'Tubos individuales en placa pcr aluminio')
    destinations0 = dest_plate.wells()[:8]
    destinations1 = dest_plate.wells()[24:32]
    destinations2 = dest_plate.wells()[48:56]
    destinations3 = dest_plate.wells()[72:80]
    
    # Aplanamos tupla de posicions
    part1 = []
    part1.extend(destinations0)
    part1.extend(destinations1)
    part1.extend(destinations2)

    part2 = []
    part2.extend(destinations3)


    # ------------------
    # Protocol
    # ------------------
    if not p200.hw_pipette['has_tip']:
        common.pick_up(p200)

    if num_destinations <= 24:
        for d in part1:
            if not p200.hw_pipette['has_tip']:
                common.pick_up(p200)
            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p200, reagent=sample, source=source0, dest=d,
                                        vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                        pickup_height=pickup_height, disp_height=dispense_height,
                                        x_offset=x_offset, blow_out=True, touch_tip=True)
    else:
        for d in part1:
            if not p200.hw_pipette['has_tip']:
                common.pick_up(p200)
            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p200, reagent=sample, source=source0, dest=d,
                                        vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                        pickup_height=pickup_height, disp_height=dispense_height,
                                        x_offset=x_offset, blow_out=True, touch_tip=True)
        for d in part2:
            if not p200.hw_pipette['has_tip']:
                common.pick_up(p200)
            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p200, reagent=sample, source=source1, dest=d,
                                        vol=volume_to_be_transfered, air_gap_vol=air_gap_vol_sample,
                                        pickup_height=pickup_height, disp_height=dispense_height,
                                        x_offset=x_offset, blow_out=True, touch_tip=True)                                

    # Drop pipette tip
    p200.drop_tip()                                 

    # Notify users
    # common.notify_finish_process()