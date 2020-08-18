import math


# following volumes in ul
def brands(brand_name):
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
    mastermix = brands.get(brand_name).get('master_mix')
    arn = brands.get(brand_name).get('arn')
    requires_double_master_mix = brands.get(brand_name).get('split_pcr')
    return mastermix, arn, requires_double_master_mix


def tubes(tube_tipe):
    tubes = {
        'falcon': {
            'diameter': 28,
            'hcono': 14         #previously it was: 174
        },
        'eppendorf': {          #alias magcore
            'diameter': 9,
            'hdisp': -2,
            'hpick': 20,        #previously it was: 35
            'hcono': 19
        },
        'labturbo': {
            'diameter': 8,
            'hdisp': -2,
            'hpick': 10,
            'hcono': 6
        },
        'criotubo': {           #alias magnapure
            'diameter': 8,
            'hdisp': 5,
            'hpick': 10,
            'hcono': 2
        },
        'criotubo_conico': {
            'diameter': 8,
            'hdisp': 0.5,
            'hpick': 15,
            'hcono': 2
        },
        'serologia': {
            'diameter': 14,
            'hdisp': 0.5,
            'hpick': 56,        #tube height = 98
            'hcono': 2
        },
        'f_redondo': {
            'diameter': 9,
            'hdisp': -5,
            'hpick': 15,
            'hcono': 3
        },
        'f_redondo2': {         #alias alipota
            'diameter': 10,
            'hdisp': -5,
            'hpick': 15,
            'hcono': 3
        }
    }
    diameter = tubes.get(tube_tipe).get('diameter')
    hcono = tubes.get(tube_tipe).get('hcono')
    hdisp = tubes.get(tube_tipe).get('hdisp')
    hpick = tubes.get(tube_tipe).get('hpick')
    #Calculos
    area = (math.pi * diameter**2) / 4

    if tube_tipe == 'falcon' or tube_tipe == 'labturbo':
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
            'vol_well': 45000
        },
        'Lisis': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 1,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 45000
        },
        'Roche Cobas': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 1,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 45000
        },
        'UXL Longwood': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 3,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 45000
        },
        'Roche Bleau': {
            'flow_rate_aspirate': 1,  # multiplier
            'flow_rate_dispense': 1,  # multiplier
            'delay': 3,  # delay after aspirate: to allow drops to fall before moving the pipette
            'vol_well': 45000
        },
    }
    return buffer[buffer_name]
