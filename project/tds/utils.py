__all__ = ["is_eligible_for_free_trial"]

FREE_TRIAL_CIDS = ["10", "14", "15"]


def is_eligible_for_free_trial(request):
    if getattr(request, "campaign_id", None) in FREE_TRIAL_CIDS:
        return True
    return False
