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
    'protocolName': 'C2',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'Creates RNAteca, in other words, dispense 40ul from deep-weel to 1.5ml Eppendorf tubes'
}

# ------------------------
# Protocol parameters
# ------------------------
NUM_SAMPLES = 16
brand_name = 'vircell'

x_offset = [0, 0]
volume_source = 19      # FIXME: no deja aspirar 20?!
air_gap_vol_source = 1
diameter_sample = 8.25
area_section_sample = (math.pi * diameter_sample**2) / 4

(brand_master_mix, arn) = lab_stuff.brands(brand_name)

sample = {
    'name': 'RNA samples',
    'flow_rate_aspirate': 1,
    'flow_rate_dispense': 1,
    'rinse': False,
    'delay': 0,
    'reagent_reservoir_volume': 20 * 24,
    'num_wells': 24,
    'h_cono': 4,
    'v_cono': 4 * area_section_sample * diameter_sample * 0.5 / 3,
    'vol_well_original': 20,
    'vol_well': 20,
    'unused': [],
    'col': 0,
    'vol_well': 0
}

# following volumes in ul
master_mix = {
    'name': 'master mix',
    'flow_rate_aspirate': 1,
    'flow_rate_dispense': 1,
    'rinse': False,
    'delay': 0,
    'reagent_reservoir_volume': 1500,
    'num_wells': 1,
    'h_cono': 4,
    'v_cono': 4 * area_section_sample * diameter_sample * 0.5 / 3,
    'vol_well_original': 1500,
    'vol_well': 1500,
    'unused': [],
    'col': 0,
    'vol_well': 0
}


# ----------------------------
# Main
# ----------------------------
def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_20ul', slot, '20µl filter tiprack') for slot in ['11']]

    # Pipette
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    # Source (in this case NUM_SAMPLES well plate)
    source_plate = ctx.load_labware('abgene_96_wellplate_800ul', '5', 'ABGENE 96 Well Plate 800 µL')
    sources = source_plate.wells()[:NUM_SAMPLES]

    # Destination (in this case NUM_SAMPLES 1.5ml Eppendorf tubes)
    rack_num = math.ceil(NUM_SAMPLES / 24) if NUM_SAMPLES < 96 else 4
    destination_racks = [ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', slot,
        'source tuberack with screwcap' + str(i + 1)) for i, slot in enumerate(['8', '4', '6', '2'][:rack_num])
    ]
    destination_racks_full = common.generate_source_table(destination_racks)
    destinations = destination_racks_full[:NUM_SAMPLES]

    # ------------------
    # Protocol
    # ------------------
    for s, d in zip(sources, destinations):
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        # 2 * 20ul ~> 40ul of rna sample
        for _ in range(2):
            common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=s, dest=d,
                                     vol=brand_master_mix, air_gap_vol=air_gap_vol_source,
                                     x_offset=x_offset, pickup_height=1, disp_height=-10,
                                     blow_out=True, touch_tip=True)
        # Drop pipette tip
        p20.drop_tip()
