import time

from opentrons.drivers.rpi_drivers import gpio
from opentrons.types import Point


def move_vol_multichannel(ctx, pipette, reagent, source, dest, vol, air_gap_vol, x_offset, pickup_height, disp_height,
                          blow_out, touch_tip):
    """

    :param ctx: yes
    :param pipette: labware object for pipette
    :param reagent: parameters for this specific reagent
    :param source: list of labware objects from which the reagent is picked
    :param dest: list labware objects to where the reagent is dispensed
    :param vol: volume of reagent to move from each source to each dest
    :param air_gap_vol: volume of air to pick after aspirate
    :param x_offset: 2 positions in x axis for the pippete: pos 0 to aspirate, pos 1 to dispense
    :param pickup_height: height for the pipette to aspirate
    :param disp_height: height for the pipette to dispense
    :param blow_out: if True they will be done after dispensing
    :param touch_tip: if True they will be done after dispensing

    :return:
    """
    # Rinse before aspirating
    rinse = reagent.get('rinse')
    if rinse:
        custom_mix(pipette, reagent, location=source, vol=vol, rounds=rinse, blow_out=True, mix_height=0, x_offset=x_offset)
    # Source
    s = source.bottom(pickup_height).move(Point(x=x_offset[0]))
    pipette.aspirate(vol, s, rate=1.2)
    # If there is air_gap_vol, switch pipette to slow speed
    if air_gap_vol != 0:
        pipette.aspirate(air_gap_vol, source.top(z=-2), rate=reagent.get('flow_rate_aspirate'))
    # Apply a delay, if there is any
    delay = reagent.get('delay')
    if delay:
        ctx.delay(seconds=delay)
    # Go to destination
    drop = dest.top(z=disp_height).move(Point(x=x_offset[1]))
    pipette.dispense(vol + air_gap_vol, drop, rate=reagent.get('flow_rate_dispense'))

    if blow_out:
        pipette.blow_out(dest.top(z=-2))
    if touch_tip:
        pipette.touch_tip(speed=20, v_offset=-5)


def custom_mix(pipette, reagent, location, vol, rounds, blow_out, mix_height, x_offset, source_height=3):
    """
    Function for mixing a given [vol] in the same [location] a x number of [rounds].

    :param pipette:
    :param reagent:
    :param location:
    :param vol:
    :param rounds:
    :param blow_out: Blow out optional [True,False]
    :param x_offset: [source, destination]
    :param source_height: height from bottom to aspirate
    :param mix_height: height from bottom to dispense

    :return:
    """
    mix_height = 3 if mix_height == 0 else mix_height
    pipette.aspirate(1, location=location.bottom(z=source_height).move(Point(x=x_offset[0])), rate=reagent.get('flow_rate_aspirate'))

    for _ in range(rounds):
        pipette.aspirate(vol, location=location.bottom(z=source_height).move(Point(x=x_offset[0])), rate=reagent.get('flow_rate_aspirate'))
        pipette.dispense(vol, location=location.bottom(z=mix_height).move(Point(x=x_offset[1])), rate=reagent.get('flow_rate_dispense'))
    pipette.dispense(1, location=location.bottom(z=mix_height).move(Point(x=x_offset[1])), rate=reagent.get('flow_rate_dispense'))

    if blow_out:
        pipette.blow_out(location.top(z=-2))


def calc_height(ctx, reagent, tube_physical_description, cross_section_area, aspirate_volume, min_height=0.5):
    """
    Calculate pickup_height based on remaining volume and shape of container

    :param reagent:
    :param tube_physical_description:
    :param cross_section_area:
    :param aspirate_volume:
    :param min_height:

    :return:
    """
    if not(reagent.get('vol_well_original')):
        reagent['vol_well_original'] = reagent.get('vol_well')
    if not (reagent.get('unused')):
        reagent['unused'] = []
    if not (reagent.get('col')):
        reagent['col'] = 0
    if reagent.get('vol_well') < aspirate_volume:
        reagent.get('unused').append(reagent.get('vol_well'))
        reagent['col'] = reagent.get('col') + 1
        reagent['vol_well'] = reagent.get('vol_well_original')
        height = (reagent.get('vol_well') - aspirate_volume - tube_physical_description.get('v_cono')) / cross_section_area
        reagent['vol_well'] = reagent.get('vol_well') - aspirate_volume
        if height < min_height:
            height = min_height
        col_change = True
    else:
        height = (reagent.get('vol_well') - aspirate_volume - tube_physical_description.get('v_cono')) / cross_section_area
        reagent['vol_well'] = reagent.get('vol_well') - aspirate_volume
        if height < min_height:
            height = min_height
        col_change = False
    return height, col_change


def generate_source_table(source):
    """
    Concatenate the wells from the different origin racks
    """
    for rack_number in range(len(source)):
        s = source[rack_number].wells() if rack_number == 0 else s + source[rack_number].wells()
    return s


def pick_up(pip):
    pip.pick_up_tip()


def notify_finish_process():
    for i in range(3):
        gpio.set_rail_lights(False)
        gpio.set_button_light(1, 0, 0)
        time.sleep(0.3)
        gpio.set_rail_lights(True)
        gpio.set_button_light(0, 0, 1)
        time.sleep(0.3)
    gpio.set_button_light(0, 1, 0)
