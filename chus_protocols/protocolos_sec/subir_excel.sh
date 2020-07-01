#!/bin/bash


# -------------------------------------------------------------------------------------------------------
# Script Name: subir-excel.sh
#
# Author: Luis Lorenzo Mosquera, Víctor Soroña Pombo & Ismael Castiñeira Paz
#
# Date : July 1st 2020
#
# Description: The following script updates datasheet with qubit concetrarion os each sample 
#
# Error Log: Any errors or output associated with the script can be found in standard output
# 
# License: GPL-3.0
# -------------------------------------------------------------------------------------------------------

# -------------------------
# Install requirements
# -------------------------
# sudo apt install -y sshpass ssh-agent openssh-client

# -------------------------
# Constants
# -------------------------
IP=''
export SSHPASS='L@b0r4t010'
PUBLIC_KEY_PATH='~/ot-ssh-key'
LOCAL_DATA_PATHS=('/home/luis/Escritorio/data.csv' '/home/luis/Escritorio/data2.csv')
ROBOT_RP_USER='root'
ROBOT_REMOTE_PATH='/root'


# -------------------------
# Updating loop
# -------------------------
for path in "${LOCAL_DATA_PATHS[@]}"; do
   echo "updating ~> $path"
   sshpass -e scp -i $PUBLIC_KEY_PATH -r $path $ROBOT_RP_USER@$IP:$ROBOT_REMOTE_PATH
done
