# EXPT Board Test Script for Flight 401 Software

This directory contains scripts and files to test the EXPT board flight 401
bootloader and user program.

Usage:

```bash
cd $HOME/git-repos/tartan-artibeus-gnd-sw/test-expt/
./setup_p3_venv.sh
python3 test_expt.py /dev/ttyUSB0
```

## Directory Contents

* [setup_p3_venv.sh](setup_p3_venv.sh): Set up Python virtual environment
* [test_expt.py](test_expt.py): Test the EXPT board
* [README.md](README.md): This document

## License

Written by Bradley Denby  
Other contributors: None

See the top-level LICENSE file for the license.
