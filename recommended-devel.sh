#!/bin/bash
: ${CMD_ARGS:=gui --debug --no-inline --clear-cache}
python3 ./main.py ${CMD_ARGS[@]} $@