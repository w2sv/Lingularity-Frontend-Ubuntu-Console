SHELL=/bin/bash

source /home/w2sv/miniconda3/etc/profile.d/conda.sh
conda activate ./console-env
python -m lingularity.frontend.console.main
