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
    'apiLevel': '2.0',
    'description': 'Dispense samples, with pooling, from 4 x 96 x tube rack in 96 Well Plate'
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
num_sources = 96                                # num of sources


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
tube_type_dest = 'eppendorf'                    # Selected destination tube for this protocol
num_dest = 1                                    # total number of destinations
volume_to_be_transfered = 100                   # volume in uL to be moved from 1 source to 1 destination


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 5
x_offset = [0, 0]


# ----------------------------
# Main
# ----------------------------
(_, _, _, dispense_height, _) = lab_stuff.tubes(tube_type_dest)
(sample) = lab_stuff.buffer(reagent_name)


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot, 'Tiprack') for slot in ['11']]

    # Pipette
    p300 = ctx.load_instrument('p300_single_gen2', 'left', tip_racks=tips)

    # Source (in this case X opentrons 24 tube rack 2ml)
    source_plate = ctx.load_labware('abgene_96_wellplate_800ul', '1', 'PCR')
    sources = source_plate.wells()[:num_sources]

    # Destination (in this case Xs well plate)
    dest_plate = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '4', 'Tuberack')
    destinations = dest_plate.wells()[:num_dest]

    # ------------------
    # Protocol
    # ------------------
    if not p300.hw_pipette['has_tip']:
        common.pick_up(p300)

    custom_sources = split_list(sources, num_sources)

    for sources, dest in zip(custom_sources, destinations):
        for source in sources:
            if not p300.hw_pipette['has_tip']:
                common.pick_up(p300)

            # Calculate pickup_height based on remaining volume and shape of container
            common.move_vol_multichannel(ctx, p300, reagent=sample, source=source, dest=dest,
                                         vol=volume_to_be_transfered / num_sources, air_gap_vol=air_gap_vol_sample,
                                         pickup_height=1, disp_height=dispense_height,
                                         x_offset=x_offset, blow_out=True, touch_tip=True)
            # Drop pipette tip
            p300.drop_tip()

    # Notify users
    # common.notify_finish_process()


# ----------------------------
# Aux functions
# ----------------------------
def split_list(l: list, n: int):
    """
    Split list in several chunks of n elements

    :param l: list to split in chunks
    :param n: number of elements per chunk

    :return: chunk list's generator

    :example of use:
    list(split_list(list(range(0,100)), 10))
    """
    for i in range(0, len(l), n):
        yield l[i:i+n]
