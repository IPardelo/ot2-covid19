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
    'apiLevel': '2.0',
    'description': 'PCR preparation, mix the master mix and rna sample in pcr plate'
}


# ------------------------
# Protocol parameters
# ------------------------
numero_muestras = 6                             # Número de muestras (sin las muestras de control) 
                                                    #   (máximo 22, o 20 si es doble Mastermix)
brand_name = 'roche'
master_mix_vol, arn_vol, doble_mix = lab_stuff.brands(brand_name)

tipo_de_tubo = 'labturbo'                           # Tipo de tubo que contiene el ARN: 'labturbo' o 'criotubo'


# ------------------------
# Other parameters
# ------------------------
(_, _, _, _, pickup_height) = lab_stuff.tubes(tipo_de_tubo)
num_cols = math.ceil(numero_muestras / 8)
x_offset = [0, 0]
air_gap_vol_source = 2
diameter_sample = 8.25
area_section_sample = (math.pi * diameter_sample**2) / 4


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

rna_sample = {
    'name': 'RNA samples',
    'flow_rate_aspirate': 1,
    'flow_rate_dispense': 1,
    'rinse': False,
    'delay': 0,
    'reagent_reservoir_volume': 200 * 24,
    'num_wells': 24,
    'h_cono': 4,
    'v_cono': 4 * area_section_sample * diameter_sample * 0.5 / 3,
    'vol_well_original': 200,
    'vol_well': 200,
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

    # Source (master_mix in and deep-weel with NUM SAMPLES x RNA samples)
    source_master_mix = ctx.load_labware('opentrons_24_aluminumblock_generic_2ml_screwcap', '7', 'Bloque Aluminio opentrons 24 screwcaps 2000 µL')
    source_master_mix = source_master_mix.wells()

    source_rna_samples = ctx.load_labware('opentrons_24_tuberack_generic_2ml_screwcap', '5', 'source tuberack with screwcap')
    sources_rna = source_rna_samples.wells()

    # Destination (NUM SAMPLES x pcr plate)
    pcr_plate_destination = ctx.load_labware('abi_fast_qpcr_96_alum_opentrons_100ul', '1', 'chilled qPCR final plate')
    destinations = pcr_plate_destination.wells()

    # ------------------
    # Protocol
    # ------------------
    # Dispense master mix
    for i in range(0, numero_muestras + 2):
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        source = source_master_mix[0]
        destination = destinations[i]
        common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=source, dest=destination,
                                         vol=master_mix_vol, air_gap_vol=air_gap_vol_source,
                                         x_offset=x_offset, pickup_height=pickup_height,
                                         disp_height=-10, blow_out=True, touch_tip=True)
        p20.drop_tip()
        
        if doble_mix:        
            common.pick_up(p20)    
            source = source_master_mix[1]
            destination = destinations[48 + i]
            common.move_vol_multichannel(ctx, p20, reagent=master_mix, source=source, dest=destination,
                                         vol=master_mix_vol, air_gap_vol=air_gap_vol_source,
                                         x_offset=x_offset, pickup_height=pickup_height,
                                         disp_height=-10, blow_out=True, touch_tip=True)
            p20.drop_tip()
    

    # Dispense RNA
    for i in range(0, numero_muestras + 2):
        if not p20.hw_pipette['has_tip']:
            common.pick_up(p20)

        source = sources_rna[i]
        destination = destinations[i]
        common.move_vol_multichannel(ctx, p20, reagent=rna_sample, source=source, dest=destination,
                                         vol=arn_vol, air_gap_vol=air_gap_vol_source,
                                         x_offset=x_offset, pickup_height=pickup_height,
                                         disp_height=-10, blow_out=True, touch_tip=True)
        p20.drop_tip()

        if doble_mix:
            destination = destinations[48 + i]
            common.pick_up(p20)
            common.move_vol_multichannel(ctx, p20, reagent=rna_sample, source=source, dest=destination,
                                         vol=arn_vol, air_gap_vol=air_gap_vol_source,
                                         x_offset=x_offset, pickup_height=pickup_height,
                                         disp_height=-10, blow_out=True, touch_tip=True)
            p20.drop_tip()

        