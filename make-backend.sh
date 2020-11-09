SHELL=/bin/bash

source /home/w2sv/miniconda3/etc/profile.d/conda.sh

cd ../backend || exit
conda activate ./env
make wheel

cd ../frontend || exit
conda activate ./env
pip uninstall -y backend
pip install /home/w2sv/W2SV/python/projects/lingularity/dist/backend-0.1.2-py3-none-any.whl