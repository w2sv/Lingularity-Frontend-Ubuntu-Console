SHELL=/bin/bash

source .source-conda-executable.sh
conda activate ./env
python -m frontend.__init__