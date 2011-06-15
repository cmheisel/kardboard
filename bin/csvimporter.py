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


def parse_kardboard_output(csv_filename):
    reader = csv.DictReader(open(csv_filename))
    for row in reader:

        try:
            k = Kard.objects.get(key=row['key'])
        except Kard.DoesNotExist:
            k = Kard()

        try:
            k.category = row['category']
            k.backlog_date = parse_date(row['backlog_date'])
            k.start_date = parse_date(row['start_date'])
            k.done_date = parse_date(row['done_date'])
            k.key = row['key']
            k.title = row['title']
            k.state = row['state']
            if k.state == "Unknown":
                k.state = "Done"
            k.save()
        except Exception, e:
            print "Error reported!"
            print row
            print str(e)
            print "============="
            print
            print


def parse_google_output(csv_filename):
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
    parse_kardboard_output(sys.argv[1])
