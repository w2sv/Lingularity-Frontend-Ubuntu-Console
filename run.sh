#!/bin/bash

# cd to script path
SCRIPT_PATH=$(dirname "$(realpath -s "$0")")
cd "$SCRIPT_PATH" || exit

# activate ./env
chmod +x .source-conda-executable.sh
source .source-conda-executable.sh
conda activate ./env

# run program
python -m frontend

# uncomment to keep terminal open when failing
$SHELL