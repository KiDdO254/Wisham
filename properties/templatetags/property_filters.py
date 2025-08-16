from django import template

register = template.Library()

@register.filter
def get_primary_image(property):
    """Get the primary image for a property"""
    try:
        return property.images.filter(is_primary=True).first()
    except:
        return None
