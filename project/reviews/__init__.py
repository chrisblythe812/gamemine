def get_model():
    from project.catalog.models import Review
    return Review

def get_form():
    from forms import ReviewForm
    return ReviewForm
