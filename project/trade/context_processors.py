from project.members.models import Profile


def common(request):
    can_send_incomplete_game = True

    if not request.user.is_authenticated():
        can_send_incomplete_game = False
    else:
        try:
            profile = request.user.get_profile()
        except Profile.DoesNotExist:
            can_send_incomplete_game = False
        else:
            if not profile.has_game_perks():
                can_send_incomplete_game = False

    return {
        'rent_can_send_incomplete_game': can_send_incomplete_game,
    }
