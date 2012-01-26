from django.conf.urls.defaults import *
from tastypie.api import Api

from project.new_members.resources import MemberRentalPlanResource, RentalPlanResource

v1_api = Api(api_name="v1")
v1_api.register(MemberRentalPlanResource())
v1_api.register(RentalPlanResource())

urlpatterns = patterns("",
    (r"^api/", include(v1_api.urls)),
)
