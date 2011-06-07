from pygooglechart import StackedVerticalBarChart, Axis

class ThroughputChart(StackedVerticalBarChart):
    def __init__(self, *args, **kwargs):
        super(ThroughputChart, self).__init__(*args, **kwargs)
        self.set_colours(['92CC47', ])
        max_y = 100
        self.y_range = (0, max_y)
        self.set_grid(0, 25)
        left_axis = range(0, max_y + 1, 25)
        self.set_axis_labels(Axis.LEFT, left_axis)


    def add_bars(self, month_counts):
        self.set_x_range = (0, len(month_counts))
        self.set_bar_width((self.width - 100) / len(month_counts))
        self.add_data([m[1] for m in month_counts])
        self.set_axis_labels(Axis.BOTTOM, [m[0] for m in month_counts])