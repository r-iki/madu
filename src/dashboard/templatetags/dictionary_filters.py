from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Gets an item from a dictionary using the key.
    Returns None if the key does not exist.
    """
    return dictionary.get(key)