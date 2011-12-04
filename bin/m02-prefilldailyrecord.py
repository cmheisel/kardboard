import datetime

from kardboard.models import Kard, DailyRecord
from kardboard.util import make_start_date, make_end_date

from kardboard.tasks import update_daily_records


def main():
    DailyRecord._get_collection().drop_indexes()
    oldest_card = Kard.objects.all().order_by('+backlog_date')[0]
    start_date = make_start_date(date=oldest_card.backlog_date)
    end_date = make_end_date(date=datetime.datetime.now())

    print "Daily records: %s" % DailyRecord.objects.count()
    print "Creating daily records"
    print "%s --> %s" % (start_date, end_date)

    days = end_date - start_date
    print "Going back %s days" % days.days

    r = update_daily_records.apply(args=(days.days,))
    r.get()

    print "DONE!"
    print "Daily records: %s" % DailyRecord.objects.count()

if __name__ == "__main__":
    main()
