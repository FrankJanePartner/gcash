# accounts/templatetags/form_tags.py
from django import template

register = template.Library()

@register.filter
def render_with_class(form):
    output = []
    for field in form:
        output.append(f'''
        <p class="input-box">
            {field.label_tag()}
            {field}
            {field.errors}
        </p>
        ''')
    return '\n'.join(output)
