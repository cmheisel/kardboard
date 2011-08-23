import base64
import md5

import requests

from pygooglechart import StackedVerticalBarChart, SimpleLineChart, Axis, PieChart2D


class KardboardChartMixer(object):
    def find_even_number(self, num, divisor=10):
        return num - (num % divisor)

    @property
    def cache_key(self):
        return str(md5.new(self.get_url()).hexdigest())

    def b64_image_src(self):
        from kardboard.app import cache
        image_src = cache.get(self.cache_key)
        if not image_src:
            b64_image_src = "data:image/png;base64,%s"
            r = requests.post(self.BASE_URL, data='&'.join(self.get_url_bits()))
            b64_image_src = b64_image_src % base64.b64encode(r.content)
            cache.set(self.cache_key, b64_image_src, 60 * 10)
            image_src = b64_image_src
        return image_src


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

        from kardboard.app import app
        goal = app.config.get('CYCLE_TIME_GOAL', ())
        if goal:
            self.desired_min = goal[0]
            self.desired_max = goal[1]
        else:
            self.desired_max = 0
            self.desired_min = 0

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

        x_labels = []
        counter = 1
        for row in daily_average:
            if counter % 7 == 0 or counter == 1:
                x_labels.append(row[0].strftime("%m/%d"))
            else:
                x_labels.append('')
            counter = counter + 1
        self.set_axis_labels(Axis.BOTTOM, x_labels)
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
            if counter % 14 == 0 or counter == 1:
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


class CycleDistributionChart(PieChart2D):
    def __init__(self, *args, **kwargs):
        super(CycleDistributionChart, self).__init__(*args, **kwargs)

        self.colours = ['3366CC', 'DC3912', 'FF9900', '109618', '990099', '0099C6', 'DD4477']
        self.set_colours(self.colours)
