# Scripts for Programming EXPT Board through UART

This directory contains scripts and files to program the EXPT board with 
bootloader write page commands

Usage:

```bash
cd $HOME/git-repos/tartan-artibeus-gnd-sw/expt-chad/
python3 upload_program.py blink_app.hex /dev/ttyUSB0
```

## Usage for multiprogramming the EXPT board

```bash
cd $HOME/git-repos/tartan-artibeus-sw/ta-expt/software/flight-chad-blr
make
st-flash write flight-chad-blr.bin 0x8000000
```
Power cycle the EXPT board


```bash
cd $HOME/git-repos/tartan-artibeus-gnd-sw/expt-chad
python3 upload_program_addr32.py blink-slow.hex /dev/ttyUSB0
```
Power cycle the EXPT board

Then edit the 0x8008000 in the line
```bash
START_ADDR = 0x8008000
```
to be 0x8050000 

```bash
python3 upload_program_addr32.py blink-med.hex /dev/ttyUSB0
```
Power cycle the EXPT board

Then edit the 0x8050000 in the line
```bash
START_ADDR = 0x8050000
```
to be 0x8080000 

```bash
python3 upload_program_addr32.py blink-fast.hex /dev/ttyUSB0
```
Power cycle the EXPT board

Now as you run 
```bash
python3 blink_demo_jump.py /dev/ttyUSB0
```
you should see the blink speed of the LEDs change each time a jump is made \
in the order of slow, med, fast repeatedly in a loop


## Directory Contents

* [blink_app.hex](blink_app.hex): Blink program for EXPT board in hex
* [blink-slow.hex](blink-slow.hex): Blink program with slow blinking speed for EXPT board in hex
* [blink-med.hex](blink-med.hex): Blink program with medium blinking speed for EXPT board in hex
* [blink-fast.hex](blink-fast.hex): Blink program with fast blinking speed for EXPT board in hex
* [flight-401-usr.hex](flight-401-usr.hex): Flight-401-usr program for EXPT board in hex
* [upload_program.py](upload_program.py): Program the EXPT board with UART
* [upload_program_ext.py](upload_program_ext.py): Program the EXPT board with UART using bootloader_write_page_ext command instead
* [upload_program_addr32.py](upload_program_addr32.py): Program the EXPT board with UART using bootloader_write_page_addr32 command instead
* [test_expt_data.py](test_expt_data.py): Test script for common_data command
* [README.md](README.md): This document

## License

Written by Chad Taylor  
Other contributors: Bradley Denby

See the top-level LICENSE file for the license.