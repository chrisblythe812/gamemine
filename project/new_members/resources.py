from django.conf.urls.defaults import url

from tastypie.resources import ModelResource, Resource
from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.authorization import Authorization
from tastypie.bundle import Bundle

from project.new_rent.models import MemberRentalPlan
from project.new_rent.models import RentalPlan


class DjangoAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        if request.user.is_authenticated():
            return True

        return False


class RentalPlanResource(Resource):
    pk = fields.IntegerField(attribute='pk')
    first_payment_amount = fields.DecimalField(attribute='first_payment_amount')
    thereafter_payments_amount = fields.DecimalField(attribute='thereafter_payments_amount', null=True)
    out_per_month = fields.IntegerField(attribute="out_per_month", null=True)
    games_allowed = fields.IntegerField(attribute="games_allowed")

    class Meta:
        resource_name = 'rental_plan'
        object_class = RentalPlan
        authentication = DjangoAuthentication()

    def get_resource_uri(self, bundle_or_obj):
        kwargs = {
            'resource_name': self._meta.resource_name,
        }

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.pk
        else:
            kwargs['pk'] = bundle_or_obj.pk

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        return self._build_reverse_url("api_dispatch_detail", kwargs=kwargs)

    def get_object_list(self, request):
        return RentalPlan.objects.all()

    def obj_get_list(self, request=None, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(request)

    def obj_get(self, request=None, **kwargs):
        return RentalPlan.objects.get(pk=int(kwargs['pk']))


class MemberRentalPlanResource(ModelResource):
    rental_plan = fields.ForeignKey(RentalPlanResource, "rental_plan", full=True)

    class Meta:
        queryset = MemberRentalPlan.objects.all()
        resource_name = 'member_rental_plan'
        fields = ["next_payment_amount", "status", "rental_plan"]
        authentication = DjangoAuthentication()

    def apply_authorization_limits(self, request, object_list):
        # Just to be consistent, we don't realy need this
        return object_list.filter(user=request.user)

    def override_urls(self):
        return [
            url(r"^(?P<resource_name>%s)/$" % self._meta.resource_name, self.wrap_view('dispatch_detail')),
        ]

    def obj_get(self, request=None, **kwargs):
        return self.obj_get_list(request).get(user=request.user)
