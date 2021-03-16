from flask import url_for

from wtforms.widgets import Select, HTMLString, html_params, PasswordInput


class ExtendedSelectWidget(Select):
    """
    Add support of choices with ``optgroup`` to the ``Select`` widget.
    """
    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        if self.multiple:
            kwargs['multiple'] = True
        html = ['<select %s>' % html_params(name=field.name, **kwargs)]
        for item1, item2 in field.choices:
            if isinstance(item2, (list,tuple)):
                group_label = item1
                group_items = item2
                html.append('<optgroup %s>' % html_params(label=group_label))
                for inner_val, inner_label in group_items:
                    html.append(self.render_option(inner_val,
                                                   inner_label,
                                                   inner_val in field.data))
                html.append('</optgroup>')
            else:
                val = item1
                label = item2
                html.append(self.render_option(val, label, val == field.data))
        html.append('</select>')
        return HTMLString(''.join(html))


class ExtendedSelect2Widget(ExtendedSelectWidget):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('data-role', u'select2')

        allow_blank = getattr(field, 'allow_blank', False)
        if allow_blank and not self.multiple:
            kwargs['data-allow-blank'] = u'1'

        return super(ExtendedSelect2Widget, self).__call__(field, **kwargs)


class PasswordWidget(PasswordInput):
    input_type = 'text'

    def __init__(self, url, icon=None, hide_value=True):
        super().__init__(hide_value=hide_value)

        self.url = url
        self.icon = icon or 'glyphicon glyphicon-lock'

    @staticmethod
    def _wrap_in_col(col_value, element, style=''):
        return HTMLString(f'<div class="col-md-{col_value}" style="{style}">'
                          f'{element}</div>')

    def __call__(self, field, **kwargs):
        if field.object_data is not None:
            field.flags.required = False

        input_el = super().__call__(field, **kwargs)

        url = url_for(self.url)

        js = (
            f'''(function() {{ 
            $.ajax({{
                url: '{url}',
                timeout: 3 * 1000
            }})
            .done(function( data ) {{
                $('#{field.id}').val(data);
            }})
            .fail(function() {{
                alert('Cannot generate');
            }}); 
            }})()'''
        )

        icon_el = (f'<span class="{self.icon}" '
                   f'title="Generate" '
                   f'style="font-size: x-large; '
                   f'vertical-align: -webkit-baseline-middle; '
                   f'cursor: pointer;" '
                   f'onclick="{js}">'
                   f'</span>')

        return HTMLString(
            '<div class="row" style="margin: 0;" >' +
            self._wrap_in_col(11, input_el, style='padding-left: 0;') +
            self._wrap_in_col(1, icon_el) +
            '</div>'
        )
