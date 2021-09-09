# Tartan Artibeus Ground Software

This repository provides ground software for the Tartan Artibeus satellite.

Useful tips:
* Write a hex command to a file:
```bash
# A common_ack from COMM to TERM (COMM expects a common_ack back from TERM):
echo -en \\x22\\x69\\x06\\x01\\x00\\x01\\x00\\x10\\x10 > common-ack.hex
# Expected reply from TERM to COMM:
echo -en \\x22\\x69\\x06\\x01\\x00\\x01\\x00\\x01\\x10 > reply.hex
```
* View a hex command file:
```bash
hexdump -C common-ack.hex
hexdump -C reply.hex
```

## Directory Contents

* [demo](demo/README.md): Demonstrates TAOLST protocol
* [README.md](README.md): This document

## License

Written by Bradley Denby  
Other contributors: None

See the top-level LICENSE file for the license.
