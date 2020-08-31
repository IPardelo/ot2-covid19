import sys
sys.path.append('/root/ot2-covid19-master/ot2/library')

from constants import IP
from general.rename_robot import rename
from general.configure_static_ip import set_static_ip
from opentrons import robot

if not robot.is_simulating():
    rename('sbr3')
    set_static_ip(IP.replace('x', '56'))

robot.comment("Please, reboot")
