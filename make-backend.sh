SHELL=/bin/bash

LOCAL_CONDA_EXECUTABLE=/home/w2sv/miniconda3/ec/profile.d/conda.sh

# for some reason not necessarily required
if test -f "LOCAL_CONDA_EXECUTABLE"; then
  source LOCAL_CONDA_EXECUTABLE
else
  echo "$LOCAL_CONDA_EXECUTABLE does not exist. Rectification of path to local conda executable required"
  return
fi

cd ../backend || exit
conda activate ./env
make wheel

cd ../dist || exit
dist_dir_path=$(realpath .)
latest_backend_wheel=$(find . -type f -name "backend*" | head -n 1)

cd ../frontend || exit
conda activate ./env
pip uninstall -y backend
pip install "$dist_dir_path/$latest_backend_wheel"