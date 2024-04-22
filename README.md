# tbk-v3

Tape-Backup Software for LTO-Tapes Version 3

## List of Exit-Codes

## Issues

1. Hardcoded for `/dev/st0` and `/dev/nst0`
2. Hardcoded for LTO-3

## TODO

1. Implement Silent and "Script" mode
   1. Silent-Mode: only exit-code as response
   2. Script-Mode: give enough feedback, dd-arg `status=progress` is changed to `none` so only at the end the statistics of dd is shown
2. Create a config-file with default LTO-n Values and the ability to cusomize them. LTO-n-LUT: Propably written in xml
3. Proper exception-Handling
4. Create a Wiki
