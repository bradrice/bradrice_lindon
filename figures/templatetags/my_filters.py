# my_app/templatetags/my_filters.py
from django import template

register = template.Library()

@register.filter
def to_string(value):
    return str(value)

@register.filter
def get_type(value):
    return type(value).__name__
