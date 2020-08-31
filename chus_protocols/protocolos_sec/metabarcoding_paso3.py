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
    'apiLevel': '2.3',
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
tube_type_mastermix = 'criotubo'            # Selected mastermix tube for this protocol
tube_type_sample = 'eppendorf'              # Selected sample tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
vol_to_mix = 10                             # Vol to mix in mastermix
mastermix_vol_to_move = 272.82              # volume to move from mastermix tube to pcr tubes
sample_vol_to_move = 5                      # volume to move from pcr samples to the pcr plate
num_destinations = 96                       # Num of destinations from pcr plate
pcr_index_vol_to_move = 10                  # PCR Index vol to move


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 1
x_offset = [0, 0]
rounds = 3


# ----------------------------
# Main
# ----------------------------
buffer = lab_stuff.buffer(buffer_name)
_, _, _, _, pickup_height = lab_stuff.tubes(tube_type_mastermix)
_, _, _, dispense_height, _ = lab_stuff.tubes(tube_type_sample)

num_cols = math.ceil(num_destinations / 8)
num_rows = math.ceil(num_destinations / 12)
pcr_final_vol = mastermix_vol_to_move / 12

def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20µl filter tiprack') for slot in ['10', '11']]

    # Pipette
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)
    m20 = ctx.load_instrument('p20_multi_gen2', 'left', tip_racks=tips)

    # Modules
    tempdeck = ctx.load_module('temperature module gen2', '1')
    tempdeck.set_temperature(4)

    # Mastermix source
    mastermix = tempdeck.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap')
    mastermix_sources = mastermix.wells()[:2]
    mastermix_volumes = [1200, 485, 485]
    mastermix_sources = zip(mastermix_sources, mastermix_volumes)
    mastermix_tube = mastermix.wells()[2]

    # PCR Index source
    source_plate = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '5', 'Tuberack')
    source_1 = source_plate.wells()[:8]
    source_2 = source_plate.wells()[8:20]

    # Mastermix destination 1
    dest_plate1 = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '2', 'PCR plate')
    dest_1 = dest_plate1.columns()[0][:num_rows]
    source_3 = dest_plate1.wells()[0]

    # Mastermix and PCR Index destination
    dest_plate2 = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '3', 'PCR plate')
    dest_2 = dest_plate2.rows()[0][:num_cols]
    num_dest_1 = dest_plate2.rows()[:num_rows]
    num_dest_2 = dest_plate2.columns()[:num_cols]

    mov_1 = zip(source_1, num_dest_1)
    mov_2 = zip(source_2, num_dest_2)

    # PCR con muestras
    source_plate4 = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '6', 'PCR plate')
    dest_4 = source_plate4.rows()[0][:num_cols]


    # ------------------
    # Protocol
    # ------------------

    # ------------------
    # Hacemos la mastermix
    # ------------------

    for s, v in mastermix_sources:
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        common.move_vol_multichannel(ctx, p20, reagent=buffer, source=s, dest=mastermix_tube,
                                     vol=v, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)

        # Drop pipette tip
        p20.drop_tip()  # TODO: preguntar si hace falta tirar la punta o no

    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    common.custom_mix(p20, reagent=buffer, location=mastermix_tube, vol=vol_to_mix,
                      rounds=rounds, blow_out=True, mix_height=dispense_height, x_offset=x_offset, source_height=dispense_height)

    # ------------------
    # Dispensamos mastermix en tira de pcr y con la multi lo propagamos en la placa pcr del slot 3
    # ------------------

    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    for d in dest_1:
        common.move_vol_multichannel(ctx, p20, reagent=buffer, source=mastermix_tube, dest=d,
                                     vol=mastermix_vol_to_move, air_gap_vol=air_gap_vol_sample,
                                     x_offset=x_offset, pickup_height=1, disp_height=-10,
                                     blow_out=True, touch_tip=False)

    p20.drop_tip()

    if not m20.hw_pipette['has_tip']:
        common.pick_up(m20)

    for d in dest_2:
        common.move_vol_multichannel(ctx, m20, reagent=buffer, source=source_3, dest=d,
                                     vol=pcr_final_vol, air_gap_vol=air_gap_vol_sample,
                                     x_offset=x_offset, pickup_height=1, disp_height=-10,
                                     blow_out=True, touch_tip=True)
    m20.drop_tip()

    # ------------------
    # PCR Index
    # ------------------

    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    for s, d in mov_1:
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)
        for destination in d:
            common.move_vol_multichannel(ctx, p20, reagent=buffer, source=s, dest=destination,
                                            vol=pcr_index_vol_to_move, air_gap_vol=air_gap_vol_sample,
                                            pickup_height=pickup_height, disp_height=0,
                                            x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p20.drop_tip()

    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    for s, d in mov_2:
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)
        for destination in d:
            if not p20.hw_pipette['has_tip']:
                common.pick_up(p20)
            common.move_vol_multichannel(ctx, p20, reagent=buffer, source=s, dest=destination,
                                            vol=pcr_index_vol_to_move, air_gap_vol=air_gap_vol_sample,
                                            pickup_height=pickup_height, disp_height=0,
                                            x_offset=x_offset, blow_out=True, touch_tip=True)
            # Drop pipette tip
            p20.drop_tip()

    # ------------------
    # PCR con muestras a PCR Index
    # ------------------

    for s, d in zip(dest_2, dest_4):
        if not m20.hw_pipette['has_tip']:
            common.pick_up(m20)
        common.move_vol_multichannel(ctx, m20, reagent=buffer, source=s, dest=d,
                                     vol=sample_vol_to_move, air_gap_vol=air_gap_vol_sample,
                                     x_offset=x_offset, pickup_height=1, disp_height=-10,
                                     blow_out=True, touch_tip=True)
    m20.drop_tip()


    # Notify users
    # common.notify_finish_process()
