from datetime import date


def get_current_term() -> dict:
    now = date.today()
    year = now.year
    month = now.month

    return {
        'year': year - 1 if month < 8 else year,
        'term': 2 if 2 <= month < 8 else 1
    }


def get_term_before(term: dict) -> dict:
    if term['term'] == 1:
        return {
            'year': term['year'] - 1,
            'term': 2
        }
    else:
        return {
            'year': term['year'],
            'term': 1
        }
