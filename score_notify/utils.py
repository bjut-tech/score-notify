from datetime import date


def get_current_term():
    now = date.today()
    year = now.year
    month = now.month

    return {
        'year': year - 1 if month < 8 else year,
        'term': 2 if 2 <= month < 8 else 1
    }
