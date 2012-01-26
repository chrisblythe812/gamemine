from django.conf.urls.defaults import *

from project.new_rent.views import ChangeRentPlanWizard, rent_sign_up_wizard_factory


urlpatterns = patterns("",
   url(r"^Rent/Change-Plan/$", ChangeRentPlanWizard.as_view(), name="change_plan"),
   url(r"^Rent/SignUp/$", rent_sign_up_wizard_factory, name="sign_up"),
   url(r"^Rent/SignUp/Plan/(?P<rental_plan_slug>\w+)/$", rent_sign_up_wizard_factory, name="sign_up"),
)
