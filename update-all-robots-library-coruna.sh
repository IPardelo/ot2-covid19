#!/bin/bash


# -------------------------------------------------------------------------------------------------------
# Script Name: update-all-robots-library.sh
#
# Author: Luis Lorenzo Mosquera, Víctor Soroña Pombo & Ismael Castiñeira Paz
#
# Date : June 12th 2020
#
# Description: The following script updates ot2 libraries in specified input parameters 
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
IP='69.101.94.'
export SSHPASS='L@b0r4t0ri0'
PUBLIC_KEY_PATH='/home/luis/.ssh/id_rsa.pub'
LOCAL_LIBRARY_PATH='/home/luis/Escritorio/ot2-covid19/library'
ROBOT_RP_USER='root'
ROBOT_LIBRARY_PATH='/root'

SARS=(${IP}'150' ${IP}'157')
SBRS=(${IP}'151' ${IP}'152' ${IP}'156')
SCRS=(${IP}'153' ${IP}'155')
SEC=(${IP}'154')

ALL_ROBOTS=("${SARS[@]}" "${SBRS[@]}" "${SCRS[@]}" "${SEC[@]}")


# -------------------------
# Input processing
# -------------------------
if [[ $1 == "a" ]]; then
    printf "Updating A robots\n\n"
    TARGETS=("${SARS[@]}")
elif [[ $1 == "b" ]]; then
    printf "Updating B robots\n\n"
    TARGETS=("${SBRS[@]}")
elif [[ $1 == "c" ]]; then
    printf "Updating C robots\n\n"
    TARGETS=("${SCRS[@]}")
elif [[ $1 == "s" ]]; then
    printf "Updating Sequecing robot\n\n"
    TARGETS=("${SEC[@]}")
else
    printf "Updating all robots\n\n"
    TARGETS=("${ALL_ROBOTS[@]}")
fi


# -------------------------
# Updating loop
# -------------------------
for robot_ip in "${TARGETS[@]}"; do
   echo "updating ~> $robot_ip"
   sshpass -e scp -i $PUBLIC_KEY_PATH -r $LOCAL_LIBRARY_PATH $ROBOT_RP_USER@$robot_ip:$ROBOT_LIBRARY_PATH
done
