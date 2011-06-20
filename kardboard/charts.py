from pygooglechart import StackedVerticalBarChart, SimpleLineChart, Axis


class KardboardChartMixer(object):
    def find_even_number(self, num, divisor=10):
        return num - (num % divisor)


class ThroughputChart(StackedVerticalBarChart, KardboardChartMixer):
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


class MovingCycleTimeChart(SimpleLineChart, KardboardChartMixer):
    def __init__(self, *args, **kwargs):
        super(MovingCycleTimeChart, self).__init__(*args, **kwargs)
        self.set_colours(['DC3912', '3366CC'])

        self.desired_min = 10
        self.desired_max = 15

    def setup_grid(self, dataset):
        max_y = max(dataset, key=lambda x: x[1])[1]
        max_y = self.find_even_number(max_y + 10, 10)
        self.y_range = (0, max_y)
        left_axis = range(0, max_y + 1, 10)
        self.set_axis_labels(Axis.LEFT, left_axis)

        range_start = float(self.desired_max) / max_y
        range_stop = float(self.desired_min) / max_y

        self.add_horizontal_range('E5ECF9', range_start, range_stop)

    def add_first_line(self, daily_average):
        self.set_x_range = (0, len(daily_average))
        self.add_data([m[1] for m in daily_average])
        self.set_axis_labels(Axis.BOTTOM,
                [m[0].strftime("%m/%d") for m in daily_average])

        self.setup_grid(daily_average)

    def add_line(self, daily_average):
        self.add_data([m[1] for m in daily_average])


class CumulativeFlowChart(MovingCycleTimeChart):
    def __init__(self, *args, **kwargs):
        super(MovingCycleTimeChart, self).__init__(*args, **kwargs)
        self.colours = ['DC3912', 'FF9900', '109618']
        self.set_colours(self.colours)

    def setup_grid(self, dataset):
        max_y = max(dataset, key=lambda x: x.backlog_cum).backlog_cum
        max_y = self.find_even_number(max_y + 10, 10)
        self.y_range = (0, max_y)
        left_axis = range(0, max_y + 1, 20)
        self.set_axis_labels(Axis.LEFT, left_axis)

        x_labels = []
        counter = 1
        for row in dataset:
            if counter % 7 == 0 or counter == 1:
                x_labels.append(row.date.strftime("%m/%d"))
            else:
                x_labels.append('')
            counter = counter + 1
        self.set_axis_labels(Axis.BOTTOM, x_labels)

        self.add_data([0] * 2)

        #self.add_fill_range('000000', 0, 1)
        self.add_fill_range("F4C3B7", 0, 1)
        self.add_fill_range("FFE0B2", 1, 2)
        self.add_fill_range("B7DFB9", 2, 3)
