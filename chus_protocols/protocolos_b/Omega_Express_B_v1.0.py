import math
from opentrons.types import Point, Location
from opentrons import protocol_api
#from opentrons.drivers.rpi_drivers import gpio
import time
import os
import numpy as np
from timeit import default_timer as timer
import json
from datetime import datetime
import csv
#from opentrons import simulate

#ctx = simulate.get_protocol_api('2.4')

metadata = {
    'protocolName': 'S2 Station B Version 4',
    'author': 'Andres Montes, Mario Moncada, Mercedes Perez, Sergio Perez',
    'source': 'Hospital Regional Universitario de Malaga',
    'apiLevel': '2.4',
    'description': 'Protocol for RNA extraction'
}

################################################
# CHANGE THESE VARIABLES ONLY
################################################
NUM_SAMPLES     = 8
sample_volume   = 200   # Sample volume received in station A
set_temp_on     = True # Do you want to start temperature module?
temperature     = 8    # Set temperature. It will be uesed if set_temp_on is set to True
################################################

mag_height = 6 # Height needed for Cobas deepwell in magnetic deck
num_samples_to_show = NUM_SAMPLES
L_deepwell = 8.35 # Deepwell lenght (Cobas deepwell)
multi_well_rack_area = 8 * 71 #Cross section of the 12 well reservoir
deepwell_cross_section_area = L_deepwell ** 2 # deepwell square cross secion area

multi_well_rack_vol = 13000

num_cols = math.ceil(NUM_SAMPLES / 8) # Columns we are working on

NUM_SAMPLES = num_cols * 8

reagent_proportion = sample_volume / 200

def run(ctx: protocol_api.ProtocolContext):

    #Change light to red
    #gpio.set_button_light(1,0,0)

    ctx.comment('Actual used columns: '+str(num_cols))
    STEP = 0
    STEPS = { #Dictionary with STEP activation, description, and times
            1:{'Execute': True, 'description': 'Transfer lysis'},#
            2:{'Execute': True, 'description': 'Wait with magnet OFF', 'wait_time': 600}, #300
            3:{'Execute': True, 'description': 'Incubate wait with magnet ON', 'wait_time': 600}, #300
            4:{'Execute': True, 'description': 'Remove supernatant'},#
            5:{'Execute': True, 'description': 'Switch off magnet'},#
            6:{'Execute': True, 'description': 'Add VHB/WB1'},#
            7:{'Execute': True, 'description': 'Incubate wait with magnet ON', 'wait_time': 600},#300
            8:{'Execute': True, 'description': 'Remove supernatant'},#
            9:{'Execute': True, 'description': 'Switch off magnet'},#
            10:{'Execute': True, 'description': 'Add SPR/WB2'},#
            11:{'Execute': True, 'description': 'Incubate wait with magnet ON', 'wait_time': 600},#300
            12:{'Execute': True, 'description': 'Remove supernatant'},#
            13:{'Execute': True, 'description': 'Switch off magnet'},#
            14:{'Execute': True, 'description': 'Add SPR/WB2'},#
            15:{'Execute': True, 'description': 'Incubate wait with magnet ON', 'wait_time': 600},#300
            16:{'Execute': True, 'description': 'Remove supernatant'},#
            17:{'Execute': True, 'description': 'Allow to dry', 'wait_time': 600},#900
            18:{'Execute': True, 'description': 'Switch off magnet'},#
            19:{'Execute': True, 'description': 'Add water'},#
            20:{'Execute': True, 'description': 'Wait with magnet OFF', 'wait_time': 600},#600
            21:{'Execute': True, 'description': 'Incubate wait with magnet ON', 'wait_time': 600},#300
            22:{'Execute': True, 'description': 'Transfer to final elution plate'},
            }

    """if not ctx.is_simulating():
        folder_path='/data/log_times/'
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        file_path=folder_path+'/time_log.json'"""

    #Define Reagents as objects with their properties
    class Reagent:

        def __init__(self, name, num_samples, aspirate_max_volume_allowed, dead_vol, well_max_vol, reagent_volume, h_cono, v_fondo,  num_channels = 1, flow_rate_aspirate = 1, flow_rate_dispense = 1, flow_rate_aspirate_mix = 1, flow_rate_dispense_mix = 1,
        air_gap_vol_bottom = 0, air_gap_vol_top = 0, disposal_volume = 1, repeat = 1):
            self.name = name
            self.__num_samples = num_samples
            self.num_channels = num_channels
            self.repeat = repeat
            self.flow_rate_aspirate = flow_rate_aspirate
            self.flow_rate_dispense = flow_rate_dispense
            self.flow_rate_aspirate_mix = flow_rate_aspirate_mix
            self.flow_rate_dispense_mix = flow_rate_dispense_mix
            self.air_gap_vol_bottom = air_gap_vol_bottom
            self.air_gap_vol_top = air_gap_vol_top
            self.disposal_volume = disposal_volume
            self.aspirate_max_volume_allowed = aspirate_max_volume_allowed 
            self.reagent_volume = reagent_volume
            self.well_max_vol = well_max_vol
            
            assert (dead_vol >= 0 and dead_vol <= 50), 'dead_vol debe ser un valor [0, 50]'
            self.dead_vol = dead_vol * 0.01 + 1 # Convert to range [1.0, 1.5]
            self.num_wells = math.ceil( (self.__num_samples * self.reagent_volume * self.dead_vol ) * self.repeat / self.well_max_vol)
                
            self.col = 0
            self.vol_well = []
            self.h_cono = h_cono
            self.v_cono = v_fondo
            self.vol_well_original =  self.__calculate_initial_reagent_wellVol()

            
            
        def __calculate_initial_reagent_wellVol (self):
            vol_per_well = []
            columnas = math.ceil(self.__num_samples / self.num_channels)
            vol_col = self.reagent_volume * self.num_channels
            vol_total = self.repeat * (vol_col * columnas * self.dead_vol) # EL volumen para todo un set de muestras se multiplica por el numero de iteraciones
            num_wells = math.ceil((vol_total) / self.well_max_vol)
        
            vol_well = vol_total / num_wells
            vol_well = vol_well - ( vol_well % 100) + 100 # volume is rounded 100 by 100 always upwards. I.E. 9110 ul is 9200ul as well as 9390ul is 9400ul 
            if vol_well > self.well_max_vol:
                vol_well = self.well_max_vol
            # El volumen se reparte de manera equitativa entre todos los pozos, ya que es la mejor forma de aprovechar el volumen
                
            for i in range (num_wells):
                    vol_per_well.append(vol_well)
                
            return vol_per_well
            
            


    #Reagents and their characteristics
    Lysis = Reagent(name = 'Lysis',
                    num_samples = NUM_SAMPLES,
                    num_channels = 8,
                    reagent_volume = 280 * reagent_proportion, # reagent volume needed per sample. 200ul of sample needs 265ul of lysis
                    dead_vol = 10, # 10% dead volume
                    well_max_vol = multi_well_rack_vol,
                    
                    flow_rate_aspirate = 0.5, # Original = 0.5
                    flow_rate_dispense = 0.8, # Original = 1
                    flow_rate_aspirate_mix = 0.7, # Liquid density very high, needs slow aspiration
                    flow_rate_dispense_mix = 2, # Liquid density very high, needs slow dispensation
                    air_gap_vol_bottom = 0,
                    aspirate_max_volume_allowed = 180,
                    
                    h_cono = 1.95,
                    v_fondo = 750 #1.95 * multi_well_rack_area / 2, #Prismatic
                    )

    VHB = Reagent(name = 'VHB',
                    num_samples = NUM_SAMPLES,
                    num_channels = 8,
                    reagent_volume = 350 * reagent_proportion,
                    dead_vol = 7, # 7% dead volume
                    well_max_vol = multi_well_rack_vol,
                    
                    flow_rate_aspirate = 1.5,
                    flow_rate_dispense = 1.5,
                    flow_rate_aspirate_mix = 1.5,
                    flow_rate_dispense_mix = 1.5,
                    air_gap_vol_bottom = 5,
                    aspirate_max_volume_allowed = 180,
                    
                    h_cono = 1.95,
                    v_fondo = 750 #1.95 * multi_well_rack_area / 2, #Prismatic
                    )

    SPR = Reagent(name = 'SPR',
                    num_samples = NUM_SAMPLES,
                    num_channels = 8,
                    reagent_volume = 500 * reagent_proportion,
                    repeat = 2,
                    dead_vol = 15,
                    well_max_vol = multi_well_rack_vol,
                    
                    flow_rate_aspirate = 1, # Original = 1
                    flow_rate_dispense = 1, # Original = 1
                    flow_rate_aspirate_mix = 2,
                    flow_rate_dispense_mix = 2,
                    air_gap_vol_bottom = 5,
                    aspirate_max_volume_allowed = 180,
                    
                    h_cono = 1.95,
                    v_fondo = 750 #1.95 * multi_well_rack_area / 2, #Prismatic
                    )

    Water = Reagent(name = 'Water',
                    num_samples = NUM_SAMPLES,
                    num_channels = 8,
                    reagent_volume = 60,
                    dead_vol = 10,
                    well_max_vol = multi_well_rack_vol,
                    
                    flow_rate_aspirate = 2,
                    flow_rate_dispense = 2,
                    flow_rate_aspirate_mix = 3,
                    flow_rate_dispense_mix = 3,
                    air_gap_vol_bottom = 5,
                    aspirate_max_volume_allowed = 150,

                    h_cono = 1.95,
                    v_fondo = 750) #1.95*multi_well_rack_area/2) #Prismatic

    Elution = Reagent(name = 'Elution',
                    num_samples = NUM_SAMPLES,
                    num_channels = 8,
                    reagent_volume = 50,
                    dead_vol = 10,
                    well_max_vol = multi_well_rack_vol,
                    
                    flow_rate_aspirate = 0.7, # Original 0.5
                    flow_rate_dispense = 1.5, # Original 1
                    flow_rate_aspirate_mix = 0.7,
                    flow_rate_dispense_mix = 1.5,
                    air_gap_vol_bottom = 5,
                    aspirate_max_volume_allowed = 150,
                    
                    h_cono = 4.5,
                    v_fondo = ((4/3) * math.pi * 4.5**3)/2 # Volume of a half sphere (4/3pi* r^3)/2
                    ) 
    #Inicializamos volumenes instantaneos
    Lysis.vol_well      = Lysis.vol_well_original
    VHB.vol_well        = VHB.vol_well_original
    SPR.vol_well        = SPR.vol_well_original
    Water.vol_well      = Water.vol_well_original
    Elution.vol_well    = 350 # Arbitrary value

    ctx.comment(' ')
    ctx.comment('###############################################')
    ctx.comment('Volumenes para ' + str(num_samples_to_show) + ' MUESTRAS')
    ctx.comment(' ')
    
    ctx.comment('Lysis: ' + str(Lysis.num_wells) + ' pozos a partir del 1er pozo en el reservorio 1 con volumenes: ')
    for i in range( len(Lysis.vol_well_original)):
        ctx.comment('     POZO ' + str(i) + ':' + str(Lysis.vol_well_original[i]) + ' uL')
        
    ctx.comment('VHB/WB1: ' + str(VHB.num_wells) + ' pozos a partir del 5º pozo en el reservorio 1 con volumenes: ')
    for i in range( len(VHB.vol_well_original)):
        ctx.comment('     POZO ' + str(i) + ':' + str(VHB.vol_well_original[i]) + ' uL')
        
    ctx.comment('Agua: ' + str(Water.num_wells) + ' pozos a partir del 12º pozo en el reservorio 1 con volumenes: ')
    for i in range( len(Water.vol_well_original)):
        ctx.comment('     POZO ' + str(i) + ':' + str(Water.vol_well_original[i]) + ' uL')
        
    ctx.comment('SPR/WB2: ' + str(SPR.num_wells) + ' pozos a partir del 1er pozo en el reservorio 2 con volumenes ')
    for i in range( len(SPR.vol_well_original)):
        ctx.comment('     POZO ' + str(i) + ':' + str(SPR.vol_well_original[i]) + ' uL')
        
    ctx.comment('###############################################')
    ctx.comment(' ')
    ###################
    #Custom functions

    
    def custom_mix(pipet, reagent, location, vol, rounds, blow_out, mix_height, offset):
        '''
        Function for mix in the same location a certain number of rounds. Blow out optional. Offset
        can set to 0 or a higher/lower value which indicates the lateral movement
        '''
        if mix_height == 0:
            mix_height = 1
        pipet.aspirate(1, location = location.bottom(z = mix_height), rate = reagent.flow_rate_aspirate_mix)
        for _ in range(rounds):
            pipet.aspirate(vol, location = location.bottom(z = mix_height), rate = reagent.flow_rate_aspirate_mix)
            pipet.dispense(vol, location = location.bottom(z = mix_height + 2).move(Point(x = offset)), rate = reagent.flow_rate_dispense_mix)
        pipet.dispense(1, location = location.bottom(z = mix_height + 3), rate = reagent.flow_rate_dispense_mix)
        if blow_out == True:
            pipet.blow_out(location.top(z = -3)) # Blow out

    def calc_height(reagent, cross_section_area, aspirate_volume):
        nonlocal ctx
        ctx.comment('Remaining volume ' + str(reagent.vol_well[reagent.col]) +
                    '< needed volume ' + str(aspirate_volume) + '?')
        if reagent.vol_well[reagent.col] < aspirate_volume:
            ctx.comment('Next column should be picked')
            ctx.comment('Previous to change: ' + str(reagent.col))
            # column selector position; intialize to required number
            reagent.col = reagent.col + 1
            ctx.comment(str('After change: ' + str(reagent.col)))

            ctx.comment('New volume:' + str(reagent.vol_well[reagent.col]))    
    
            col_change = True
        else:
            col_change = False

        height = (( (reagent.vol_well[reagent.col] - aspirate_volume - (reagent.v_cono)) / cross_section_area ) + reagent.h_cono) - 2
        reagent.vol_well[reagent.col] = reagent.vol_well[reagent.col] - aspirate_volume
        ctx.comment('Remaining volume:' + str(reagent.vol_well[reagent.col]))
        ctx.comment('Calculated height is ' + str(height))

        if height < 5:
            height = 1
        ctx.comment('Used height is ' + str(height))
            
            
        return height, col_change

    def move_vol_multi(pipet, reagent, source, dest, vol, x_offset_source, x_offset_dest, pickup_height, wait_time, blow_out,  intermidiate_pos = None):

        # SOURCE
        if reagent.air_gap_vol_top != 0: #If there is air_gap_vol, switch pipette to slow speed
            pipet.move_to(source.top(z = 0))
            pipet.air_gap(reagent.air_gap_vol_top)

        s = source.bottom(pickup_height).move(Point(x = x_offset_source))
        pipet.aspirate(vol + reagent.disposal_volume, s, rate = reagent.flow_rate_aspirate) # aspirate liquid
        
        if wait_time != 0:
                ctx.delay(seconds=wait_time, msg='Waiting for ' + str(wait_time) + ' seconds.')

        if reagent.air_gap_vol_bottom != 0: #If there is air_gap_vol, switch pipette to slow speed
            pipet.move_to(source.top(z = 0))
            pipet.air_gap(reagent.air_gap_vol_bottom)

        if isinstance(intermidiate_pos, Location):
            pipet.move_to(intermidiate_pos)

        # GO TO DESTINATION
        d = dest.top(z = -5).move(Point(x = x_offset_dest))
        pipet.dispense(vol - reagent.disposal_volume + reagent.air_gap_vol_bottom, d, rate = reagent.flow_rate_dispense)

        if wait_time != 0:
            ctx.delay(seconds=wait_time, msg='Waiting for ' + str(wait_time) + ' seconds.')

        if reagent.air_gap_vol_top != 0:
            pipet.dispense(reagent.air_gap_vol_top, dest.top(z = 0), rate = reagent.flow_rate_dispense)

        if blow_out == True:
            pipet.blow_out(dest.top(z = -1))

        if reagent.air_gap_vol_bottom != 0:
            pipet.move_to(dest.top(z = 0))
            pipet.air_gap(reagent.air_gap_vol_bottom)


    ##########
    # pick up tip and if there is none left, prompt user for a new rack
    def pick_up(pip):
        pip.pick_up_tip()

    ##########
    def find_side(col):
        if col%2 == 0:
            side = -1 # left
        else:
            side = 1 # right
        return side
    
    def find_next_tip(rack_list):
        
        if isinstance( rack_list, list):
            
            for tiprack in rack_list:
        
                start_tip = tiprack.next_tip()
                
                if start_tip is not None:
                    break
        else:
            start_tip = rack_list.next_tip()

        return start_tip
    
    def reset_tipWell_OnTipTracker (tip_well_list, channels = 1):
        if isinstance( tip_well_list, list):
            
            for tip_well in tip_well_list:
                working_tip_rack = tip_well.parent
                working_tip_rack.return_tips(tip_well , channels)
        else:
            working_tip_rack = tip_well_list.parent
            working_tip_rack.return_tips(tip_well_list , channels)
    def print_step (step, description):
        ctx.comment(' ')
        ctx.comment('###############################################')
        ctx.comment('Step '+str(step)+': '+description)
        ctx.comment('###############################################')
        ctx.comment(' ')
            
####################################
    # load labware and modules
    ######## 12 well rack
    reagent_res = ctx.load_labware('nest_12_reservoir_15ml', '2','reagent deepwell plate 1')
    reagent_res_2 = ctx.load_labware('nest_12_reservoir_15ml', '3','reagent deepwell plate 2')

############################################
    ########## tempdeck
    tempdeck = ctx.load_module('tempdeck', '1')

##################################
    ####### Elution plate - final plate, goes to C
    elution_plate = tempdeck.load_labware(
        'opentrons_96_aluminumblock_nest_wellplate_100ul',
        'cooled elution plate')

############################################
    ######## Elution plate - comes from A
    magdeck = ctx.load_module('Magnetic Module Gen2', '4')
    # deepwell_plate = magdeck.load_labware('abgene_96_wellplate_800ul', 'NEST 96 Deep Well Plate 2 mL') # Change to NEST deepwell plate
    deepwell_plate = magdeck.load_labware('cobas_96_deepwell_1600', 'Cobas 96 Well Plate 1600 µL') # Change to NEST deepwell plate. cobas_96_deepwell_1600
    magdeck.disengage()

####################################
    ######## Waste reservoir
    waste_reservoir = ctx.load_labware('nest_1_reservoir_195ml', '5', 'waste reservoir') # Change to our waste reservoir
    # waste_reservoir = ctx.load_labware('biotix_1_reservoir_560000ul', '5', 'waste reservoir')
    
####################################
    ######### Load tip_racks
    tips300 = [ctx.load_labware('opentrons_96_tiprack_300ul', slot, '200µl filter tiprack')
        for slot in ['6', '7', '8', '9', '10', '11']]

###############################################################################
    #Declare which reagents are in each reservoir as well as deepwell and elution plate
    Lysis.reagent_reservoir = reagent_res.rows()[0][:4] # 4 columns
    VHB.reagent_reservoir   = reagent_res.rows()[0][4:8] # 4 columns
    SPR.reagent_reservoir   = reagent_res_2.rows()[0][0:8] # 8 columns
    Water.reagent_reservoir = reagent_res.rows()[0][-1]
    work_destinations       = deepwell_plate.rows()[0][:num_cols]
    final_destinations      = elution_plate.rows()[0][:num_cols]
    waste = waste_reservoir.wells()[0] # referenced as reservoir

    # pipettes. P1000 currently deactivated
    m300 = ctx.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300) # Load multi pipette

    #### used tip counter and set maximum tips available
    tip_track = {
        'counts': {m300: 0},
        'maxes': {m300: 96 * len(m300.tip_racks)} #96 tips per tiprack * number or tipracks in the layout
        }

###############################################################################

    ###############################################################################
    # STEP 1 TRANSFER LYSIS
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
    #Transfer lysis
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # aspirate_max_volume_allowed = 160 # Tips allow up to 200uL, but we only allow max_volume_allowed
        lysis_trips = math.ceil(Lysis.reagent_volume / Lysis.aspirate_max_volume_allowed)
        lysis_volume = Lysis.reagent_volume / lysis_trips #136.66
        lysis_transfer_vol = []
        for i in range(lysis_trips):
            lysis_transfer_vol.append(lysis_volume + Lysis.disposal_volume)

        #lysis_transfer_vol = [lysis_volume + Lysis.disposal_volume, lysis_volume + Lysis.disposal_volume, lysis_volume + Lysis.disposal_volume] # Three rounds of 140 + disposal volume
        x_offset_source = 0
        x_offset_dest   = 0
        
        for i in range(num_cols):
            ctx.comment("Column: " + str(i))
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            ctx.comment(' ')
            ctx.comment('Mixing Mag-Bind MaxterMix ')
            rondas_mezcla = 3
            if i == 0:
                rondas_mezcla = 10
            custom_mix (m300, Lysis, location = Lysis.reagent_reservoir[Lysis.col], vol = 150, rounds = rondas_mezcla, blow_out = True, mix_height = 2, offset = 0)
            for j,transfer_vol in enumerate(lysis_transfer_vol):
                #Calculate pickup_height based on remaining volume and shape of container
                [pickup_height, change_col] = calc_height(Lysis, multi_well_rack_area, transfer_vol * 8)

                ctx.comment('Aspirate from reservoir column: ' + str(Lysis.col))
                ctx.comment('Pickup height is ' + str(pickup_height))
                
                inter_pos = waste.top(z = 45).move(Point(x = -43))
                
                move_vol_multi(m300, reagent = Lysis, source = Lysis.reagent_reservoir[Lysis.col],
                               dest = work_destinations[i], vol = transfer_vol, intermidiate_pos = inter_pos, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                               pickup_height = pickup_height, wait_time = 3, blow_out = False)
                # Después de todas las dispensaciones menos la última pasa por el reservorio de vaciado
                if ( j < (lysis_trips - 1) ):
                    m300.move_to(inter_pos)

            ctx.comment(' ')
            ctx.comment('Mixing sample ')
            
            custom_mix(m300, Lysis, location = work_destinations[i], vol = 150,rounds = 3, blow_out = True, mix_height = 1, offset = 0)
            m300.move_to(work_destinations[i].top(0))
            m300.air_gap(Lysis.air_gap_vol_bottom) 
            #Devuelve la punta al tiprack para no saturar la papelera y no pasar por encima de los tipracks
            m300.drop_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8


        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 2 INCUBATING WITHOUT MAGNET OFF
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
    #Transfer magnetic beads
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Incubating for ' + format(STEPS[STEP]['wait_time']) + ' seconds.') # minutes=2
        ctx.comment(' ')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 3 INCUBATE WAIT WITH MAGNET ON
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        magdeck.engage(height=mag_height)
        ctx.comment(' ')
        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Incubating ON magnet for ' + format(STEPS[STEP]['wait_time']) + ' seconds.') # minutes=2
        ctx.comment(' ')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 4 REMOVE SUPERNATANT
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])
        # remove supernatant -> height calculation can be omitted and referred to bottom!

        supernatant_trips = math.ceil((Lysis.reagent_volume + sample_volume) / Lysis.aspirate_max_volume_allowed)
        supernatant_volume = Lysis.aspirate_max_volume_allowed # We try to remove an exceeding amount of supernatant to make sure it is empty

        supernatant_transfer_vol = []
        for i in range(supernatant_trips):
            supernatant_transfer_vol.append(supernatant_volume + Elution.disposal_volume)
        
        x_offset_rs = 0

        for i in range(num_cols):
            x_offset_source = find_side(i) * x_offset_rs
            x_offset_dest   = 0
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
                
            for transfer_vol in supernatant_transfer_vol:
                #Pickup_height is fixed here
                pickup_height = 1 # Original 0.5
                ctx.comment('Aspirate from deep well column: ' + str(i+1))
                ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')
                move_vol_multi(m300, reagent = Elution, source = work_destinations[i],
                               dest = waste, vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                               pickup_height = pickup_height,  wait_time = 2, blow_out = False)
                
            m300.drop_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 5 MAGNET OFF
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch off magnet
        magdeck.disengage()

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 6 VHB/WB1
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        vhb_trips = math.ceil(VHB.reagent_volume / VHB.aspirate_max_volume_allowed)
        vhb_volume = VHB.reagent_volume / vhb_trips #136.66
        vhb_transfer_vol = []
        for i in range(vhb_trips):
            vhb_transfer_vol.append(vhb_volume + VHB.disposal_volume)
   
        x_offset_rs = 2.1
        
        # Lista de reutilizacion de puntas
        reuse_tip_list = []
        # Busco la siguiente punta disponible en todos los tipracks vinculados con la pipeta Multi 300
        reuse_tip_list.append(find_next_tip(m300.tip_racks))


        ########
        # whb washes
        for i in range(num_cols):
            x_offset_source = 0
            x_offset_dest   = -1 * find_side(i) * x_offset_rs
        


            if not m300.hw_pipette['has_tip']:
                
                if i != 0:
                    #Añadimos la siguiente punta que vamos a utilizar a la lista de reutilizacion
                    reuse_tip_list.append(find_next_tip(m300.tip_racks))
                
                pick_up(m300)
                
            for j,transfer_vol in enumerate(vhb_transfer_vol):
                
                #Calculate pickup_height based on remaining volume and shape of container
                [pickup_height, change_col] = calc_height(VHB, multi_well_rack_area, transfer_vol*8)
                ctx.comment('Aspirate from Reservoir column: ' + str(VHB.col))
                ctx.comment('Pickup height is ' + str(pickup_height))
                
                inter_pos = waste.top(z = 45).move(Point(x = -43))
                
                move_vol_multi(m300, reagent = VHB, source = VHB.reagent_reservoir[VHB.col],
                dest = work_destinations[i], vol = transfer_vol, intermidiate_pos = inter_pos, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height, wait_time = 1, blow_out = True)
                
                if ( j < (vhb_trips - 1) ):
                    m300.move_to(inter_pos)

            custom_mix(m300, VHB, location = work_destinations[i], vol = 150,
                rounds = 8, blow_out = True, mix_height = 2, offset = x_offset_dest - 1)
            m300.move_to(work_destinations[i].top(0))
            m300.air_gap(VHB.air_gap_vol_bottom) #air gap
            
            m300.drop_tip(home_after = False)

        end = datetime.now()
        time_taken = (end - start)        
        
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 7 INCUBATE WAIT WITH MAGNET ON
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch on magnet
        magdeck.engage(mag_height)
        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Wait for 5 minutes.')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 8 REMOVE SUPERNATANT
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        supernatant_trips = math.ceil(VHB.reagent_volume / VHB.aspirate_max_volume_allowed)
        supernatant_volume = VHB.aspirate_max_volume_allowed # We try to remove an exceeding amount of supernatant to make sure it is empty

        supernatant_transfer_vol = []
        for i in range(supernatant_trips):
            supernatant_transfer_vol.append(supernatant_volume + Elution.disposal_volume)

        x_offset_rs = 0

        for i in range(num_cols):
            x_offset_source = find_side(i) * x_offset_rs
            x_offset_dest   = 0
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            for transfer_vol in supernatant_transfer_vol:
                #Pickup_height is fixed here
                pickup_height = 0.3# Original 0.5
                ctx.comment('Aspirate from deep well column: ' + str(i+1))
                ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')
                move_vol_multi(m300, reagent = Elution, source = work_destinations[i],
                dest = waste, vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height,  wait_time = 2, blow_out = False)

            m300.return_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 9 MAGNET OFF
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch off magnet
        magdeck.disengage()

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+ str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 10 SPR
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])
        
        spr_trips = math.ceil(SPR.reagent_volume / SPR.aspirate_max_volume_allowed)
        spr_volume = SPR.reagent_volume / spr_trips #136.66
        spr_transfer_vol = []
        for i in range(spr_trips):
            spr_transfer_vol.append(spr_volume + SPR.disposal_volume)
    
        x_offset_rs = 2.25


        # Lista de reutilizacion de puntas
        reuse_tip_list = []
        # Busco la siguiente punta disponible en todos los tipracks vinculados con la pipeta Multi 300
        reuse_tip_list.append(find_next_tip(m300.tip_racks))

        ########
        # spr washes
        for i in range(num_cols):
            x_offset_source = 0
            x_offset_dest   = -1 * find_side(i) * x_offset_rs
            if not m300.hw_pipette['has_tip']:
                if i != 0:
                    #Añadimos la siguiente punta que vamos a utilizar a la lista de reutilizacion
                    reuse_tip_list.append(find_next_tip(m300.tip_racks))
                
                pick_up(m300)
            for j,transfer_vol in enumerate(spr_transfer_vol):
                #Calculate pickup_height based on remaining volume and shape of container
                [pickup_height, change_col] = calc_height(SPR, multi_well_rack_area, transfer_vol*8)
                ctx.comment('Aspirate from Reservoir column: ' + str(SPR.col))
                ctx.comment('Pickup height is ' + str(pickup_height))

                inter_pos = waste.top(z = 40).move(Point(x = -43))
                
                move_vol_multi(m300, reagent = SPR, source = SPR.reagent_reservoir[SPR.col],
                dest = work_destinations[i], vol = transfer_vol, intermidiate_pos = inter_pos, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height, wait_time = 2, blow_out = True)
                
                if ( j < (spr_trips - 1) ):
                    m300.move_to(inter_pos)

            custom_mix(m300, SPR, location = work_destinations[i], vol = 150,
                rounds = 8, blow_out = True, mix_height = 2, offset = x_offset_dest)
            m300.move_to(work_destinations[i].top(0))
            m300.air_gap(SPR.air_gap_vol_bottom) 

            m300.drop_tip(home_after = False)

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 11 INCUBATE WAIT WITH MAGNET ON
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch on magnet
        magdeck.engage(mag_height)
        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Wait for 5 minutes.')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 12 REMOVE SUPERNATANT
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        supernatant_trips = math.ceil(SPR.reagent_volume / SPR.aspirate_max_volume_allowed)
        supernatant_volume = SPR.aspirate_max_volume_allowed # We try to remove an exceeding amount of supernatant to make sure it is empty
        
        supernatant_transfer_vol = []
        for i in range(supernatant_trips):
            supernatant_transfer_vol.append(supernatant_volume + Elution.disposal_volume)
        
        x_offset_rs = 0

        for i in range(num_cols):
            x_offset_source = find_side(i) * x_offset_rs
            x_offset_dest   = 0
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            for transfer_vol in supernatant_transfer_vol:
                #Pickup_height is fixed here
                pickup_height = 0.3 # Original 0.5
                ctx.comment('Aspirate from deep well column: ' + str(i+1))
                ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')
                move_vol_multi(m300, reagent = VHB, source = work_destinations[i],
                                dest = waste, vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                                pickup_height = pickup_height, wait_time = 2, blow_out = False)
                
            m300.return_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 13 MAGNET OFF
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch off magnet
        magdeck.disengage()

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 14 SPR
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        #aspirate_max_volume_allowed = 190
        spr_trips = math.ceil(SPR.reagent_volume / SPR.aspirate_max_volume_allowed)
        spr_volume = SPR.reagent_volume / spr_trips #136.66
        spr_transfer_vol = []
        for i in range(spr_trips):
            spr_transfer_vol.append(spr_volume + SPR.disposal_volume)

        x_offset_rs = 2.1

        # Lista de reutilizacion de puntas
        reuse_tip_list = []
        # Busco la siguiente punta disponible en todos los tipracks vinculados con la pipeta Multi 300
        reuse_tip_list.append(find_next_tip(m300.tip_racks))

        ########
        # spr washes
        for i in range(num_cols):
            x_offset_source = 0
            x_offset_dest   = -1 * find_side(i) * x_offset_rs
            if not m300.hw_pipette['has_tip']:
                if i != 0:
                    #Añadimos la siguiente punta que vamos a utilizar a la lista de reutilizacion
                    reuse_tip_list.append(find_next_tip(m300.tip_racks))
                
                pick_up(m300)
            for j,transfer_vol in enumerate(spr_transfer_vol):
                #Calculate pickup_height based on remaining volume and shape of container
                [pickup_height, change_col] = calc_height(SPR, multi_well_rack_area, transfer_vol*8)
                ctx.comment('Aspirate from Reservoir column: ' + str(SPR.col))
                ctx.comment('Pickup height is ' + str(pickup_height))
                
                inter_pos = waste.top(z = 40).move(Point(x = -43))
                
                move_vol_multi(m300, reagent = SPR, source = SPR.reagent_reservoir[SPR.col],
                dest = work_destinations[i], vol = transfer_vol, intermidiate_pos = inter_pos, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height, wait_time = 2, blow_out = False)
                if ( j < (spr_trips - 1) ):
                    m300.move_to(inter_pos)

            custom_mix(m300, SPR, location = work_destinations[i], vol = 150,
                rounds = 8, blow_out = True, mix_height = 2, offset = x_offset_dest)
            m300.move_to(work_destinations[i].top(0))
            m300.air_gap(SPR.air_gap_vol_bottom)

            m300.drop_tip(home_after = False)

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 15 INCUBATE WAIT WITH MAGNET ON
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch on magnet
        magdeck.engage(mag_height)
        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Wait for 30 seconds.')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 16 REMOVE SUPERNATANT
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # remove supernatant -> height calculation can be omitted and referred to bottom!
        supernatant_trips = math.ceil(SPR.reagent_volume / SPR.aspirate_max_volume_allowed)
        supernatant_volume = SPR.aspirate_max_volume_allowed # We try to remove an exceeding amount of supernatant to make sure it is empty
      
        supernatant_transfer_vol = []
        for i in range(supernatant_trips):
            supernatant_transfer_vol.append(supernatant_volume + Elution.disposal_volume)
  
        x_offset_rs = 0

        for i in range(num_cols):
            x_offset_source = find_side(i) * x_offset_rs
            x_offset_dest   = 0
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            for transfer_vol in supernatant_transfer_vol:
                #Pickup_height is fixed here
                pickup_height = 0.3 # Original 0.5
                ctx.comment('Aspirate from deep well column: ' + str(i+1))
                ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')
                move_vol_multi(m300, reagent = SPR, source = work_destinations[i],
                dest = waste, vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height, wait_time = 3, blow_out = False)

            m300.return_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8
            
        # Extraer líquido del fondo
        for i in range(num_cols):
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
                
            pickup_height = 0.2 # Original 0.5
            ctx.comment('Aspirate from deep well column: ' + str(i+1))
            ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')
            move_vol_multi(m300, reagent = SPR, source = work_destinations[i],
                           dest = waste, vol = SPR.aspirate_max_volume_allowed, x_offset_source = 0, x_offset_dest = 0,
                           pickup_height = pickup_height, wait_time = 2, blow_out = False)
            m300.return_tip()
            tip_track['counts'][m300] += 8
            
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:'] = str(time_taken)
        ctx.comment('Used tips in total: ' + str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 17 ALLOW DRY
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Incubating OFF magnet for ' + format(STEPS[STEP]['wait_time']) + ' seconds.') # minutes=2
        ctx.comment(' ')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:'] = str(time_taken)
        ctx.comment('Used tips in total: ' + str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 18 MAGNET OFF
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch off magnet
        magdeck.disengage()

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:'] = str(time_taken)
        ctx.comment('Used tips in total: ' + str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 19 Transfer water
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        #Water elution
        water_trips = math.ceil(Water.reagent_volume / Water.aspirate_max_volume_allowed)
        water_volume = Water.reagent_volume / water_trips
        water_wash_vol = []
        for i in range(water_trips):
            water_wash_vol.append(water_volume + Elution.disposal_volume)

        x_offset_rs = 2.1
        
        # Lista de reutilizacion de puntas
        reuse_tip_list = []
        # Busco la siguiente punta disponible en todos los tipracks vinculados con la pipeta Multi 300
        reuse_tip_list.append(find_next_tip(m300.tip_racks))
        
        
        ########
        # Water or elution buffer
        for i in range(num_cols):
            x_offset_source = 0
            x_offset_dest   = -1 * find_side(i) * x_offset_rs # Original 0
            if not m300.hw_pipette['has_tip']:
                if i != 0:
                    #Añadimos la siguiente punta que vamos a utilizar a la lista de reutilizacion
                    reuse_tip_list.append(find_next_tip(m300.tip_racks))
                    
                pick_up(m300)
                
            for transfer_vol in water_wash_vol:
                #Calculate pickup_height based on remaining volume and shape of container
                [pickup_height, change_col] = calc_height(Water, multi_well_rack_area, transfer_vol*8)
                ctx.comment('Aspirate from Reservoir column: ' + str(Water.col))
                ctx.comment('Pickup height is ' + str(pickup_height))
                
                #inter_pos = waste.top(z = 40).move(Point(x = -43))
                
                move_vol_multi(m300, reagent = Water, source = Water.reagent_reservoir,
                dest = work_destinations[i], vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height,  wait_time = 0, blow_out = True)

            ctx.comment(' ')
            ctx.comment('Mixing sample with Water')
            #Mixing
            custom_mix(m300, Elution, work_destinations[i], vol = 40, rounds = 8,
            blow_out = True, mix_height = 2, offset = x_offset_dest)
            m300.move_to(work_destinations[i].top(0))
            m300.air_gap(Water.air_gap_vol_bottom)

            m300.drop_tip(home_after = False)

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 20 WAIT FOR 10'
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Wait for ' + format(STEPS[STEP]['wait_time']) + ' seconds.')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 21 INCUBATE WAIT WITH MAGNET ON
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        # switch on magnet
        magdeck.engage(mag_height)
        ctx.delay(seconds=STEPS[STEP]['wait_time'], msg='Wait for 5 minutes.')
        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ###############################################################################
    # STEP 22 TRANSFER TO ELUTION PLATE
    ########
    STEP += 1
    if STEPS[STEP]['Execute']==True:
        start = datetime.now()
        print_step (STEP, STEPS[STEP]['description'])

        elution_trips = math.ceil(Elution.reagent_volume / Elution.aspirate_max_volume_allowed)
        elution_volume = Elution.reagent_volume / elution_trips
        elution_vol = []
        for i in range(elution_trips):
            elution_vol.append(elution_volume + Elution.disposal_volume)

        x_offset_rs = 0
        for i in range(num_cols):
            x_offset_source = find_side(i) * x_offset_rs
            x_offset_dest   = find_side(i) * x_offset_rs
            if not m300.hw_pipette['has_tip']:
                pick_up(m300)
            for transfer_vol in elution_vol:
                #Pickup_height is fixed here
                pickup_height = 0.3
                ctx.comment('Aspirate from deep well column: ' + str(i+1))
                ctx.comment('Pickup height is ' + str(pickup_height) +' (fixed)')

                move_vol_multi(m300, reagent = Elution, source = work_destinations[i],
                dest = final_destinations[i], vol = transfer_vol, x_offset_source = x_offset_source, x_offset_dest = x_offset_dest,
                pickup_height = pickup_height, wait_time = 2, blow_out = True)

            m300.drop_tip(home_after = False)
            #Aumenta la cuenta de puntas usadas
            tip_track['counts'][m300] += 8

        end = datetime.now()
        time_taken = (end - start)
        ctx.comment('Step ' + str(STEP) + ': ' + STEPS[STEP]['description'] + ' took ' + str(time_taken))
        STEPS[STEP]['Time:']=str(time_taken)
        ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))

    ############################################################################
    #       FIN DEL PROTOCOLO
    ############################################################################
    ctx.comment(' ')
    ctx.comment('###############################################')
    ctx.comment('Homing robot')
    ctx.comment('###############################################')
    ctx.comment(' ')
    ctx.home()
    magdeck.disengage()
    if set_temp_on == True:
        tempdeck.set_temperature(temperature)
###############################################################################
    # Light flash end of program
    import os
    #os.system('mpg123 /etc/audio/speaker-test.mp3')
    for i in range(3):
        #gpio.set_rail_lights(False)
        #gpio.set_button_light(1,0,0)
        time.sleep(0.3)
        #gpio.set_rail_lights(True)
        #gpio.set_button_light(0,0,1)
        time.sleep(0.3)
    #gpio.set_button_light(0,1,0)
    ctx.comment('Finished! \nMove deepwell plate (slot 5) to Station C for MMIX addition and PCR preparation.')
    ctx.comment('Used tips in total: '+str(tip_track['counts'][m300]))
    ctx.comment('Used racks in total: '+str(tip_track['counts'][m300]/96))
    ctx.comment('Available tips: '+str(tip_track['maxes'][m300]))

#run(ctx)
