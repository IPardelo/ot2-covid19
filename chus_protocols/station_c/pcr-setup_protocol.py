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


metadata = {
    'protocolName': 'C1',
    'author': 'Luis Lorenzo Mosquera, Victor Soroña Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'PCR preparation, mix the master mix and rna sample in pcr plate'
}

# ------------------------
# Protocol parameters
# ------------------------
NUM_SAMPLES = 10            # Máximo: 48 para vircell o genomica, 96 para los demás 
brand_name = 'vircell'


# ------------------------
# Other parameters
# ------------------------
air_gap_vol_source = 2
diameter_sample = 8.25
x_offset = [0, 0]
area_section_sample = (math.pi * diameter_sample**2) / 4

# following volumes in ul
brands = {
    'seegene-2019-ncov': {
        'master_mix': 17,
        'arn': 8
    },
    'seegene-sars-cov2': {
        'master_mix': 15,
        'arn': 5
    },
    'thermofisher': {
        'master_mix': 15,
        'arn': 10
    },
    'roche': {
        'master_mix': 10,
        'arn': 10
    },
    'vircell': {
        'master_mix': 15,
        'arn': 5,
        'split_pcr': True
    },
    'vircell_multiplex': {
        'master_mix': 15,
        'arn': 5,
        'split_pcr': False
    },
    'genomica': {
        'master_mix': 15,
        'arn': 5,
        'split_pcr': True
    }
}

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

    # Pipettes
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    # Source (master_mix)
    source_master_mix = ctx.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap', '7', 'Bloque Aluminio opentrons 24 screwcaps 2000 µL')
    source_master_mix = source_master_mix.wells()

    # Destination (NUM SAMPLES x pcr plate)
    pcr_plate_destination = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '1', 'chilled qPCR final plate')
    destinations = pcr_plate_destination.wells()

    # Set our brand
    brand = brands.get(brand_name)


    # ------------------
    # Protocol
    # ------------------
    # Dispense master mix
    for i in range(0, NUM_SAMPLES):
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)
        if brand.get('split_pcr'):
            source = source_master_mix[0]
            destination = destinations[i]
            common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=source, dest=destination,
                                     vol=brand.get('master_mix'), air_gap_vol=air_gap_vol_source,
                                     x_offset=x_offset, pickup_height=1, rinse=master_mix.get('rinse'),
                                     disp_height=-10, blow_out=True, touch_tip=True)
            source = source_master_mix[1]
            destination = destinations[48 + i]
            common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=source, dest=destination,
                                     vol=brand.get('master_mix'), air_gap_vol=air_gap_vol_source,
                                     x_offset=x_offset, pickup_height=1, rinse=master_mix.get('rinse'),
                                     disp_height=-10, blow_out=True, touch_tip=True)
        else:
            source = source_master_mix[0]
            destination = destinations[i]
            common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=source, dest=destination,
                                     vol=brand.get('master_mix'), air_gap_vol=air_gap_vol_source,
                                     x_offset=x_offset, pickup_height=1, rinse=master_mix.get('rinse'),
                                     disp_height=-10, blow_out=True, touch_tip=True)
    p20.drop_tip()
