from typing import Sequence

import matplotlib
import matplotlib.pyplot as plt
import screeninfo
import numpy as np


matplotlib.use("TkAgg")
plt.rcParams['toolbar'] = 'None'  # disables toolbar


def center_window():
	monitor = screeninfo.get_monitors()[0]
	height, width = monitor.height, monitor.width

	dx, dy = 600, 600
	window_manager = plt.get_current_fig_manager()
	window_manager.window.wm_geometry(f"+{int(width/2 - dx/2)}+{int(height/2 - dy/2)}")


def get_legend_location(y_values: Sequence[float]) -> str:
	""" Returns:
			legend location allowing for display of the former without overlap with visualization of y-values, that is
				'upper right' if max value within left half of y_values,
				'upper left' otherwise """

	max_value_index = np.argmax(y_values)

	return ['upper right', 'upper left'][max_value_index > (len(y_values) / 2)]


def close_window_on_button_press():
	plt.show(block=False)
	plt.waitforbuttonpress(timeout=0)
