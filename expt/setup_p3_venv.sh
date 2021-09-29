#!/bin/bash
#
# setup_p3_venv.sh
# A bash script to set up Python 3 virtual environment
#
# Usage: ./setup_p3_venv.sh
# Prerequisites:
#  - sudo apt install python3-venv
# Arguments:
#  - None
# Outputs:
#  - Python 3 virtual environment
#
# Written by Bradley Denby
# Other contributors: None
#
# See the top-level LICENSE file for the license.

python3 -m venv p3-env
source p3-env/bin/activate
python3 -m pip install pyserial==3.5
deactivate
