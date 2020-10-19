from typing import Iterable

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


def get_legend_location(max_y_value_sequence: Iterable[float]) -> str:
	max_value_index = np.argmax(max_y_value_sequence)

	return ['upper right', 'upper left'][max_value_index > (len(max_y_value_sequence) / 2)]
