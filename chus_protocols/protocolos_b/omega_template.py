""" Short description of this Python module.

Longer description of this module.

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
You should have received a copy of the GNU General Public License along with
this program. If not, see <http://www.gnu.org/licenses/>.
"""

__authors__ = ["Jon Sicilia","Alicia Arévalo","Luis Torrico", "Alejandro André", "Aitor Gastaminza", "Alex Gasulla", "Sara Monzon" , "Miguel Julian", "Eva González" , "José Luis Villanueva", "Angel Menendez Vazquez", "Nick"]
__contact__ = "luis.torrico@covidrobots.org"
__copyright__ = "Copyright 2020, CovidRobots"
__date__ = "2020/06/01"
__license__ = "GPLv3"
__version__ = "1.0.0"



# #####################################################
# Imports
# #####################################################
from opentrons import protocol_api
from opentrons.types import Point, Location
import time
import math
import os
import subprocess
import json
import itertools
from timeit import default_timer as timer
from datetime import datetime
import csv


# #####################################################
# Metadata
# #####################################################
metadata = {
    'protocolName': 'Nextera DNA Flex NGS Library Prep: Cleanup Libraries',
    'author': 'Luis Torrico (luis.torrico@covidrobots.org), Alejandro Andre (alejandro.andre@covidrobots.org)',
    'source': 'Hospital Gregorio Marañon',
    'apiLevel': '2.4',
    'description': ''
}

# #####################################################
# Protocol parameters
# #####################################################
NUM_SAMPLES = 8
RESET_TIPCOUNT = True
PROTOCOL_ID = "GM"
recycle_tip = False # Do you want to recycle tips? It shoud only be set True for testing
photosensitivity = False
# End Parameters to adapt the protocol

#Defined variables
##################
## global vars
## initialize robot object
robot = None
# default var for drop tip switching
switch = True
# initialize tip_log dictionary
tip_log = {}
tip_log['count'] = {}
tip_log['tips'] = {}
tip_log['max'] = {}
tip_log['used'] = {}


### Formulas info ###
'''
Where V : volume ; B: Area of base ; h : Height; r : Radius ; d : Diameter; A = Area

### General ###

V = B * h

h = V / B

### Circular Cylinder ###

V = math.pi * r**2 * h

V = math.pi * d**2 * h / 4


### For hemispheres ###

h = r

r = d / 2

V = 2 * math.pi * r**3 / 3

V = math.pi * d**3 / 12

### For Cones ###

V = math.pi * r**2 * h / 3

h = 3 * V / (math.pi * r**2)

V = math.pi * d**2 * h / 12

h = 12 * V / (math.pi * d**2)

### Area of a circle ###

A = math.pi * r**2

A = math.pi * d**2 / 4

'''
### End formulas info ###

# #####################################################
# Common classes
# #####################################################
class Tube:

    """Summary

    Attributes:
        actual_volume (TYPE): Description
        base_type (TYPE): Description
        diameter (TYPE): Description
        height (TYPE): Description
        height_base (TYPE): Description
        max_volume (TYPE): Description
        name (TYPE): Description
        volume_base (TYPE): Description
    """

    def __init__(self, name, max_volume, actual_volume, diameter,
                 base_type, height_base, min_height=0.5, reservoir = False):
        """Summary

        Args:
            name (String): Description
            max_volume (float): Description
            actual_volume (float): Description
            diameter (float): Description
            base_type (integer): 1 => Base type U (Hemisphere), 2 => Base type V (Cone), 3 => Base type flat (|_|)
            height_base (float): Description
        """
        self._name = name
        self._max_volume = max_volume
        self._actual_volume = actual_volume
        self._diameter = diameter
        self._base_type = base_type
        self._height_base = height_base
        self._min_height = min_height
        self._reservoir = reservoir

        if base_type == 1:
            self._volume_base = (math.pi * diameter**3) / 12
            self._height_base = diameter / 2
        elif base_type == 2:
            self._volume_base = (math.pi * diameter**2 * height_base) / 12
        else:
            self._volume_base = 0
            self._height_base = 0

    @property
    def reservoir(self):
        return self._reservoir

    @property
    def actual_volume(self):
        return self._actual_volume

    @actual_volume.setter
    def actual_volume(self, value):
        self._actual_volume = value

    def calc_height(self, aspirate_volume):
        volume_cylinder = self._actual_volume - self._volume_base
        if volume_cylinder <= aspirate_volume:
            height = self._min_height
        else:
            cross_section_area = (math.pi * self._diameter**2) / 4
            height = ((self._actual_volume - aspirate_volume - self._volume_base) / cross_section_area) + self._height_base
            if height < self._min_height:
                height = self._min_height

        return height


class Reagent:
    def __init__(self, name, flow_rate_aspirate, flow_rate_dispense,
        flow_rate_aspirate_mix, flow_rate_dispense_mix, delay_aspirate=0,
        delay_dispense = 0, touch_tip_aspirate_speed = 20,
        touch_tip_dispense_speed = 20):
        self._name = name
        self._flow_rate_aspirate = flow_rate_aspirate
        self._flow_rate_dispense = flow_rate_dispense
        self._flow_rate_blow_out = flow_rate_dispense
        self._flow_rate_aspirate_mix = flow_rate_aspirate_mix
        self._flow_rate_dispense_mix = flow_rate_dispense_mix
        self._delay_aspirate = delay_aspirate
        self._delay_dispense = delay_dispense
        self._touch_tip_aspirate_speed = touch_tip_aspirate_speed
        self._touch_tip_dispense_speed = touch_tip_dispense_speed

    @property
    def flow_rate_aspirate(self):
        return self._flow_rate_aspirate

    @property
    def flow_rate_dispense(self):
        return self._flow_rate_dispense

    @property
    def flow_rate_blow_out(self):
        return self._flow_rate_blow_out

    @property
    def flow_rate_aspirate_mix(self):
        return self._flow_rate_dispense_mix

    @property
    def flow_rate_dispense_mix(self):
        return self._flow_rate_dispense_mix

    @property
    def delay_aspirate(self):
        return self._delay_aspirate

    @property
    def delay_dispense(self):
        return self._delay_dispense

    @property
    def touch_tip_aspirate_speed(self):
        return self._touch_tip_aspirate_speed

    @property
    def touch_tip_dispense_speed(self):
        return self._touch_tip_dispense_speed




# Constants
TEXT_NOTIFICATIONS_DICT = {
    'start': f"Started process",
    'finish': f"Finished process",
    'close_door': f"Close the door",
    'replace_tipracks': f"Replace tipracks",
}



# #####################################################
# Global functions
# #####################################################
def notification(action):
    if not robot.is_simulating():
        robot.comment(TEXT_NOTIFICATIONS_DICT[action])

def check_door():
    if 'CLOSED' in str(robot._hw_manager.hardware.door_state):
        return True
    else:
        return False

def confirm_door_is_closed():
    if not robot.is_simulating():
        #Check if door is opened
        if check_door() == False:
            #Set light color to red and pause
            robot._hw_manager.hardware.set_lights(button = True, rails =  False)
            robot.pause()
            notification('close_door')
            time.sleep(5)
            confirm_door_is_closed()
        else:
            if photosensitivity==False:
                robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            else:
                robot._hw_manager.hardware.set_lights(button = True, rails =  False)

def start_run():
    notification('start')
    if photosensitivity==False:
        robot._hw_manager.hardware.set_lights(button = True, rails =  True)
    else:
        robot._hw_manager.hardware.set_lights(button = True, rails =  False)
    now = datetime.now()
    # dd/mm/YY H:M:S
    start_time = now.strftime("%Y/%m/%d %H:%M:%S")
    return start_time

def finish_run():
    notification('finish')
    #Set light color to blue
    robot._hw_manager.hardware.set_lights(button = True, rails =  False)
    now = datetime.now()
    # dd/mm/YY H:M:S
    finish_time = now.strftime("%Y/%m/%d %H:%M:%S")
    if photosensitivity==False:
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            time.sleep(0.3)
    else:
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  False)
            time.sleep(0.3)
    return finish_time

def reset_tipcount(file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    if os.path.isfile(file_path):
        os.remove(file_path)

def retrieve_tip_info(pip,tipracks,file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    global tip_log
    if not tip_log['count'] or pip not in tip_log['count']:
        tip_log['count'][pip] = 0
        if not robot.is_simulating():
            folder_path = os.path.dirname(file_path)
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            if os.path.isfile(file_path):
                with open(file_path) as json_file:
                    data = json.load(json_file)
                    if "P1000" in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips1000' in data.keys() else data['tips1000']
                    elif 'P300' in str(pip) and 'Single-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips300' in data.keys() else data['tips300']
                    elif 'P300' in str(pip) and '8-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tipsm300' in data.keys() else data['tipsm300']
                    elif 'P20' in str(pip) and 'Single-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tips20' in data.keys() else data['tips20']
                    elif 'P20' in str(pip) and '8-Channel' in str(pip):
                        tip_log['count'][pip] = 0 if not 'tipsm20' in data.keys() else data['tipsm20']
        if "8-Channel" in str(pip):
            tip_log['tips'][pip] =  [tip for rack in tipracks for tip in rack.rows()[0]]
        else:
            tip_log['tips'][pip] = [tip for rack in tipracks for tip in rack.wells()]

        tip_log['max'][pip] = len(tip_log['tips'][pip])

    if not tip_log['used'] or pip not in tip_log['used']:
        tip_log['used'][pip] = 0

    return tip_log


def save_tip_info(file_path = '/data/' + PROTOCOL_ID + '/tip_log.json'):
    data = {}
    if not robot.is_simulating():
        if os.path.isfile(file_path):
            with open(file_path) as json_file:
                data = json.load(json_file)
            os.rename(file_path,file_path + ".bak")
        for pip in tip_log['count']:
            if "P1000" in str(pip):
                data['tips1000'] = tip_log['count'][pip]
            elif 'P300' in str(pip) and 'Single-Channel' in str(pip):
                data['tips300'] = tip_log['count'][pip]
            elif 'P300' in str(pip) and '8-Channel' in str(pip):
                data['tipsm300'] = tip_log['count'][pip]
            elif 'P20' in str(pip) and 'Single-Channel' in str(pip):
                data['tips20'] = tip_log['count'][pip]
            elif 'P20' in str(pip) and '8-Channel' in str(pip):
                data['tipsm20'] = tip_log['count'][pip]

        with open(file_path, 'a+') as outfile:
            json.dump(data, outfile)


def pick_up(pip,tiprack):
    ## retrieve tip_log
    global tip_log
    if not tip_log:
        tip_log = {}
    tip_log = retrieve_tip_info(pip,tiprack)
    if tip_log['count'][pip] == tip_log['max'][pip]:
        notification('replace_tipracks')
        robot.pause('Replace ' + str(pip.max_volume) + 'µl tipracks before \
resuming.')
        confirm_door_is_closed()
        pip.reset_tipracks()
        tip_log['count'][pip] = 0
    pip.pick_up_tip(tip_log['tips'][pip][tip_log['count'][pip]])
    # Optional only to prevente cacelations
    # save_tip_info()
    tip_log['count'][pip] += 1
    if "8-Channel" not in str(pip):
        tip_log['used'][pip] += 1
    else:
        tip_log['used'][pip] += 8


def drop(pip):
    global switch
    if recycle_tip:
        pip.return_tip()
    else:
        if "8-Channel" not in str(pip):
            side = 1 if switch else -1
            drop_loc = robot.loaded_labwares[12].wells()[0].top().move(Point(x=side*20))
            pip.drop_tip(drop_loc,home_after=False)
            switch = not switch
        else:
            drop_loc = robot.loaded_labwares[12].wells()[0].top().move(Point(x=20))
            pip.drop_tip(drop_loc,home_after=False)


# Function definitions
## General purposes
def divide_volume(volume,max_vol):
    num_transfers=math.ceil(volume/max_vol)
    vol_roundup=math.ceil(volume/num_transfers)
    last_vol=volume-vol_roundup*(num_transfers-1)
    vol_list=[vol_roundup for v in range(1,num_transfers)]
    vol_list.append(last_vol)
    return vol_list


def divide_destinations(l, n):
    # Divide the list of destinations in size n lists.
    for i in range(0, len(l), n):
        yield l[i:i + n]


# Function definitions
## Expecific for liquids
def custom_mix(pip, reagent, repetitions, volume, location, mix_height = 3,
    source_height = 3):
    '''
    Function for mixing a given volume in the same location a x number of repetitions.
    source_height: height from bottom to aspirate
    mix_height: height from bottom to dispense
    '''
    if mix_height == 0:
        mix_height = 3

    pip.aspirate(volume = 1,
                 location = location.bottom(z=source_height),
                 rate = reagent.flow_rate_aspirate_mix)
    for _ in range(repetitions):
        pip.aspirate(volume = volume,
                    location = location.bottom(z=source_height),
                    rate = reagent.flow_rate_aspirate_mix)
        pip.dispense(volume = volume,
                    location = location.bottom(z=mix_height),
                    rate=reagent.flow_rate_dispense)
    pip.dispense(volume = 1,
        location = location.bottom(z=mix_height),
            rate=reagent.flow_rate_dispense)


def distribute_custom(pip, reagent, tube_type, volume, src, dest, max_volume=0,
    extra_dispensal=0, disp_height=0, touch_tip_aspirate=False,
    touch_tip_dispense = False):

    if max_volume == 0:
        max_volume = pip.max_volume

    if len(dest) > 1 or max_volume < (volume + extra_dispensal):
        max_trans_per_asp = (max_volume - extra_dispensal) // volume
    else:
        max_trans_per_asp = 1

    actual_blow_rate = pip.flow_rate.blow_out
    pip.flow_rate.blow_out = reagent.flow_rate_blow_out

    if max_trans_per_asp != 0:

        volume_per_asp = (max_trans_per_asp * volume) + extra_dispensal

        list_dest = list(divide_destinations(dest,max_trans_per_asp))

        for i in range(len(list_dest)):
            pickup_height = tube_type.calc_height(volume_per_asp)

            if tube_type.reservoir:
                tube_type.actual_volume -= (max_trans_per_asp * volume * 8)
            else:
                tube_type.actual_volume -= (max_trans_per_asp * volume)

            pip.aspirate(volume=volume_per_asp,
                        location=src.bottom(pickup_height),
                        rate=reagent.flow_rate_aspirate)

            robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent

            if touch_tip_aspirate:
                    pip.touch_tip(radius=1.0,v_offset=-5,speed=reagent.touch_tip_aspirate_speed)

            for d in list_dest[i]:

                pip.dispense(volume=volume,
                            location=d.bottom(disp_height),
                            rate=reagent.flow_rate_dispense)

                robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent

                if touch_tip_dispense:
                    pip.touch_tip(radius=1.0,v_offset=-5,speed=reagent.touch_tip_dispense_speed)

            if extra_dispensal != 0:
                pip.blow_out(location=src.top())

        pip.flow_rate.blow_out = actual_blow_rate

    else:

        list_vol_per_well = divide_volume(volume,(max_volume - extra_dispensal))

        list_dest = dest

        for d in list_dest:

            for vol in list_vol_per_well:

                volume_per_asp = vol + extra_dispensal

                pickup_height = tube_type.calc_height(volume_per_asp)

                if tube_type.reservoir:
                    tube_type.actual_volume -= (vol * 8)
                else:
                    tube_type.actual_volume -= vol

                pip.aspirate(volume=volume_per_asp,
                            location=src.bottom(pickup_height),
                            rate=reagent.flow_rate_aspirate)

                robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent

                if touch_tip_aspirate:
                    pip.touch_tip(radius=1.0,v_offset=-5,speed=reagent.touch_tip_aspirate_speed)

                pip.dispense(volume=vol,
                            location=d.bottom(disp_height),
                            rate=reagent.flow_rate_dispense)

                robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent

                if touch_tip_dispense:
                    pip.touch_tip(radius=1.0,v_offset=-5,speed=reagent.touch_tip_dispense_speed)

                if extra_dispensal != 0:
                    pip.blow_out(location=src.top())

        pip.flow_rate.blow_out = actual_blow_rate


def find_side(col):
    if col%2 == 0:
        side = -1 # left
    else:
        side = 1 # right
    return side


def remove_supernatant(pip, reagent, tube_type, volume, src,
    dest, x_offset_src, max_volume=0, pickup_height=0.5, x_offset_dest=0,
    disp_height=0):

    if max_volume == 0:
        max_volume = pip.max_volume

    s = src.bottom(pickup_height).move(Point(x = x_offset_src))

    d = dest.bottom(disp_height).move(Point(x = x_offset_dest))

    list_vol_per_round = divide_volume(volume,max_volume)

    actual_blow_rate = pip.flow_rate.blow_out
    pip.flow_rate.blow_out = reagent.flow_rate_blow_out

    for vol in list_vol_per_round:

        #pickup_height = tube_type.calc_height(volume_per_asp)

        if tube_type.reservoir:
            tube_type.actual_volume -= (vol * 8)
        else:
            tube_type.actual_volume -= vol

        pip.aspirate(volume=vol,
                    location=s,
                    rate=reagent.flow_rate_aspirate)

        robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent

        pip.dispense(volume=vol,
                    location=d,
                    rate=reagent.flow_rate_dispense)

        pip.blow_out()

        robot.delay(seconds = reagent.delay_dispense) # pause for x seconds depending on reagent

def remove_supernatant_and_drop(pip, reagent, tube_type, volume, src, 
    x_offset_src, pickup_height=0.5):

    s = src.bottom(pickup_height).move(Point(x = x_offset_src))

    actual_blow_rate = pip.flow_rate.blow_out
    pip.flow_rate.blow_out = reagent.flow_rate_blow_out

    if tube_type.reservoir:
        tube_type.actual_volume -= (volume * 8)
    else:
        tube_type.actual_volume -= volume

    pip.aspirate(volume=volume, 
                location=s,
                rate=reagent.flow_rate_aspirate)
    
    robot.delay(seconds = reagent.delay_aspirate) # pause for x seconds depending on reagent
    
    drop(pip)


# #####################################################
# Protocol start
# #####################################################
def run(ctx: protocol_api.ProtocolContext):

    # Initial data
    global robot
    global tip_log

    # Set robot as global var
    robot = ctx

    # check if tipcount is being reset
    if RESET_TIPCOUNT:
        reset_tipcount()


    # confirm door is close
    if not robot.is_simulating():
        # confirm door is close
        robot.comment(f"Please, close the door")
        confirm_door_is_closed()

        start = start_run()


    # #####################################################
    # Common functions
    # #####################################################
    
    # -----------------------------------------------------
    # Execute step
    # -----------------------------------------------------
    def run_step(step):

        robot.comment(' ')
        robot.comment('###############################################')
        robot.comment('Step ' + str(step) + ': ' + STEPS[step]['Description'])
        robot.comment('===============================================')

        # Execute step?
        if STEPS[step]['Execute']:

            # Execute function step
            STEPS[step]['Function']()

            # Wait
            if STEPS[step].get('wait_time'):
                robot.comment('===============================================')
                wait = STEPS[step]['wait_time']
                robot.delay(seconds = wait)

        # Dont execute step
        else:
            robot.comment('No ejecutado')

        # End
        robot.comment('###############################################')
        robot.comment(' ')

    # #####################################################
    # 1. Start defining deck
    # #####################################################
    
    # Labware
    # Positions are:
    # 10    11      TRASH
    # 7     8       9
    # 4     5       6
    # 1     2       3
    
    # -----------------------------------------------------
    # Tips
    # -----------------------------------------------------
    tips300 = [robot.load_labware('opentrons_96_filtertiprack_200ul', slot)
        for slot in ['2', '3', '6','7','8','9','10','11']
    ]

    # -----------------------------------------------------
    # Pipettes
    # -----------------------------------------------------
    m300 = robot.load_instrument('p300_multi_gen2', 'left', tip_racks=tips300)

    # -----------------------------------------------------
    # Magnetic module + labware
    # -----------------------------------------------------
    # magdeck = robot.load_module('Magnetic Module Gen2', '4')
    magdeck = robot.load_module('magdeck', '4')
    magnet_rack = magdeck.load_labware('nest_96_wellplate_2000ul', 'nest_96_wellplate_2000ul')
    magdeck.disengage()

    # -----------------------------------------------------
    # Initial labware
    # -----------------------------------------------------
    
    # FPCR plate
    result_rack = robot.load_labware('nest_96_wellplate_2000ul', '1', 'nest_96_wellplate_2000ul')

    # Reagents plate
    reagents_rack = robot.load_labware('nest_12_reservoir_15ml', '5', 'nest_12_reservoir_15ml')

    # -----------------------------------------------------
    # Reagents
    # -----------------------------------------------------

    # SPB
    spb_reagent = Reagent(name = 'SPB',
                    flow_rate_aspirate = 600,
                    flow_rate_dispense = 1000,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix = 1000)

    # RSB
    rsb_reagent = Reagent(name = 'RSB',
                    flow_rate_aspirate = 600,
                    flow_rate_dispense = 1000,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix = 1000)

    # Ethanol
    eth_reagent = Reagent(name = 'Ethanol',
                    flow_rate_aspirate = 600,
                    flow_rate_dispense = 1000,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix = 1000)

    # FPCR
    fpcr_reagent = Reagent(name = 'FPCR',
                    flow_rate_aspirate = 600,
                    flow_rate_dispense = 1000,
                    flow_rate_aspirate_mix = 600,
                    flow_rate_dispense_mix = 1000)
    
   
                
    # -----------------------------------------------------
    # Tubes
    # -----------------------------------------------------
   
    # SPB
    spb_tube = Tube(name = 'nest_12_reservoir_15ml',
                actual_volume = 14000, 
                max_volume = 15000, 
                diameter = 26.68, 
                base_type = 3,
                height_base = 0,
                reservoir = True)
    
    # RSB
    rsb_tube = Tube(name = 'nest_12_reservoir_15ml',
                actual_volume = 12000, 
                max_volume = 15000, 
                diameter = 26.68, 
                base_type = 3,
                height_base = 0,
                reservoir = True)
    
    # ETHANOL
    eth_tube = Tube(name = 'reservoir 15ml plate',
                actual_volume = 14000, 
                max_volume = 15000, 
                diameter = 26.68, 
                base_type = 3,
                height_base = 0,
                reservoir = True)

    # FPCR
    fpcr_tube = Tube(name = 'nest_96_wellplate_2000ul',
                actual_volume = 200,
                max_volume = 2000,
                diameter = 8.7, 
                base_type = 2,
                height_base = 1,
                min_height = 0.1)

    spb_src = reagents_rack.columns()[0:1]
    
    rsb_src = reagents_rack.columns()[2:4]   
    
    eth_src = reagents_rack.columns()[6:11]

    c_eth = 0           # Current ethanol channel
    v_eth = 14000       # Current channel ethanol volume

    c_spb = 0           # Current spb channel
    v_spb = 14000       # Current channel spb volume

    c_rsb = 0           # Current rsb channel
    v_rsb = 12000       # Current channel rsb volume    

    x_offset_rs = 2

    # #####################################################
    # 2. Steps definition
    # #####################################################

    # -----------------------------------------------------
    # Activar el módulo magnético
    # -----------------------------------------------------
    def magnet_on():
        magdeck.engage(height = 10.5)

    # -----------------------------------------------------
    # Desactivar el módulo magnético
    # -----------------------------------------------------
    def magnet_off():
        magdeck.disengage()
        
    # -----------------------------------------------------
    # Void
    # -----------------------------------------------------
    def wait():
        pass
  
    # -----------------------------------------------------
    # Pausa para intercambiar placas
    # -----------------------------------------------------
    def pause():
        for i in range(3):
            robot._hw_manager.hardware.set_lights(button = False, rails =  False)
            time.sleep(0.3)
            robot._hw_manager.hardware.set_lights(button = True, rails =  True)
            time.sleep(0.3)
        robot.pause('Cambia placas')
        
    # -----------------------------------------------------
    # Transfer SPB and mix
    # -----------------------------------------------------
    def xfer_and_mix_spb():

        nonlocal c_spb
        nonlocal v_spb 

        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            # New tips
            if not m300.hw_pipette['has_tip']:
                pick_up(m300, tips300)

            # Destination MIDI plate
            dest_wells = [magnet_rack.columns()[i][0]]

            # Dispense 81 ul of SPB
            distribute_custom(pip = m300,
                        reagent = spb_reagent,
                        tube_type = spb_tube,
                        volume = 140,
                        src = spb_src[c_spb][0],
                        dest = dest_wells,
                        max_volume = 140,
                        extra_dispensal = 0,
                        touch_tip_aspirate = False,
                        touch_tip_dispense = False)

            # Mix
            custom_mix(pip = m300,
                    reagent = spb_reagent,
                    repetitions = 10,
                    volume = 100,
                    location = dest_wells[0],
                    mix_height = 1,
                    source_height = 1)
			    
            # spb remaining volume
            v_spb -= 140
            if v_spb < 140:
                v_spb = 14000
                c_spb += 1
                spb_tube.actual_volume = 14000

            # Discard tips
            drop(m300)


    # -----------------------------------------------------
    # Discard supernatant
    # -----------------------------------------------------
    def d_120():

        # Transfer 120 uL of supernatant from TAGP plate to MIDI plate
        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            # New tips
            if not m300.hw_pipette['has_tip']:
                pick_up(m300, tips300)
                
            x_offset_source = find_side(i) * x_offset_rs

            # Source TAGP plate
            src = magnet_rack.columns()[i][0]

            remove_supernatant_and_drop(pip=m300,
                        reagent=spb_reagent,
                        tube_type=fpcr_tube,
                        volume=45,
                        src=src,
                        x_offset_src=x_offset_source,
			pickup_height=4.5)
          
    # -----------------------------------------------------
    # Transfer ethanol
    # -----------------------------------------------------
    def xfer_eth():

        nonlocal c_eth
        nonlocal v_eth

        # New tips
        if not m300.hw_pipette['has_tip']:
            pick_up(m300, tips300)

        # Dispense Ethanol
        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            robot.comment(str(c_eth))
        
            # Destination MIDI plate
            dest_wells = [magnet_rack.columns()[i][0]]

            # Dispense 200 ul of Ethanol
            distribute_custom(pip = m300,
                        reagent = eth_reagent,
                        tube_type = eth_tube,
                        volume = 175,
                        src = eth_src[c_eth][0],
                        dest = dest_wells,
                        max_volume = 175,
                        disp_height=3,
                        extra_dispensal = 0,
                        touch_tip_aspirate = False,
                        touch_tip_dispense = False)

            # Ethanol remaining volume
            v_eth -= 175
            if v_eth < 175:
                v_eth = 14000
                c_eth += 1
                eth_tube.actual_volume = 14000

        # Dont discard tips
        drop(m300)

    # -----------------------------------------------------
    # Discard supernatant
    # -----------------------------------------------------
    def d_200():
        # Transfer 120 uL of supernatant from TAGP plate to MIDI plate
        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            # New tips
            if not m300.hw_pipette['has_tip']:
                pick_up(m300, tips300)
                
            x_offset_source = find_side(i) * x_offset_rs

            # Source TAGP plate
            src = magnet_rack.columns()[i][0]

            remove_supernatant_and_drop(pip=m300,
                        reagent=eth_reagent,
                        tube_type=fpcr_tube,
                        volume=200,
                        src=src,
                        x_offset_src=x_offset_source)


    # -----------------------------------------------------
    # Transfer RSB
    # -----------------------------------------------------
    def xfer_rsb():

        nonlocal c_rsb
        nonlocal v_rsb 
    
        # New tips
        if not m300.hw_pipette['has_tip']:
            pick_up(m300, tips300)

        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            robot.comment(str(c_eth))
        
            # Destination MIDI plate
            dest_wells = [magnet_rack.columns()[i][0]]

            # Dispense 81 ul of SPB
            distribute_custom(pip = m300,
            reagent = rsb_reagent,
            tube_type = rsb_tube,
            volume = 175,
                    src = rsb_src[c_rsb][0],
                    dest = dest_wells,
                    max_volume = 175,
                    disp_height = 3,
                    extra_dispensal = 0,
                    touch_tip_aspirate = False,
                    touch_tip_dispense = False)

            # Ethanol remaining volume
            v_rsb -= 175
            if v_rsb < 175:
                v_rsb = 12000
                c_rsb += 1
                rsb_tube.actual_volume = 12000

        # Discard tips
        drop(m300)


    # -----------------------------------------------------
    # Mix RSB
    # -----------------------------------------------------
    def mix_rsb():
 
        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            # New tips
            if not m300.hw_pipette['has_tip']:
                pick_up(m300, tips300)

            # Destination MIDI plate
            dest_wells = [magnet_rack.columns()[i][0]]

            # Mix
            custom_mix(pip = m300,
                    reagent = rsb_reagent,
                    repetitions = 5,
                    volume = 30,
                    location = dest_wells[0],
                    mix_height = 1,
                    source_height = 1)

            # Discard tips
            drop(m300)    

    # -----------------------------------------------------
    # Discard supernatant
    # -----------------------------------------------------
    def elucion():
        # Transfer 30 uL of elution from MIDI plate to FPCT plate
        for i in range(len(magnet_rack.columns()[0:NUM_SAMPLES // 8])):

            # New tips
            if not m300.hw_pipette['has_tip']:
                pick_up(m300, tips300)

            x_offset_source = find_side(i) * x_offset_rs

            # Source TAP plate
            src = magnet_rack.columns()[i][0]

            # Destination FPCR plate
            dest = result_rack.columns()[i][0]

            # Transfer
            remove_supernatant(pip=m300,
                        reagent=fpcr_reagent,
                        tube_type=fpcr_tube,
                        volume=45,
                        src=src,
                        dest=dest,
                        x_offset_src=x_offset_source,
                        max_volume=200)

            # Drop tip
            drop(m300)
        
    # -----------------------------------------------------
    # Execution plan
    # -----------------------------------------------------
    STEPS = {
        1:{'Execute': True, 'Function': xfer_and_mix_spb,   'Description': 'Transferir 81 µL de SPB a MIDI y mezclar 10 veces'},
        2:{'Execute': True, 'Function': xfer_and_mix_spb,   'Description': 'Transferir 81 µL de SPB a MIDI y mezclar 10 veces'},
        3:{'Execute': True, 'Function': wait,       'Description': 'Incubar a temperatura ambiente 5 min', 'wait_time': 3},
        4:{'Execute': True, 'Function': magnet_on,  'Description': 'Activar el módulo magnético 5 min', 'wait_time': 3},
        5:{'Execute': True, 'Function': d_120,      'Description': 'Desechar 126 µL de sobrenadante'},
        6:{'Execute': True, 'Function': xfer_rsb,   'Description': 'Añadir 32 µL de RSB a MIDI'},
        7:{'Execute': True, 'Function': xfer_rsb,   'Description': 'Añadir 32 µL de RSB a MIDI'},
        8:{'Execute': True, 'Function': magnet_off, 'Description': 'Desactivar el módulo magnético'},
        9:{'Execute': True, 'Function': mix_rsb,    'Description': 'Mezclar RSB (en MIDI) 5 veces  y esperamos 2 min.', 'wait_time': 12},
        10:{'Execute': True, 'Function': magnet_on,  'Description': 'Activar el módulo magnético 2 min', 'wait_time': 12}, 
        11:{'Execute': True, 'Function': xfer_eth,   'Description': 'Transferir 200 µL de Etanol a MIDI'},
	12:{'Execute': True, 'Function': wait,       'Description': 'Esperar 30 seg', 'wait_time': 3},  
        13:{'Execute': True, 'Function': d_200,      'Description': 'Desechar 200 µL de sobrenadante'},
	14:{'Execute': True, 'Function': xfer_eth,   'Description': 'Transferir 200 µL de Etanol a MIDI'},
        15:{'Execute': True, 'Function': xfer_eth,   'Description': 'Transferir 200 µL de Etanol a MIDI'},
	16:{'Execute': True, 'Function': wait,       'Description': 'Esperar 30 seg', 'wait_time': 3},  
        17:{'Execute': True, 'Function': d_200,      'Description': 'Desechar 200 µL de sobrenadante'},
        18:{'Execute': True, 'Function': wait,       'Description': 'Dejar secar 5 min en iman', 'wait_time': 3},
        19:{'Execute': True, 'Function': elucion,    'Description': 'Dispensar 30 µL de elución a placa FPCR'},
        20:{'Execute': True, 'Function': magnet_off, 'Description': 'Desactivar el módulo magnético'},
    }

    # #####################################################
    # 3. Execute every step!!
    # #####################################################
    for step in STEPS:
        run_step(step)
   
    # track final used tip
    save_tip_info()

    # -----------------------------------------------------
    # Stats
    # -----------------------------------------------------
    if not robot.is_simulating():
        end = finish_run()

        robot.comment('===============================================')
        robot.comment('Start time:   ' + str(start))
        robot.comment('Finish time:  ' + str(end))
        robot.comment('Elapsed time: ' + str(datetime.strptime(end, "%Y/%m/%d %H:%M:%S") - datetime.strptime(start, "%Y/%m/%d %H:%M:%S")))
        for key in tip_log['used']:
            val = tip_log['used'][key]
            robot.comment('Tips "' + str(key) + '" used: ' + str(val))
        robot.comment('===============================================')
