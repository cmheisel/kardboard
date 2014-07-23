from kardboard.app import app
from kardboard.tickethelpers import JIRAHelper
from kardboard.models import Kard, ReportGroup
from kardboard.util import make_start_date, make_end_date


def find_value_cards(year):
    start = make_start_date(year, 1, 1)
    end = make_end_date(year, 12, 31)

    query = Kard.objects.filter(done_date__gte=start, done_date__lte=end)
    rg = ReportGroup('dev', query)

    cards = [c for c in rg.queryset if c.is_card]
    return cards


def find_jira_issues(filter_id):
    helper = JIRAHelper(app.config, None)
    issues = helper.service.getIssuesFromFilter(helper.auth, filter_id)
    return issues


def missing_card_report(filter_id, year, details=True, other_cards=[]):

    cards = find_value_cards(year)
    cards = cards + other_cards
    issues = find_jira_issues(filter_id)

    diff = len(issues) - len(cards)
    diff_pct = diff / len(issues)

    print "Overview"
    print "Cards: %s" % (len(cards), )
    print "Issues: %s" % (len(issues), )
    print "Diff: %s / %.2f" % (diff, diff_pct * 100)

    if details:
        card_keys = [c.key for c in cards]
        issue_keys = [i.key for i in issues]

        for i in issue_keys:
            if i not in card_keys:
                print i

    return issues, cards


if __name__ == "__main__":
    issues, cards = missing_card_report(13122, 2012, details=False)
    missing_card_report(13121, 2013, other_cards=cards)
