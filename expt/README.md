# EXPT Board Test Script

This directory contains scripts and files to test the EXPT boards flight 401
bootloader and user programs.

Usage:

```bash
cd $HOME/git-repos/tartan-artibeus-gnd-sw/demo/
python3 expt.py ./sample.hex ./
diff expected.hex reply-sample.hex
# There should be no output
```

## Directory Contents

* [demo.py](demo.py): Demonstration Python script
* [expected.hex](expected.hex): Expected reply of the terminal to sample.hex
* [sample.hex](sample.hex): Sample input command
* [README.md](README.md): This document

## License

Written by Bradley Denby  
Other contributors: None

See the top-level LICENSE file for the license.
