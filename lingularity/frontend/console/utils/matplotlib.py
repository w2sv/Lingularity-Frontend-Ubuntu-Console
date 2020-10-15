from typing import Sequence
from itertools import chain

import matplotlib
import matplotlib.pyplot as plt
import screeninfo
import numpy as np


matplotlib.use("TkAgg")
plt.rcParams['toolbar'] = 'None'


def center_windows():
	monitor = screeninfo.get_monitors()[0]
	height, width = monitor.height, monitor.width

	dx, dy = 600, 600
	window_manager = plt.get_current_fig_manager()
	window_manager.window.wm_geometry(f"+{int(width/2 - dx/2)}+{int(height/2 - dy/2)}")


def get_legend_location(*y_range: Sequence[float]) -> str:
	assert len(set((len(_range) for _range in y_range))) == 1

	range_length = len(y_range[0])

	max_value_index_concatenated_values = np.argmax(list(chain(*y_range)))
	max_value_index = max_value_index_concatenated_values - ((max_value_index_concatenated_values // (range_length - 1)) * range_length)

	return ['upper right', 'upper left'][int(max_value_index > (range_length / 2))]
