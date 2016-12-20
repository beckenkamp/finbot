import re

from datetime import date

months = [
    'janeiro',
    'fevereiro',
    'março',
    'abril',
    'maio',
    'junho',
    'julho',
    'agosto',
    'setembro',
    'outubro',
    'novembro',
    'dezembro'
]

def get_month(raw):
    """
    Return the month from a raw string
    """
    for index, month in enumerate(months, start=1):
        if month in raw.lower():
            return index
    return None

def get_date(raw):
    """
    Return date object from a raw string
    """
    numbers = re.findall('\d*\d+', raw)

    month = None
    year = None
    day = None

    month = get_month(raw)

    # Day is always the first number finded
    if len(numbers) > 0:
        day = int(numbers[0])

    if len(numbers) > 1:
        if not month:
            month = int(numbers[1])
        else:
            year = int(numbers[1])

    if len(numbers) > 2:
        year = int(numbers[2])

    if not day:
        day = date.today().day
    if not month:
        month = date.today().month
    if not year:
        year = date.today().year

    return date.today().replace(year=year, month=month, day=day)
