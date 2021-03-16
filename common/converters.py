from peewee import ForeignKeyField, fn
from wtfpeewee.orm import model_form

from flask_admin import form
from flask_admin.model import filters
from flask_admin.model.filters import convert
from flask_admin.contrib.peewee.tools import get_meta_fields
from flask_admin.contrib.peewee.form import (
    InlineModelConverter as PInlineModelConverter, CustomModelConverter)
from flask_admin.contrib.peewee.filters import (
    FilterConverter as PFilterConverter)

from common.filters import JSONContainsFilter
from common.fields import PrettyJsonField


class ModelConverter(CustomModelConverter):
    def handle_json(self, model, field, **kwargs):
        return field.name, PrettyJsonField(**kwargs)


class FilterConverter(PFilterConverter):
    json_filters = (JSONContainsFilter, )

    @convert('IntegerField', 'BigIntegerField', 'PrimaryKeyField', 'AutoField')
    def conv_int(self, column, name):
        return [f(column, name) for f in self.int_filters]

    @filters.convert('DateTimeField')
    def conv_datetime(self, column, name):
        return [f(fn.date_trunc('second', column), name)
                for f in self.datetime_filters]

    @filters.convert('BinaryJSONField', 'JSONField')
    def conv_json(self, column, name):
        return [f(column, name) for f in self.json_filters]


class InlineModelConverter(PInlineModelConverter):
    """
    Added support of the peewee>=3.0
    """

    def contribute(self, converter, model, form_class, inline_model):
        # Find property from target model to current model
        info = self.get_info(inline_model)

        for field in get_meta_fields(info.model):
            field_type = type(field)

            if field_type == ForeignKeyField:
                if field.rel_model == model:
                    reverse_field = field
                    break
        else:
            raise Exception(
                'Cannot find reverse relation for model %s' % info.model)

        # Remove reverse property from the list
        ignore = [reverse_field.name]

        if info.form_excluded_columns:
            exclude = ignore + info.form_excluded_columns
        else:
            exclude = ignore

        # Create field
        child_form = info.get_form()

        if child_form is None:
            child_form = model_form(info.model,
                                    base_class=form.BaseForm,
                                    only=info.form_columns,
                                    exclude=exclude,
                                    field_args=info.form_args,
                                    allow_pk=True,
                                    converter=converter)

        prop_name = reverse_field.backref

        label = self.get_label(info, prop_name)

        setattr(form_class,
                prop_name,
                self.inline_field_list_type(child_form,
                                            info.model,
                                            reverse_field.name,
                                            info,
                                            label=label or info.model.__name__))

        return form_class
