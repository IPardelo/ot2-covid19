import math


# following volumes in ul
def brands(brand_name):
    brands = {
        'seegene': {
           'mastermix': 17,
            'arn': 8
        },
        'thermofisher': {
            'mastermix': 15,
            'arn': 10
        },
        'roche': {
            'mastermix': 10,
            'arn': 10
        },
        'vircell': {
            'mastermix': 15,
            'arn': 5
        }
    }
    mastermix = brands.get(brand_name).get('mastermix')
    arn = brands.get(brand_name).get('arn')
    return mastermix, arn


def tubes(tube_tipe):
    tubes = {
        'falcon': {
            'diameter': 28,
            'hcono': 14         #previously it was: 17.4
        },
        'eppendorf': {
            'diameter': 9,
            'hdisp': -2,
            'hpick': 1.5,
            'hcono': 19
        },
        'criotubo': {
            'diameter': 8,
            'hdisp': 0.5,
            'hpick': 3.5,
            'hcono': 2
        },
        'f_redondo': {
            'diameter': 9,
            'hdisp': -5,
            'hpick': -10,
            'hcono': 3
        }
    }
    diameter = tubes.get(tube_tipe).get('diameter')
    hcono = tubes.get(tube_tipe).get('hcono')
    hdisp = tubes.get(tube_tipe).get('hdisp')
    hpick = tubes.get(tube_tipe).get('hpick')
    #Calculos
    area = (math.pi * diameter**2) / 4

    if tube_tipe == 'falcon':
        vcono = 1 / 3 * hcono * area
        hcono = vcono * 3 / area
    else:
        vcono = 4 * area * diameter * 0.5 / 3
    return area, vcono, hcono, hdisp, hpick


def buffer(buffer_name):
    buffer = {
        'Sample': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 1,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 30000
        },
        'Lisis': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 1,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 30000
        },
        'Roche Cobas': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 1,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 30000
        },
        'UXL Longwood': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 3,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 30000
        },
        'Roche Bleau': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 3,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 30000
        },
    }
    return buffer[buffer_name]
