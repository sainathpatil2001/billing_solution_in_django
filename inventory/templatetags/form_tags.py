from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css_class):
    if field.field.widget.__class__.__name__ == 'CheckboxInput':
        return field.as_widget(attrs={'class': f'form-check-input {css_class}'})
    return field.as_widget(attrs={'class': css_class}) 