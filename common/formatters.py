from flask import url_for, Markup, current_app
from json2html import json2html
import pytz


def url_formatter(endpoint,
                  sort_param,
                  name_column=None,
                  get_sort_expression=None):
    def get(model, path):

        column = getattr(model, path.pop(0))

        if path:
            return get(column, path)

        return column

    def _url_formatter(view, context, model, name):
        field_value = getattr(model, name)
        if field_value:

            if get_sort_expression is not None:
                expression = get_sort_expression(model, name)
            else:
                expression = field_value

            markup_string = "<a href={url}>{name}</a>".format(
                url=url_for(endpoint, **{sort_param: expression}),
                name=(get(model, name_column.split('.'))
                      if name_column else field_value)
            )

            return Markup(markup_string)

    return _url_formatter


class AbortUrlCreation(Exception):
    pass


def external_url_formatter(url, get_name=None):
    def _external_url_formatter(view, context, model, name):
        field_value = getattr(model, name)

        if field_value is not None:
            url_name = (
                get_name(model, name)
                if get_name is not None
                else field_value

            )
            if callable(url):
                try:
                    endpoint = url(model, name)
                except AbortUrlCreation:
                    return url_name
            else:
                endpoint = url

            markup_string = '<a href={url} target="_blank">{name}</a>'.format(
                url=endpoint,
                name=url_name
            )

            return Markup(markup_string)

    return _external_url_formatter


def blockchain_url_formatter(entity_type, get_currency_config, get_name=None):
    def generate_url(model, name):
        config = get_currency_config(model)

        if not config.get('url_admin_template'):
            raise AbortUrlCreation()

        blockchain_url = config['url_admin_template'][entity_type]

        return (
            blockchain_url.format(entity_id=getattr(model, name))
        )

    return external_url_formatter(generate_url, get_name=get_name)


def readable_number_formatter(view, context, model, name):
    value = getattr(model, name)
    if value:
        return (
            '{number:.{precision}f}'
                .format(number=float(value),
                        precision=8)
                .rstrip('0')
                .rstrip('.')
        )


def datetime_formatter(f="%Y-%m-%d %H:%M:%S", to_local_tz=False):
    def _truncate_datetime(view, context, model, name):
        value = getattr(model, name)

        if value:
            if to_local_tz:
                value = value.astimezone(pytz.timezone(
                    current_app.config['TZ']))

            return value.strftime(f)

    return _truncate_datetime


def json_formatter(view, context, model, name):
    value = getattr(model, name)

    if value:
        return Markup(
            json2html.convert(json=value,
                              table_attributes='class="table json-table '
                                               'table-hover table-sm"')
        )


def colored_row_formatter(column, *colors_mapping, default=''):
    def get_class(c):
        for expression, color in colors_mapping:
            if expression(c):
                return color

        return default

    def _colored_formatter(view, item):
        return get_class(getattr(item, column))

    return _colored_formatter
