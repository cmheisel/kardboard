from mongoengine.queryset import Q

from kardboard.app import app


class ReportGroup(object):
    def __init__(self, group, queryset):
        self.group = group
        self.qs = queryset
        super(ReportGroup, self).__init__()

    @property
    def queryset(self):
        groups_config = app.config.get('REPORT_GROUPS', {})
        group = groups_config.get(self.group, ())
        query = Q()

        if group:
            teams = group[0]
            for team in teams:
                query = Q(team=team) | query

        if query:
            return self.qs.filter(query)
        return self.qs
