from django.views.generic import TemplateView
from django.shortcuts import Http404, redirect

from project.catalog.models.items import Item
from project.tds.utils import is_eligible_for_free_trial


class IntroView(TemplateView):
    template_name = "index.html"

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect("catalog:index")
        return super(IntroView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        return {
            "popular_releases": Item.objects.hottest_selling()[:10],
            "free_trial": is_eligible_for_free_trial(self.request),
        }


class RentIntroView(TemplateView):
    pages_list = ["0", "1", "2", "3", "4", "5", "C1"]

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated() and request.user.get_profile().is_rental_active():
            return redirect("rent_intro2")
        return super(RentIntroView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        page_id = self.request.GET.get("pageid", "0")
        if page_id not in self.pages_list:
            raise Http404()
        self.page_id = page_id

        context = {}

        if self.page_id in ["0", "4", "C1"]:
            context.update({
                "popular_releases": Item.objects.hottest_selling()[:10],
            })
        if self.page_id == "0":
            context.update({
                "free_trial": is_eligible_for_free_trial(self.request),
            })
        if self.page_id == "1":
            context.update({
                "top_rentals": Item.objects.hottest_selling()[:10],
            })

        return context

    def get_template_names(self):
        template_name = "new_rent/landings/landing-%s.html" % self.page_id
        return [template_name]
