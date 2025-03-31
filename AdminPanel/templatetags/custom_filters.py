import base64
from django import template

register = template.Library()

@register.filter
def encode_base64(value):
    """Encode a string to base64, useful for passing special characters in URLs"""
    if value is None:
        return ''
    return base64.b64encode(str(value).encode('utf-8')).decode('utf-8') 