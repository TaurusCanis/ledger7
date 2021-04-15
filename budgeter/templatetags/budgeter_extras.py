from django import template
import datetime

register = template.Library()

@register.filter
def get_month(date_day):
    print("date_day: ", date_day)
    today = datetime.date.today()
    if date_day >= today.day:
        due_date = datetime.date(today.year, today.month, date_day)
    else:
        next_month = today.month + 1
        if next_month > 12:
            next_month = 1
        due_date = datetime.date(today.year, next_month, date_day)
    print(today, due_date)
    return due_date

@register.filter
def to_class_name(value):
    return value.__class__.__name__

@register.filter
def format_date(value):
    print("value: ", value, " type: ", type(value))
    return str(value)

@register.filter
def get_class(value):
    print("VALUE: ", value)
    return value.__class__.__name__
