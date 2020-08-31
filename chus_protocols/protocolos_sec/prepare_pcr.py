# -*- coding: utf-8 -*-

import pandas as pd
import importlib
import math

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
    'protocolName': 'Dispensar muestras a placa pcr',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de A Coruña (CHUAC)',
    'apiLevel': '2.0',
    'description': 'Prepara una pcr dispensando muestras desde un eppendorf a una placa pcr'
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
tube_type_source = 'eppendorf'              # Selected source tube for this protocol


# ------------------------
# Protocol parameters (OUTPUTS)
# ------------------------
num_destinations = 96                       # total number of destinations
volume_to_be_transferred = 200              # volume in uL to be moved from 1 source to 1 destination
dispense_height = -10


# ------------------------
# Pipette parameters
# ------------------------
air_gap_vol_sample = 5
x_offset = [0, 0]

# ----------------------------
# Read csv and compute vols
# ----------------------------

data = pd.read_csv("prepare_pcr.csv")

# Ci = Concentracion inicial
# Cf = Concentracion final
# Vf = Volumen final
# Vi = Volumen incognita
# Vt = Volumen tampon

def calculate_vi(row):
    return (row['Cf'] * row['Vf']) / row['Ci']


def calculate_vt(row):
    return row['vi'] - row['Vf']


data['vi'] = data.apply(calculate_vi, axis=1)
data['vt'] = data.apply(calculate_vt, axis=1)

vi = list(data['vi'].fillna(0)).reverse()
vt = list(data['vt'].fillna(0)).reverse()


# ----------------------------
# Main
# ----------------------------
sample = lab_stuff.buffer(reagent_name)
_, _, _, _, pickup_height = lab_stuff.tubes(tube_type_source)


def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_1000ul', slot, '1000µl filter tiprack') for slot in ['10', '11']]

    # Pipette
    p20 = ctx.load_instrument('p20_single_gen2', 'right', tip_racks=tips)

    # Source Samples
    rack_num = math.ceil(num_samples / NUM_OF_SOURCES_PER_RACK) if num_samples < MAX_NUM_OF_SOURCES else MIN_NUM_OF_SOURCES
    source_racks = [ctx.load_labware(
        'opentrons_24_tuberack_generic_2ml_screwcap', slot,
        'source tuberack with screwcap' + str(i + 1)) for i, slot in enumerate(['1', '2', '4', '5'][:rack_num])
    ]
    sample_sources_full = common.generate_source_table(source_racks)
    sample_sources = sample_sources_full[:num_samples]

    # Source TRIS
    tris = ctx.load_labware('opentrons_6_tuberack_falcon_50ml_conical', '6', 'Buffer tuberack in Falcon tube')
    tris_phalcon = tris.wells()[0]

    # Destination (in this case 96 well plate)
    dest_plate = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '3', 'PCR final plate')
    destinations = dest_plate.wells()[:num_destinations]

    # ------------------
    # Protocol
    # ------------------
    if not p20.hw_pipette['has_tip']:
        common.pick_up(p20)

    # Dispense 4mM of sample in PCR plate
    for s, d in zip(sample_sources, destinations):
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        sample_volume_to_be_transferred = vi.pop()

        # Calculate pickup_height based on remaining volume and shape of container
        common.move_vol_multichannel(ctx, p20, reagent=sample, source=s, dest=d,
                                     vol=sample_volume_to_be_transferred, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p20.drop_tip()

    # Dispense rest volume of TRIS in each sample of PCR
    for d in destinations:

        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        tris_volume_to_be_transferred = vt.pop()
        common.move_vol_multichannel(ctx, p20, reagent=sample, source=tris_phalcon, dest=d,
                                     vol=tris_volume_to_be_transferred, air_gap_vol=air_gap_vol_sample,
                                     pickup_height=pickup_height, disp_height=dispense_height,
                                     x_offset=x_offset, blow_out=True, touch_tip=True)
        # Drop pipette tip
        p20.drop_tip()
