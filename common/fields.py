from copy import copy
import json

from wtforms.fields import SelectField, SelectMultipleField
from wtforms.compat import text_type
from flask_admin.form.fields import JSONField
from flask_admin._compat import as_unicode

from common.widgets import ExtendedSelectWidget


class DynamicSelectField(SelectField):
    def __init__(self, label=None, validators=None, coerce=text_type,
                 choices=None, **kwargs):
        super(SelectField, self).__init__(label, validators, **kwargs)
        self.coerce = coerce
        self.choices_base = choices if callable(choices) else copy(choices)

    def _get_choices(self):
        if callable(self.choices_base):
            return self.choices_base()
        else:
            return self.choices_base

    def iter_choices(self):
        self.choices = self._get_choices()
        return super(DynamicSelectField, self).iter_choices()

    def pre_validate(self, form):
        self.choices = self._get_choices()
        return super(DynamicSelectField, self).pre_validate(form)


class ExtendedSelectField(SelectMultipleField):
    """
    Add support of ``optgroup`` grouping to
    default WTForms' ``SelectField`` class.

    Here is an example of how the data is laid out.

        (
            ('Fruits', (
                ('apple', 'Apple'),
                ('peach', 'Peach'),
                ('pear', 'Pear')
            )),
            ('Vegetables', (
                ('cucumber', 'Cucumber'),
                ('potato', 'Potato'),
                ('tomato', 'Tomato'),
            )),
            ('other','None Of The Above')
        )


    """
    widget = ExtendedSelectWidget()

    def pre_validate(self, form):
        """
        Don't forget to validate also values from embedded lists.
        """

        if self.data:
            choices = []
            for item_1, item_2 in self.choices:
                if type(item_2) in (list, tuple):
                    for choice, label in item_2:
                        choices.append(choice)
                else:
                    choices.append(item_1)

            for item in self.data:
                if item not in choices:
                    raise ValueError(self.gettext('Not a valid choice!'))


class PrettyJsonField(JSONField):
    def _value(self):
        if self.raw_data:
            return self.raw_data[0]
        elif self.data:
            # prevent utf8 characters from being converted to ascii
            return as_unicode(json.dumps(self.data,
                                         indent=2,
                                         sort_keys=True,
                                         ensure_ascii=False))
        else:
            return ''
