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
    reader = csv.DictReader(open(csv_filename))
    for row in reader:

        try:
            k = Kard.objects.get(key=row['Ticket'])
        except Kard.DoesNotExist:
            k = Kard()

        try:
            k.category = row['Category']
            k.backlog_date = parse_date(row['Backlog Date'])
            k.start_date = parse_date(row['Start Date'])
            k.done_date = parse_date(row['Done Date'])
            k.key = row['Ticket']
            k.title = row['Card title']
            k.shirt_size = row['Shirt Size']
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
