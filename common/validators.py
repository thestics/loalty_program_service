import ipaddress

from wtforms.validators import ValidationError, InputRequired
from common.utils import BASE_58_SYMBOLS


def unique_validator(unique_field):
    """
    Validate uniqueness of the field
    :param unique_field: a field for which uniqueness will be checked
    :return:
    """

    cls = unique_field.model

    query = cls.select()

    def _unique(form, field):
        obj = query.where(unique_field == field.data).first()

        if not obj:
            return

        if not hasattr(form, '_obj') or not form._obj == obj:
            raise ValidationError('{cls.__name__} with '
                                  '{name}: '
                                  '{field.data} already exists'
                                  .format(cls=cls,
                                          name=(unique_field.verbose_name or
                                                unique_field.name),
                                          field=field))

    return _unique


def required_on_create(form, field):
    if form._obj:
        return

    return InputRequired()(form, field)


def validate_config(form, field):
    if not field.data:
        return

    if type(field.data) != dict:
        raise ValidationError("Expected json object")
