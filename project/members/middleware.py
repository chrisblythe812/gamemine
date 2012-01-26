from models import Profile


class ProfileMiddleware(object):
    def process_request(self, request):
        if request.user.is_authenticated():
            try:
                request.user.get_profile()
            except Profile.DoesNotExist:
                Profile(user=request.user).save()
