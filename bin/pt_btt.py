import csv

from collections import defaultdict

from time_in_state import (
    parse_date,
    _get_team,
    Kard,
    _get_card_logs,
)

def histogram(times):
    d = defaultdict(int)
    for t in times:
        d[t] += 1
    return dict(d)


def _get_cards(team):
    # We need cards that are done
    # Plus cards that are in progress
    cards = Kard.objects.filter(
        team=team.name,
    )
    return list(cards)


def state_cycle_history(team_name, state_name, start_date, end_date):
    team = _get_team(team_name)
    cards = _get_cards(team)

    by_card = {}
    state_hours = []
    for card in cards:
        card_total_time_in_state = 0
        logs = _get_card_logs(card)
        for log in logs:
            if log.state == state_name:
                if log.entered >= start_date:
                    if log.entered <= end_date:
                        card_total_time_in_state += log.duration
        if card_total_time_in_state > 0:
            by_card[card.key] = card_total_time_in_state
            state_hours.append(card_total_time_in_state)

    filename = "%s_%s_%s.csv" % \
        (start_date.strftime("%b-%Y"),
         end_date.strftime("%b-%Y"),
         team_name)
    writer = csv.writer(file(filename, 'w'))
    for card, wait in by_card.items():
        writer.writerow([card, float(wait/24.0)])

if __name__ == "__main__":
    import sys
    team_name = sys.argv[1]
    state_name = sys.argv[2]
    start_date = parse_date(sys.argv[3])
    end_date = parse_date(sys.argv[4])
    state_cycle_history(team_name, state_name, start_date, end_date)
