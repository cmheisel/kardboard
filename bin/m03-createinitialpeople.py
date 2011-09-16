"""
Data migration that sets up the initial set of Person
objects. After this is run they'll be created
and updated by the actually_update method of
a card's ticket helper.
"""

from kardboard.tasks import normalize_people
from kardboard.models import Person


def main():
    print Person.objects.count()
    r = normalize_people.apply()
    r.get()
    print Person.objects.count()

if __name__ == "__main__":
    main()
