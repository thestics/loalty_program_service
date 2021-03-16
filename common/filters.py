import json

from flask_admin.model.filters import BaseFilter
from flask_admin.babel import lazy_gettext
from flask_admin.contrib.peewee.filters import BasePeeweeFilter


class BaseJSONFilter(BaseFilter):
    def clean(self, value):
        return json.loads(value)

    def validate(self, value):
        try:
            json.loads(value)
        except (TypeError, ValueError):
            return False

        return True


class FilterContains(BasePeeweeFilter):
    def apply(self, query, value):
        return query.filter(self.column.contains(value))

    def operation(self):
        return lazy_gettext('json contains')


class JSONContainsFilter(FilterContains, BaseJSONFilter):
    pass
