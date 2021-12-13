# Script for Programming EXPT Board through UART

This directory contains scripts and files to program the EXPT board with 
bootloader write page commands

Usage:

```bash
cd $HOME/git-repos/tartan-artibeus-gnd-sw/expt-chad/
python3 upload_program.py blink_app.hex /dev/ttyUSB0
```

## Directory Contents

* [blink_app.hex](blink_app.hex): Blink program for EXPT board in hex
* [upload_program.py](upload_program.py): Program the EXPT board
* [README.md](README.md): This document

## License

Written by Chad Taylor  
Other contributors: Brad Denby

See the top-level LICENSE file for the license.