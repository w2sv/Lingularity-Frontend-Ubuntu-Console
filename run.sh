SHELL=/bin/bash

source /home/w2sv/miniconda3/etc/profile.d/conda.sh
conda activate ./env
python -m frontend.__init__
