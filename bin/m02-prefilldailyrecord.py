import datetime

from dateutil.relativedelta import relativedelta

from kardboard.models import Kard, DailyRecord
from kardboard.util import make_start_date, make_end_date


def main():
    oldest_card = Kard.objects.all().order_by('+backlog_date')[0]
    start_date = make_start_date(date=oldest_card.backlog_date)
    end_date = make_end_date(date=datetime.datetime.now())

    print "Daily records: %s" % DailyRecord.objects.count()
    print "Creating daily records"
    print "%s --> %s" % (start_date, end_date)

    current_date = start_date
    while current_date <= end_date:
        DailyRecord.calculate(current_date)
        current_date = current_date + relativedelta(days=1)

    print "DONE!"
    print "Daily records: %s" % DailyRecord.objects.count()

if __name__ == "__main__":
    main()
