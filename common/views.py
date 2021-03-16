import copy

from flask import abort, redirect, url_for, request, flash
from flask.views import MethodView
from peewee import JOIN, Field, prefetch as pw_prefetch, ModelBase
from flask_security import current_user
from flask_admin import expose
from flask_admin.menu import MenuLink, MenuCategory
from flask_admin.model import BaseModelView, template
from flask_admin.contrib.peewee import ModelView as PModelView
from flask_admin._compat import string_types
from markupsafe import Markup
from jinja2 import contextfunction
from json2html import json2html


from common.utils import camel2snake, serialize_dict
from common.converters import (ModelConverter, FilterConverter,
                               InlineModelConverter)


class ModelView(PModelView):
    """
    Added support of the peewee>=3.0
    """
    simple_list_pager = True

    model_form_converter = ModelConverter
    filter_converter = FilterConverter()
    inline_model_form_converter = InlineModelConverter
    join = None
    prefetch = None

    list_template = 'admin/custom_list.html'
    create_template = 'admin/custom_create.html'
    edit_template = 'admin/custom_edit.html'

    column_classes = {}
    details_column_formatters = {}

    dynamic_filters = False

    exclude_from_log = []

    def scaffold_filters(self, name):
        if isinstance(name, string_types):
            attr = getattr(self.model, name, None)
        else:
            attr = name

        if attr is None:
            raise Exception('Failed to find field for filter: %s' % name)

        # Check if field is in different model
        if attr.model != self.model:
            visible_name = '%s / %s' % (
                self.get_column_name(attr.model.__name__),
                self.get_column_name(attr.name))
        else:
            if not isinstance(name, string_types):
                visible_name = self.get_column_name(attr.name)
            else:
                visible_name = self.get_column_name(name)

        type_name = type(attr).__name__
        flt = self.filter_converter.convert(type_name,
                                            attr,
                                            visible_name)

        return flt

    def _handle_join(self, query, field, joins):
        if field.model != self.model and issubclass(field.model.__class__,
                                                    ModelBase):
            model_name = field.model.__name__

            if (model_name not in joins
                    and model_name not in [j.__name__
                                           for j in self._flatten_joins()]):
                query = query.join(field.model, JOIN.LEFT_OUTER)
                joins.add(model_name)

        return query

    def _order_by(self, query, joins, sort_field, sort_desc):
        if isinstance(sort_field, string_types):
            field = getattr(self.model, sort_field)
            query = query.order_by(field.desc() if sort_desc else field.asc())
        elif isinstance(sort_field, Field):
            if sort_field.model != self.model:
                query = self._handle_join(query, sort_field, joins)

            query = query.order_by(
                sort_field.desc() if sort_desc else sort_field.asc())

        return query, joins


    def get_query(self):
        query = super().get_query()

        if self.join is None:
            return query

        query = self.model.select(self.model, *self._flatten_joins())

        for join in self.join:
            join_to_previous = False
            if type(join) is tuple:
                join, join_to_previous = join

            if not join_to_previous:
                query = query.switch(self.model)

            query = query.join(join, JOIN.LEFT_OUTER)

        return query.switch(self.model)

    def _flatten_joins(self):
        if self.join is None:
            return list()

        return [j[0] if type(j) is tuple else j for j in self.join]

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):

        count, query = super().get_list(
            page, sort_column, sort_desc, search, filters,
            execute=False, page_size=page_size)

        if self.prefetch is None:
            return count, query

        if page_size:
            query = pw_prefetch(query, *self.prefetch)

            if execute:
                query = list(query.execute())

        return count, query

    def _get_list_value(self, context, model, name, column_formatters,
                        column_type_formatters, details_column_formatters=None):
        """
            Returns the value to be displayed.

            :param context:
                :py:class:`jinja2.runtime.Context` if available
            :param model:
                Model instance
            :param name:
                Field name
            :param column_formatters:
                column_formatters to be used.
            :param column_type_formatters:
                column_type_formatters to be used.
        """
        if (details_column_formatters and
                context.name in (self.details_template,
                                 self.details_modal_template)):

            column_fmt = details_column_formatters.get(name)
        else:
            column_fmt = None

        column_fmt = column_fmt or column_formatters.get(name)
        if column_fmt is not None:
            value = column_fmt(self, context, model, name)
        else:
            value = self._get_field_value(model, name)

        choices_map = self._column_choices_map.get(name, {})
        if choices_map:
            return choices_map.get(value) or value

        type_fmt = None
        for typeobj, formatter in column_type_formatters.items():
            if isinstance(value, typeobj):
                type_fmt = formatter
                break
        if type_fmt is not None:
            value = type_fmt(self, value)

        return value

    @contextfunction
    def get_list_value(self, context, model, name):
        """
            Returns the value to be displayed in the list view

            :param context:
                :py:class:`jinja2.runtime.Context`
            :param model:
                Model instance
            :param name:
                Field name
        """
        return self._get_list_value(
            context,
            model,
            name,
            self.column_formatters,
            self.column_type_formatters,
            self.details_column_formatters
        )

    @expose('/')
    def index_view(self, *args, **kwargs):
        if self.dynamic_filters:
            self._refresh_filters_cache()

        return super().index_view(*args, **kwargs)

    @expose('/ajax/count/')
    def count(self):
        query = self.get_query()

        if self._filters:
            for flt, flt_name, value in self._get_list_filter_args():
                f = self._filters[flt]

                query = self._handle_join(query, f.column, set())
                query = f.apply(query, f.clean(value))

        return str(query.count())


class AuthOnly(object):
    def is_accessible(self):
        return current_user.is_active and current_user.is_authenticated

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when
        a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))


class Secured(AuthOnly):
    def is_accessible(self):
        if not super(Secured, self).is_accessible():
            return False

        return (current_user.is_manager() or
                current_user.has_access(camel2snake(self.name)))

    def can_perform(self, action):
        if not super(Secured, self).is_accessible():
            return False

        return (current_user.is_manager() or
                current_user.can_perform(camel2snake(self.name), action))


class SecuredWithCategory(Secured):
    secure_category = None

    def is_accessible(self):
        return (super().is_accessible()
                or current_user.has_access(camel2snake(self.secure_category)))


class SecuredView(Secured, BaseModelView):
    action_permissions_mapping = None

    def _has_perm(self, action):
        return (current_user.is_manager()
                or current_user.can_perform(camel2snake(self.name), action))

    def _check_permission(self, action):
        if not self._has_perm(action):
            abort(403)

    @expose('/')
    def index_view(self, *args, **kwargs):
        if not self.is_accessible():
            abort(403)

        return super().index_view(*args, **kwargs)

    @expose('/details/')
    def details_view(self, *args, **kwargs):
        if self.can_view_details:
            self._check_permission('view_details')

        return super().details_view(*args, **kwargs)

    @expose('/new/', methods=('GET', 'POST'))
    def create_view(self, *args, **kwargs):
        if self.can_create:
            self._check_permission('create')

        return super().create_view(*args, **kwargs)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self, *args, **kwargs):
        if self.can_edit:
            self._check_permission('edit')

        return super().edit_view(*args, **kwargs)

    @expose('/delete/', methods=('POST',))
    def delete_view(self, *args, **kwargs):
        if self.can_delete:
            self._check_permission('delete')

        return super().delete_view(*args, **kwargs)

    @expose('/ajax/count/')
    def count(self, *args, **kwargs):
        if not hasattr(super(), 'count'):
            return abort(404)

        if not self.is_accessible():
            abort(403)

        return super().count(*args, **kwargs)

    @expose('/export/')
    def export(self):
        if self.can_export:
            self._check_permission('export')

        return super().export('csv')

    def get_list_row_actions(self):
        """
            Return list of row action objects, each is instance of
            :class:`~flask_admin.model.template.BaseListRowAction`
        """
        actions = []

        if self.can_view_details and self._has_perm('view_details'):
            if self.details_modal:
                actions.append(template.ViewPopupRowAction())
            else:
                actions.append(template.ViewRowAction())

        if self.can_edit and self._has_perm('edit'):
            if self.edit_modal:
                actions.append(template.EditPopupRowAction())
            else:
                actions.append(template.EditRowAction())

        if self.can_delete and self._has_perm('delete'):
            actions.append(template.DeleteRowAction())

        if self.action_permissions_mapping is not None:
            for index, action in enumerate(self.column_extra_row_actions or []):

                if self._has_perm(self.action_permissions_mapping[index]):
                    actions.append(action)
        else:
            actions += (self.column_extra_row_actions or [])

        return actions


class OnlySuperUser(AuthOnly):
    def is_accessible(self):
        return super().is_accessible() and current_user.is_superuser()


class ReadOnlyView(ModelView):
    can_edit = False
    can_create = False
    can_delete = False


class DetailView(ModelView):
    can_view_details = True
    details_modal = True


class CustomRowView(ModelView):
    list_template = 'admin/custom_list.html'

    row_class = None

    def get_list(self, page, sort_column, sort_desc, search, filters,
                 execute=True, page_size=None):

        count, query = super().get_list(
            page, sort_column, sort_desc, search, filters,
            execute=execute, page_size=page_size
        )

        if self.row_class is None:
            return count, query

        items = []
        query = query if page_size else query.iterator()
        for item in query:
            if callable(self.row_class):
                item._row_class = self.row_class(item)
            else:
                item._row_class = self.row_class

            items.append(item)

        return count, items


class SecuredMenuLink(AuthOnly, MenuLink):
    def is_accessible(self):
        if not super().is_accessible():
            return False

        return (current_user.is_manager() or
                current_user.has_access(camel2snake(self.category)) or
                current_user.has_access(camel2snake(self.name)))


class SecuredMenuCategory(Secured, MenuCategory):
    pass


class DefaultMethodView(MethodView):
    FormClass = None

    template = 'loyalty_client_form.html'
    template_args = {}

    api_method = None

    @staticmethod
    def to_table(data):
        return Markup(
            json2html.convert(json=data,
                              table_attributes='class="table json-table '
                                               'table-hover"')
        )

    def get(self, cls):
        return cls.render(self.template,
                          form=self.FormClass(),
                          **self.template_args)

    def post(self, cls):
        form = self.FormClass()
        if form.validate_on_submit():

            request_data, response_data = self.process_form(cls, form)

            request_data = self.to_table(request_data)
            response_data = self.to_table(response_data)

            flash('Success', category='success')
        else:
            request_data = response_data = None

        return cls.render(self.template,
                          form=form,
                          request_data=request_data,
                          response_data=response_data,
                          **self.template_args)

    def process_form(self, cls, form):
        form_data = copy.deepcopy(form.data)
        del form_data['csrf_token']

        return getattr(cls.client, self.api_method)(
            **{k: v for k, v in form_data.items() if v})