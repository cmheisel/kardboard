import csv
import datetime

from kardboard.models import Kard


def parse_date(date_string):
    if date_string:
        month, day, year = date_string.split('/')
        month, day, year = int(month), int(day), int(year)
        return datetime.datetime(
            year=year, month=month, day=day, hour=0, minute=0, second=0)
    else:
        return None


def main(csv_filename):
    reader = csv.reader(open(csv_filename))
    for row in reader:
        try:
            k = Kard.objects.get(key=row[4])
        except Kard.DoesNotExist:
            k = Kard()

        try:
            k.category = row[0]
            k.backlog_date = parse_date(row[1])
            k.start_date = parse_date(row[2])
            k.done_date = parse_date(row[3])
            k.key = row[4]
            k.title = row[5]
            k.shirt_size = row[7]
            k.save()
        except Exception, e:
            print "Error reported!"
            print row
            print str(e)
            print "============="
            print
            print


if __name__ == "__main__":
    import sys
    main(sys.argv[1])
