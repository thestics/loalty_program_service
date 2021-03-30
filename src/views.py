import copy
from itertools import groupby

from flask import flash, abort, Markup, redirect, url_for, current_app, request
from peewee import fn
from flask.views import MethodView
from flask_security.utils import hash_password
from flask_admin.contrib.peewee.filters import FilterInList
from flask_admin import AdminIndexView, expose_plugview, expose, BaseView
from flask_admin.babel import gettext
from flask_admin.form import rules
from flask_admin.model.helpers import prettify_name
from flask_admin.model.template import EndpointLinkRowAction
from flask_admin.form.widgets import Select2Widget
from wtfpeewee.fields import SelectMultipleQueryField
from wtforms.fields import StringField
from wtforms.validators import Optional, InputRequired, Email

from common.clients.loyalty import LoyaltyClient
from common.views import (ReadOnlyView, DetailView, AuthOnly, ModelView,
                          CustomRowView, SecuredView, OnlySuperUser,
                          SecuredMenuLink, SecuredMenuCategory,
                          SecuredWithCategory, DefaultMethodView)
from common.formatters import (url_formatter, readable_number_formatter,
                               datetime_formatter, json_formatter,
                               colored_row_formatter, blockchain_url_formatter)
from common.validators import unique_validator, required_on_create, validate_config
from common.utils import camel2snake, snake2camel, generate_password
from common.widgets import PasswordWidget, ExtendedSelect2Widget
from common.fields import ExtendedSelectField, PrettyJsonField

from src.forms import (CustomerCreationForm, PurchaseForm)
from models.loyalty import (DiscountLevel, Customer, ErrorLog)
from models.admin import (User, Role, UserRoles, user_datastore)


class IndexView(AuthOnly, AdminIndexView):
    pass


class DiscountLevelView(SecuredView, DetailView, CustomRowView):
    column_list = ('name', 'minimal_amount', 'created', 'extra_data')
    column_sortable_list = ('name', 'minimal_amount', 'created')
    column_filters = (
        'name',
        'minimal_amount',
        'created'
    )

    dynamic_filters = True
    column_formatters = {
        'extra_data': json_formatter,
        'created': datetime_formatter()
    }


class CustomerView(SecuredView, DetailView, CustomRowView):
    column_list = ('id', 'name', 'phone', 'amount_of_purchases',
                   'discount_level', 'birthday', 'address',
                   'created', 'updated')
    column_sortable_list = ('id', 'name', 'birthday', 'created')
    column_default_sort = ('id', True)
    column_filters = (
        'name',
        'phone',
        # Customer.discount_level,
        'birthday',
        'amount_of_purchases',
        'created'
    )

    join = (DiscountLevel, )

    dynamic_filters = True
    column_formatters = {
        'created': datetime_formatter()
    }


class UserView(OnlySuperUser, DetailView):
    edit_modal = True
    create_modal = True
    can_delete = False

    column_list = ('id', 'email', 'active', 'last_login_at',
                   'current_login_at',
                   'login_count', 'roles', 'created')
    column_details_exclude_list = ('password',)

    column_sortable_list = ('id', 'last_login_at', 'current_login_at',
                            'login_count', 'created')
    column_default_sort = ('created', True)

    column_formatters = {
        'last_login_at': datetime_formatter(to_local_tz=True),
        'current_login_at': datetime_formatter(to_local_tz=True),
        'created': datetime_formatter(to_local_tz=True),
        'roles': lambda v, c, m, p: ', '.join(r.name for r in m.roles)
    }

    form_columns = ('email', 'password', 'active', 'roles')

    form_create_rules = (
        rules.FieldSet(('email', 'password', 'active', 'roles')),
    )

    form_edit_rules = (
        rules.FieldSet(('password', 'active', 'roles')),
    )

    form_extra_fields = {
        'roles': SelectMultipleQueryField(
            query=(Role
                   .select()
                   .where(Role.name != 'superuser')
                   .order_by(Role.name)),
            get_label=lambda m: m.name,
            validators=[Optional()],
            widget=Select2Widget(multiple=True)
        )
    }

    form_args = {
        'email': dict(validators=[InputRequired(),
                                  unique_validator(User.email)]),
        'password': dict(widget=PasswordWidget('user.generate_pass'),
                         validators=[Optional(), required_on_create])
    }

    allowed_roles = ('superuser',)

    prefetch = (UserRoles.select(UserRoles, Role).join(Role),)

    exclude_from_log = [User.password]

    def get_list(self, *args, **kwargs):
        count, query = super().get_list(*args, **kwargs)

        return count, [item for item in query if not item.is_superuser()]

    def create_model(self, form):
        try:
            model = user_datastore.create_user(**form.data)
        except Exception as ex:
            if not self.handle_view_exception(ex):
                flash(gettext('Failed to create record. %(error)s',
                              error=str(ex)), 'error')
            return False
        else:
            self.after_model_change(form, model, True)

        return model

    def update_model(self, form, model):
        if model.is_superuser():
            abort(403)

        user_roles = set(model.get_roles())
        form_roles = set(form.roles.data) if form.roles.raw_data else set()

        if 'superuser' in (role.name for role in form_roles):
            abort(403)

        for role in form_roles - user_roles:
            user_datastore.add_role_to_user(model, role)

        for role in user_roles - form_roles:
            user_datastore.remove_role_from_user(model, role)

        if not form.password.data:
            form.password.data = model.password
        else:
            form.password.data = hash_password(form.password.data)

        return super().update_model(form, model)

    def on_form_prefill(self, form, id):
        form.roles.data = (
            Role
                .select(Role.id,
                        Role.name)
                .join(UserRoles)
                .where((UserRoles.user == id) & (Role.name != 'superuser'))
                .order_by(Role.name)
        )

    @expose('/ajax/generate_password')
    def generate_pass(self):
        if not self.is_accessible():
            abort(403)

        return generate_password()


class RolesView(OnlySuperUser, ModelView):
    edit_modal = True
    create_modal = True

    form_edit_rules = (
        rules.FieldSet(('description', 'permissions')),
    )

    column_sortable_list = ('id',)
    column_default_sort = 'name'

    allowed_roles = ('superuser',)

    form_overrides = {
        'permissions': ExtendedSelectField
    }

    form_args = {
        'name': {
            'validators': [InputRequired(), unique_validator(Role.name)]
        }
    }

    @staticmethod
    def get_permission_choices():
        choices = {}
        for view in get_views(exclude=(RolesView, UserView)):
            view_choices = []

            view_id = camel2snake(view.name)

            get_choice = lambda action: (
                '{}__{}'.format(view_id, camel2snake(action)),
                f'{action} {view.name}'
            )

            view_choices.append(get_choice('View'))

            for operation in ('create', 'edit', 'delete', 'view_details', 'export'):
                if getattr(view, 'can_' + operation):
                    view_choices.append(get_choice(snake2camel(operation)))

            if hasattr(view, 'additional_permissions'):
                for perm in view.additional_permissions:
                    view_choices.append(get_choice(perm))

            choices[view.name] = view_choices

        for link in get_links():
            if link.category not in choices:
                choices[link.category] = (
                    (camel2snake(link.category) + '__view',
                     'View ' + link.category),
                )

        return sorted(choices.items(), key=lambda item: item[0].capitalize())

    def __init__(self, *args, **kwargs):
        self.form_args = self.form_args or dict()
        self.form_args['permissions'] = dict(
            widget=ExtendedSelect2Widget(multiple=True),
            choices=self.get_permission_choices()
        )

        super().__init__(*args, **kwargs)

    def is_action_allowed(self, name):
        if name == 'delete':
            return False

        return super(RolesView, self).is_action_allowed(name)

    @staticmethod
    def _group_permissions(permissions):
        splited = [item.split('__', 1) for item in permissions]

        permissions = {}
        for view_id, actions in groupby(splited, key=lambda item: item[0]):
            permission = []
            for action in actions:
                try:
                    action = action[1]
                except IndexError:
                    action = action[0]

                permission.append(action)

            permissions[view_id] = permission

        return permissions

    def on_model_change(self, form, model, is_created):
        if is_created:
            model.permissions = self._group_permissions(form.permissions.data)

    def update_model(self, form, model):
        if model.name in ('superuser', 'manager'):
            abort(403)

        form_permissions = self._group_permissions(form.permissions.data)
        model_permissions = model.permissions

        for view_id in set(model_permissions) - set(form_permissions):
            del model_permissions[view_id]

        for view_id, actions in form_permissions.items():
            model_actions = model_permissions.setdefault(view_id, list())

            for action in set(actions) - set(model_actions):
                model_actions.append(action)

            for action in set(model_actions) - set(actions):
                model_actions.remove(action)

            if not model_actions:
                del model_permissions[view_id]

        form.permissions.data = model_permissions

        return super().update_model(form, model)

    def delete_model(self, model):
        if model.name in ('superuser', 'manager'):
            abort(403)

        return super().delete_model(model)

    def on_form_prefill(self, form, id):
        permissions = (
            Role
                .select(Role.permissions)
                .where(Role.id == id).first()
        ).permissions

        form.permissions.data = sorted([
            f'{view_id}__{action}'
            for view_id, actions in permissions.items()
            for action in actions
        ])


class ErrorLogView(SecuredView, DetailView, ReadOnlyView):
    column_exclude_list = ('request_data', 'traceback')

    column_sortable_list = ('id', 'created')
    column_default_sort = ('created', True)

    column_filters = (
        'id',
        'request_ip',
        'request_url',
        'request_method',
        'error',
        'created'
    )

    column_formatters = {
        'created': datetime_formatter(),
        'request_data': json_formatter
    }


class LoyaltyClientView(SecuredWithCategory, BaseView):
    secure_category = 'API'

    client = LoyaltyClient()

    @expose('/')
    def index(self):
        return abort(404)

    @expose_plugview('/new_customer')
    class NewCustomerView(DefaultMethodView):
        FormClass = CustomerCreationForm

        template_args = {
            'form_title': 'Customer Creation'
        }

        api_method = 'create_customer'

        def process_form(self, cls, form):
            form_data = copy.deepcopy(form.data)
            del form_data['csrf_token']
            amount = form_data['amount_of_purchases']
            discount_id = DiscountLevel.get_by_amount(amount)
            form_data['discount_level'] = discount_id if discount_id else 1

            return getattr(cls.client, self.api_method)(
                **{k: v for k, v in form_data.items() if v})

    @expose_plugview('/purchase')
    class PurchaseView(DefaultMethodView):
        FormClass = PurchaseForm

        template_args = {
            'form_title': 'Customer Creation'
        }

        api_method = 'create_customer'

        def process_form(self, cls, form):
            form_data = copy.deepcopy(form.data)
            customer_card_id = form_data['client_card_id']
            try:
                purchase_sum = int(form_data['purchase_sum'])
            except:
                return redirect(url_for('API/purchase'))

            try:
                customer = Customer.get_for_update(customer_card_id)
            except:
                return redirect(url_for('API/purchase'))
            discount = customer.discount_level
            purchase_sum -= purchase_sum * discount.discount_percent






def get_views(exclude=tuple()):
    mapping = (
        (DiscountLevelView, DiscountLevel),
        (UserView, User),
        (RolesView, Role),
        (CustomerView, Customer),
        (ErrorLogView, ErrorLog)
    )

    for view, model in mapping:
        if view in exclude:
            continue

        yield view(model)


def get_links():
    links = []

    client_views = (
        ('Customer', 'NewCustomerView'),
    )

    category = SecuredMenuCategory(name='API')

    for link_name, view in client_views:
        links.append(
            SecuredMenuLink(
                link_name,
                category=category.name,
                endpoint=f'loyaltyclientview.{view}')
        )

    return links


def init_views(admin):
    admin.add_views(*get_views())

    admin.app.register_blueprint(
        LoyaltyClientView().create_blueprint(admin))

    admin.add_links(*get_links())
