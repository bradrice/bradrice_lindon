from django import template

register = template.Library()

@register.filter(name='currency')
def currency(value, currency_code="USD"):
    try:
        # Example: Format as $1,234.56
        if currency_code == "USD":
            return f"${value:,.2f}"
        # Add other currency codes as needed
        elif currency_code == "EUR":
            return f"€{value:,.2f}"
        else:
            return f"{value:,.2f} {currency_code}"
    except (ValueError, TypeError):
        return value
