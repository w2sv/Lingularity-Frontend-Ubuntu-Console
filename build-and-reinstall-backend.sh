SHELL=/bin/bash

source .source-conda-executable.sh

cd ../Lingularity-Backend || exit
conda activate ./env
poetry build -vvv

cd ./dist || exit
dist_dir_path=$(realpath .)
# shellcheck disable=SC2012
latest_backend_wheel=$(ls -t | head -n1)

echo Determined latest backend wheel: "$latest_backend_wheel"

cd ../../Lingularity-Frontend-Ubuntu-Console || exit
conda activate ./env
pip uninstall -y backend
pip install "$dist_dir_path/$latest_backend_wheel"