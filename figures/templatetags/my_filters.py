# my_app/templatetags/my_filters.py
from django import template

register = template.Library()

@register.filter
def to_string(value):
    return str(value)

@register.filter
def get_type(value):
    return type(value).__name__


@register.filter(name='inches_and_cm')
def inches_an_cm(value):
    cm = value * 2.54
    inches = f"{value:.2f}"

    return f"{inches}\" ({cm:.2f} cm)"
