from django.db import transaction

def rollback_on_error(func):
    def f(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            transaction.rollback()
            raise
    return f
