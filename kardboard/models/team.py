from kardboard.util import slugify


class Team(object):
    def __init__(self, name):
        self.name = name.strip()

    @property
    def slug(self):
        return slugify(self.name)


class TeamList(list):
    def __init__(self, *args):
        super(TeamList, self).__init__(args)
        self.teams = args

    @property
    def names(self):
        return [t.name for t in self.teams]

    @property
    def slug_name_mapping(self):
        return dict(
            [(t.slug, t.name) for t in self.teams]
        )
