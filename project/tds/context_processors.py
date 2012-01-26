from project.tds.utils import is_eligible_for_free_trial


def free_trial(request):
    return {
        "eligible_for_free_trial": is_eligible_for_free_trial(request),
    }
