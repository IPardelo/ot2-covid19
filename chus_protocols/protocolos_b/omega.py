# -*- coding: utf-8 -*-

import math
import importlib
from opentrons import protocol_api
from opentrons.types import Point

LIBRARY_PATH = '/root/ot2-covid19/library/'

# Load library
spec = importlib.util.spec_from_file_location("library.protocols.common_functions",
                                              "{}protocols/common_functions.py".format(LIBRARY_PATH))
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)

metadata = {
    'protocolName': 'B0: OMEGA',
    'author': 'Luis Lorenzo Mosquera, Victor Soñora Pombo & Ismael Castiñeira Paz',
    'source': 'Hospital Clínico Universitario de Santiago (CHUS)',
    'apiLevel': '2.0',
    'description': 'Extracts ARN from samples for OMEGA machines'
}

# ------------------------
# Protocol parameters
# ------------------------
NUM_SAMPLES = 8
num_cols = math.ceil(NUM_SAMPLES / 8)

lysis = {
    'flow_rate_aspirate': 3,
    'flow_rate_dispense': 3,
    'flow_rate_aspirate_mix': 15,
    'flow_rate_dispense_mix': 25,
    'air_gap_vol_bottom': 5,
    'air_gap_vol_top': 0,
    'disposal_volume': 1,
    'rinse': True,
    'max_volume_allowed': 180,
    'reagent_volume': 530,
    'reagent_reservoir_volume':  (NUM_SAMPLES + 5) * 530,
    'num_wells': math.ceil((NUM_SAMPLES + 5) * 530 / 13000),
    'h_cono': 1.95,
    'v_cono': 750,
    'tip_recycling': 'A1',
    'vol_well': (NUM_SAMPLES + 5) * 530 / math.ceil((NUM_SAMPLES + 5) * 530 / 13000),
    'col': 0
}

vhb = {}
spr = {}
water = {}
elution = {
    'num_wells': num_cols
}

sample = {}

multi_well_rack_area = 568
mag_height = 14
sample_volume = 200
x_offset = [0, 0]
air_gap_vol_sample = 3


# ----------------------------
# Main
# ----------------------------
def run(ctx: protocol_api.ProtocolContext):
    # ------------------------
    # Load LabWare
    # ------------------------
    # Tip racks
    tips = [ctx.load_labware('opentrons_96_filtertiprack_200ul', slot,
                             '200µl filter tiprack') for slot in ['6', '7', '8', '9', '10', '11']]
    # Pipette
    m300 = ctx.load_instrument('p300_multi_gen2', 'right', tip_racks=tips)

    # Reservoirs
    waste = ctx.load_labware('nest_1_reservoir_195ml', '5', 'waste reservoir').wells()[0]

    # well racks
    reagent_res_0 = ctx.load_labware('nest_12_reservoir_15ml', '2', 'reagent deepwell plate 1')
    reagent_res_1 = ctx.load_labware('nest_12_reservoir_15ml', '3', 'reagent deepwell plate 2')

    # Magnet module
    magdeck = ctx.load_module('magdeck', '4')

    # Deep wells
    # Come from A Robot and is above magnet module
    deep_well_plate = magdeck.load_labware('nest_96_wellplate_2000ul', 'NEST 96 Well Plate 2000 µL')
    magdeck.disengage()

    # Destination deep well
    destination = ctx.load_labware('nest_96_wellplate_2000ul', '1', 'NEST 96 Well Plate 2000 µL')

    # ------------------
    # Protocol
    # ------------------
    # Declare which reagents are in each reservoir as well as deep well and source plate
    lysis['reagent_reservoir'] = reagent_res_0.rows()[0][:4]
    vhb['reagent_reservoir'] = reagent_res_0.rows()[0][4:8]
    spr['reagent_reservoir'] = reagent_res_1.rows()[0][0:8]
    water['reagent_reservoir'] = reagent_res_0.rows()[0][-1]
    work_destinations = deep_well_plate.rows()[0][:elution.get('num_wells')]
    final_destinations = destination.rows()[0][:elution.get('num_wells')]

    # Transfer lysis
    if not m300.hw_pipette['has_tip']:
        common.pick_up(m300)

    x_offset_source = 0
    x_offset_dest = 0
    rinse = True

    lysis_trips = math.ceil(lysis.get('reagent_volume') / lysis.get('max_volume_allowed'))
    lysis_volume = lysis.get('reagent_volume') / lysis_trips
    lysis_transfer_vol = []

    for i in range(lysis_trips):
        lysis_transfer_vol.append(lysis_volume + lysis.get('disposal_volume'))

    for i in range(num_cols):
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for j, transfer_vol in enumerate(lysis_transfer_vol):
            pickup_height, change_col = common.calc_height(ctx, lysis, multi_well_rack_area, transfer_vol * 8)
            if change_col:
                common.custom_mix(m300, lysis, lysis.reagent_reservoir[lysis.col], vol=180, rounds=10, blow_out=False,
                                  mix_height=0, offset=0)
            common.move_vol_multi(ctx, m300, reagent=lysis, source=lysis.get('reagent_reservoir')[lysis.get('col')],
                                  dest=work_destinations[i], vol=transfer_vol, x_offset_source=x_offset_source,
                                  x_offset_dest=x_offset_dest, pickup_height=pickup_height, rinse=rinse,
                                  avoid_droplet=False, wait_time=2, blow_out=False)
        common.custom_mix(m300, lysis, location=work_destinations[i], vol=180, rounds=20, blow_out=False, mix_height=0, x_offset=[0, 0])
        m300.move_to(work_destinations[i].top(0))
        m300.air_gap(lysis.get('air_gap_vol_bottom'))

    # Incubating five minutes without magnet
    ctx.delay(seconds=300, msg='Incubating for 300 seconds.')

    # Incubating five minutes with magnet on
    magdeck.engage(height=mag_height)
    ctx.delay(seconds=300, msg='Incubating ON magnet for 300 seconds.')

    # Remove supernatant
    supernatant_trips = math.ceil((lysis.get('reagent_volume') + sample_volume) / lysis.get('max_volume_allowed'))
    supernatant_volume = lysis.get('max_volume_allowed')
    supernatant_transfer_vol = []
    for i in range(supernatant_trips):
        supernatant_transfer_vol.append(supernatant_volume + elution.get('disposal_volume'))
    x_offset_rs = 2

    for i in range(num_cols):
        x_offset_source = common.find_side(i) * x_offset_rs
        x_offset_dest = 0
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in supernatant_transfer_vol:
            pickup_height = 1
            common.move_vol_multi(m300, reagent=elution, source=work_destinations[i], dest=waste, vol=transfer_vol,
                                  x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=False, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
    # Switch off magnet
    magdeck.disengage()

    # Dispense VHB/WB1
    vhb_trips = math.ceil(vhb.reagent_volume / vhb.max_volume_allowed)
    vhb_volume = vhb.reagent_volume / vhb_trips
    vhb_transfer_vol = []
    for i in range(vhb_trips):
        vhb_transfer_vol.append(vhb_volume + vhb.disposal_volume)
    x_offset_rs = 2.5
    rinse = False
    # whb washes
    for i in range(num_cols):
        x_offset_source = 0
        x_offset_dest = -1 * common.find_side(i) * x_offset_rs
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in vhb_transfer_vol:
            pickup_height, change_col = common.calc_height(vhb, multi_well_rack_area, transfer_vol*8)
            common.move_vol_multi(m300, reagent=vhb, source=vhb.reagent_reservoir[vhb.col], dest=work_destinations[i],
                                  vol=transfer_vol, x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=rinse, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        common.custom_mix(m300, vhb, location=work_destinations[i], vol=180, rounds=20, blow_out=False, mix_height=0,
                          offset=x_offset_dest)
        m300.move_to(work_destinations[i].top(0))
        m300.air_gap(vhb.air_gap_vol_bottom)
        m300.drop_tip()

    # Incubating five minutes with magnet on
    magdeck.engage(height=mag_height)
    ctx.delay(seconds=300, msg='Incubating ON magnet for 300 seconds.')

    # Remove supernatant
    supernatant_trips = math.ceil(vhb.reagent_volume / vhb.max_volume_allowed)
    supernatant_volume = vhb.max_volume_allowed
    supernatant_transfer_vol = []
    for i in range(supernatant_trips):
        supernatant_transfer_vol.append(supernatant_volume + elution.disposal_volume)
    x_offset_rs = 2

    for i in range(num_cols):
        x_offset_source = common.find_side(i) * x_offset_rs
        x_offset_dest = 0
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in supernatant_transfer_vol:
            pickup_height = 1
            common.move_vol_multi(m300, reagent=elution, source=work_destinations[i], dest=waste, vol=transfer_vol,
                                  x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=False, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        m300.drop_tip()

    # switch off magnet
    magdeck.disengage()

    # Dispense SPR
    spr_trips = math.ceil(spr.reagent_volume / spr.max_volume_allowed)
    spr_volume = spr.reagent_volume / spr_trips
    spr_transfer_vol = []
    for i in range(spr_trips):
        spr_transfer_vol.append(spr_volume + spr.disposal_volume)
    x_offset_rs = 2.5
    rinse = False

    ########
    # spr washes
    for i in range(num_cols):
        x_offset_source = 0
        x_offset_dest = -1 * common.find_side(i) * x_offset_rs
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in spr_transfer_vol:
            pickup_height, change_col = common.calc_height(spr, multi_well_rack_area, transfer_vol*8)
            common.move_vol_multi(m300, reagent=spr, source=spr.reagent_reservoir[spr.col], dest=work_destinations[i],
                                  vol=transfer_vol, x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=rinse, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        common.custom_mix(m300, vhb, location=work_destinations[i], vol=180, rounds=20, blow_out=False, mix_height=0,
                          offset=x_offset_dest)
        m300.move_to(work_destinations[i].top(0))
        m300.air_gap(spr.air_gap_vol_bottom)
        m300.drop_tip()

    # Incubating five minutes with magnet on
    magdeck.engage(height=mag_height)
    ctx.delay(seconds=300, msg='Incubating ON magnet for 300 seconds.')

    # Remove supernatant
    supernatant_trips = math.ceil(spr.reagent_volume / spr.max_volume_allowed)
    supernatant_volume = spr.max_volume_allowed
    supernatant_transfer_vol = []
    for i in range(supernatant_trips):
        supernatant_transfer_vol.append(supernatant_volume + elution.disposal_volume)
    x_offset_rs = 2

    for i in range(num_cols):
        x_offset_source = common.find_side(i) * x_offset_rs
        x_offset_dest = 0
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in supernatant_transfer_vol:
            pickup_height = 1
            common.move_vol_multi(m300, reagent=elution, source=work_destinations[i], dest=waste, vol=transfer_vol,
                                  x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=False, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        m300.drop_tip()

    # switch off magnet
    magdeck.disengage()

    # Add spr (again?)
    spr_trips = math.ceil(spr.reagent_volume / spr.max_volume_allowed)
    spr_volume = spr.reagent_volume / spr_trips
    spr_transfer_vol = []
    for i in range(spr_trips):
        spr_transfer_vol.append(spr_volume + spr.disposal_volume)
    x_offset_rs = 2.5
    rinse = False

    # spr washes
    for i in range(num_cols):
        x_offset_source = 0
        x_offset_dest = -1 * common.find_side(i) * x_offset_rs
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in spr_transfer_vol:
            pickup_height, change_col = common.calc_height(spr, multi_well_rack_area, transfer_vol * 8)
            common.move_vol_multi(m300, reagent=spr, source=spr.reagent_reservoir[spr.col], dest=work_destinations[i],
                                  vol=transfer_vol, x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=rinse, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        common.custom_mix(m300, vhb, location=work_destinations[i], vol=180, rounds=20, blow_out=False, mix_height=0,
                          offset=x_offset_dest)
        m300.move_to(work_destinations[i].top(0))
        m300.air_gap(spr.air_gap_vol_bottom)
        m300.drop_tip()

    # Incubating five minutes with magnet on
    magdeck.engage(height=mag_height)
    ctx.delay(seconds=300, msg='Incubating ON magnet for 300 seconds.')

    # Remove supernatant
    supernatant_trips = math.ceil(spr.reagent_volume / spr.max_volume_allowed)
    supernatant_volume = spr.max_volume_allowed
    supernatant_transfer_vol = []
    for i in range(supernatant_trips):
        supernatant_transfer_vol.append(supernatant_volume + elution.disposal_volume)
    x_offset_rs = 2

    for i in range(num_cols):
        x_offset_source = common.find_side(i) * x_offset_rs
        x_offset_dest = 0
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in supernatant_transfer_vol:
            pickup_height = 1
            common.move_vol_multi(m300, reagent=elution, source=work_destinations[i], dest=waste, vol=transfer_vol,
                                  x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=False, avoid_droplet=False, wait_time=2,
                                  blow_out=False)
        m300.drop_tip()

    # Allow dry
    ctx.delay(seconds=900, msg='Allow dry ON magnet for 900 seconds.')

    # switch off magnet
    magdeck.disengage()

    # Transfer water
    water_trips = math.ceil(water.get('reagent_volume') / water.get('max_volume_allowed'))
    water_volume = water.get('reagent_volume') / water_trips
    water_wash_vol = []
    for i in range(water_trips):
        water_wash_vol.append(water_volume + elution.get('disposal_volume'))
    x_offset_rs = 2.5

    # Water or elution buffer
    for i in range(num_cols):
        x_offset_source = 0
        x_offset_dest = -1 * common.find_side(i) * x_offset_rs
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        for transfer_vol in water_wash_vol:
            pickup_height, change_col = common.calc_height(water, multi_well_rack_area, transfer_vol*8)
            common.move_vol_multi(m300, reagent=water, source=water.get('reagent_reservoir'), dest=work_destinations[i],
                                  vol=transfer_vol, x_offset_source=x_offset_source, x_offset_dest=x_offset_dest,
                                  pickup_height=pickup_height, rinse=False, avoid_droplet=False, wait_time=0,
                                  blow_out=False)
        common.custom_mix(m300, elution, work_destinations[i], vol=40, rounds=20, blow_out=False, mix_height=0,
                          offset=x_offset_dest)
        m300.move_to(work_destinations[i].top(0))
        m300.air_gap(water.air_gap_vol_bottom)
        m300.drop_tip()

    # Wait 10 minutes
    ctx.delay(seconds=600, msg='Allow dry ON magnet for 600 seconds.')

    # Incubating five minutes with magnet on
    magdeck.engage(height=mag_height)
    ctx.delay(seconds=300, msg='Incubating ON magnet for 300 seconds.')

    # Transfer to output deep well
    for s, d in zip(deep_well_plate, destination):
        if not m300.hw_pipette['has_tip']:
            common.pick_up(m300)
        common.move_vol_multichannel(ctx, m300, reagent=sample, source=s, dest=d, vol=sample_volume,
                                     air_gap_vol=air_gap_vol_sample, x_offset=x_offset, pickup_height=1.5,
                                     rinse=sample.get('rinse'), disp_height=-10, blow_out=True, touch_tip=True)
        # Drop pipette tip
        m300.drop_tip()

    # Notify users
    # common.notify_finish_process()
