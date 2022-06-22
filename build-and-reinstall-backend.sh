SHELL=/bin/bash

source .source-conda-executable.sh

cd ../Lingularity-Backend || exit
conda activate ./env
make wheel

cd ./dist || exit
dist_dir_path=$(realpath .)
latest_backend_wheel=$(find . -type f -name "backend*" | head -n 1)

cd ../../Lingularity-Frontend-Ubuntu-Console || exit
conda activate ./env
pip uninstall -y backend
pip install "$dist_dir_path/$latest_backend_wheel"