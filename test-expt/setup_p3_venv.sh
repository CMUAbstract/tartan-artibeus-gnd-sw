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

if [ ! -d "./p3-env/" ]
then
  python3 -c "import venv" 1> /dev/null 2> /dev/null
  if [ $? -ne 0 ]
  then
    echo "It appears that the Python venv module is not installed"
    echo "  Try sudo apt install python3-venv"
    echo "  Exiting"
    exit 1
  else
    python3 -m venv p3-env
    source p3-env/bin/activate
    python3 -m pip install pyserial==3.5
    deactivate
  fi
fi
