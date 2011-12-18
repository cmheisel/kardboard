from kardboard.models import Kard, States


def main():
    states = States()

    backlogged_states = []
    for k in Kard.backlogged():
        if k.state not in states:
            if k.state not in backlogged_states:
                backlogged_states.append(k.state)
            k.state = states.backlog
            k.save()

    start_states = []
    for k in Kard.in_progress():
        if k.state not in states:
            if k.state not in start_states:
                start_states.append(k.state)
            k.state = states.start
            k.save()

    print "Valid states"
    print states

    print "Backlogged states that went away"
    print backlogged_states

    print "Start states that went away"
    print start_states


if __name__ == "__main__":
    main()
