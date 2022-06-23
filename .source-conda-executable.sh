SHELL=/bin/bash

LOCAL_CONDA_EXECUTABLE=/home/w2sv/miniconda3/etc/profile.d/conda.sh

if test -f "$LOCAL_CONDA_EXECUTABLE"; then
  source $LOCAL_CONDA_EXECUTABLE
else
  echo "$LOCAL_CONDA_EXECUTABLE does not exist. Rectification of path to local conda executable required"
  return
fi