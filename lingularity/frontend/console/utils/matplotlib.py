import matplotlib
import matplotlib.pyplot as plt
import screeninfo


matplotlib.use("TkAgg")


def center_matplotlib_windows():
	monitor = screeninfo.get_monitors()[0]
	height, width = map(lambda attr: getattr(monitor, attr), ['height', 'width'])

	dx, dy = 600, 600
	window_manager = plt.get_current_fig_manager()
	window_manager.window.wm_geometry(f"+{int(width/2 - dx/2)}+{int(height/2 - dy/2)}")
