import optparse
import random

from util import (
    _convert_dates,
    _get_team,
    _verify_rg,
    _get_cards_by_team,
    _get_cards_by_report_group
)

def sample_lead_times(team_or_rg, start_date, end_date, max_samples=100, min_samples=11):
    try:
        team = _get_team(team_or_rg)
        cards = _get_cards_by_team(team, start_date, end_date)
    except ValueError:
        rg_slug = _verify_rg(team_or_rg)
        cards = _get_cards_by_report_group(rg_slug, start_date, end_date)

    # TODO: pull random cycle time list and return it
    assert random, cards

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-n", "--max-samples", dest="max_samples",
        help="Maximum number of samples to return", default=100)
    parser.add_option("-m", "--min-samples", dest="min_samples",
        help="Maximum number of samples to return", default=11)

    options, args = parser.parse_args()
    team_or_rg = args[0]
    start_date = args[1]
    end_date = args[2]

    start_date, end_date = _convert_dates(start_date, end_date)

    # TODO: Figure out how to get data out of the options object
    sample_lead_times(
        team_or_rg, start_date, end_date,
    )
