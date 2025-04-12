import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import os
# import sys
# sys.path.append(os.path.abspath("../../"))
# from modules.map.pure_pursuit import PurePursuit
# pp = PurePursuit()
# waypoints = pp.read_waypoints()


class PathEditor:
    def __init__(self, csv_path, csv_save_path=None):
        self.csv_path = csv_path
        self.csv_save_path = csv_save_path if csv_save_path else csv_path
        self.df = pd.read_csv(csv_path)
        self.points = self.df[['x', 'y']].values.tolist()
        self.selected_index = None

        self.fig, self.ax = plt.subplots()
        self.toolbar = self.fig.canvas.manager.toolbar  # Access the toolbar
        self.scatter = self.ax.scatter(*zip(*self.points), color='blue', picker=True, s=50)
        self.line, = self.ax.plot(*zip(*self.points), color='gray')

        self.ax.grid(True, which='both')
        self.ax.set_xticks([i * 0.1 for i in range(-100, 100)], minor=False)
        self.ax.set_yticks([i * 0.1 for i in range(-100, 100)], minor=False)
        self.ax.set_aspect('equal')

        self.cid_click = self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.cid_release = self.fig.canvas.mpl_connect('button_release_event', self.on_release)
        self.cid_motion = self.fig.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.cid_key = self.fig.canvas.mpl_connect('key_press_event', self.on_key)

        plt.title("Use toolbar to pan/zoom — Only click when no tool is active!\n"
                  "Left click = add/drag, Right click = delete, S = save")
        self.draw()
        plt.show()

    def is_toolbar_active(self):
        return self.toolbar.mode != ''

    def draw(self):
        if len(self.points) > 0:
            xs, ys = zip(*self.points)
        else:
            xs, ys = [], []

        self.scatter.set_offsets(self.points)
        self.line.set_data(xs, ys)
        self.ax.relim()
        self.ax.autoscale_view()
        self.fig.canvas.draw_idle()

    def on_click(self, event):
        if self.is_toolbar_active():
            return  # Don't handle clicks if pan/zoom is active
        if event.inaxes != self.ax or event.xdata is None or event.ydata is None:
            return

        if event.button == 1:  # Left click
            for i, (x, y) in enumerate(self.points):
                if abs(event.xdata - x) < 0.05 and abs(event.ydata - y) < 0.05:
                    self.selected_index = i
                    return
            self.points.append([event.xdata, event.ydata])
            self.draw()
        elif event.button == 3:  # Right click
            for i, (x, y) in enumerate(self.points):
                if abs(event.xdata - x) < 0.05 and abs(event.ydata - y) < 0.05:
                    self.points.pop(i)
                    self.draw()
                    return

    def on_motion(self, event):
        if self.is_toolbar_active():
            return
        if self.selected_index is not None and event.inaxes == self.ax and event.xdata and event.ydata:
            self.points[self.selected_index] = [event.xdata, event.ydata]
            self.draw()

    def on_release(self, event):
        self.selected_index = None

    def on_key(self, event):
        if event.key.lower() == 's':
            pd.DataFrame(self.points, columns=['x', 'y']).to_csv(self.csv_save_path, index=False)
            print(f"Saved to {self.csv_save_path}")



if __name__ == "__main__":
    matplotlib.use('TkAgg')  # Interactive backend
    csv_relative_path = "../../modules/map/waypoints.csv"
    csv_absolute_path = os.path.join(os.path.dirname(__file__), csv_relative_path)

    PathEditor(csv_absolute_path)
