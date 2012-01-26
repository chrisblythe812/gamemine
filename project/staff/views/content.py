from django import forms
from django.shortcuts import get_object_or_404, redirect
from django_snippets.views import simple_view
from django_snippets.views import paged

from project.banners.models import FeaturedGame, CatalogBanner, ListPageBanner
from project.staff.models import MuzeUpdateLog
from project.members.models import Campaign
from project.subscription.models import Subscriber
from project.offer_term.models import OfferTerm


def featured_games(request, **kwargs):
    return {
        'title': 'Featured Games',
        'banners': FeaturedGame.objects.all().order_by('category'),
    }, None

BaseFeaturedGameForm = forms.models.modelform_factory(FeaturedGame)

class FeaturedGameForm(BaseFeaturedGameForm):
    def __init__(self, *args, **kwargs):
        super(FeaturedGameForm, self).__init__(*args, **kwargs)
        self.fields['game'].label_from_instance = self.game_label_from_instance
        self.fields['game'].widget = forms.TextInput()

    def game_label_from_instance(self, obj):
        return u'%s - %s (%s)' % (obj.id, obj.short_name, obj.category)

@simple_view('staff/content/featured_game.html')
def featured_game_add(request, **kwargs):
    if request.method == 'POST':
        form = FeaturedGameForm(request.POST, request.FILES)
        if form.is_valid():
            fg = form.save()
            return redirect('staff:content_featured_game_edit', fg.id)
    else:
        form = FeaturedGameForm()

    return {
        'title': 'Add Featured Game',
        'form': form,
    }

@simple_view('staff/content/featured_game.html')
def featured_game_edit(request, id=None, **kwargs):
    fg = get_object_or_404(FeaturedGame, id=id)

    if request.method == 'POST':
        form = FeaturedGameForm(request.POST, request.FILES, instance=fg)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Featured-Games')
    else:
        form = FeaturedGameForm(instance=fg)

    return {
        'title': 'Featured Game',
        'banner': fg,
        'form': form,
    }

def featured_game_delete(request, id=None, **kwargs):
    fg = get_object_or_404(FeaturedGame, id=id)
    fg.delete()
    return redirect('staff:page', 'Content/Featured-Games')



def banners__browse_games(request, **kwargs):
    return {
        'title': 'Browse Games',
        'banners': CatalogBanner.objects.all(),
    }, None


@simple_view('staff/content/banners/browse_game.html')
def edit_browse_game_banner(request, id):
    b = get_object_or_404(CatalogBanner, id=id)

    CatalogBannerForm = forms.models.modelform_factory(CatalogBanner)

    if request.method == 'POST':
        form = CatalogBannerForm(request.POST, request.FILES, instance=b)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Banners/Browse-Games')
    else:
        form = CatalogBannerForm(instance=b)

    return {
        'title': 'Featured Game',
        'banner': b,
        'form': form,
    }


@simple_view('staff/content/banners/browse_game.html')
def add_browse_game_banner(request):
    CatalogBannerForm = forms.models.modelform_factory(CatalogBanner)

    if request.method == 'POST':
        form = CatalogBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Banners/Browse-Games')
    else:
        form = CatalogBannerForm()

    return {
        'title': 'Featured Game',
        'form': form,
    }


def delete_browse_game_banner(request, id):
    b = get_object_or_404(CatalogBanner, id=id)
    b.delete()
    return redirect('staff:page', 'Content/Banners/Browse-Games')


def banners__lists(request, **kwargs):
    return {
        'title': 'Lists',
        'banners': ListPageBanner.objects.all(),
    }, None


@simple_view('staff/content/banners/lists_banner.html')
def edit_lists_banner(request, id):
    b = get_object_or_404(ListPageBanner, id=id)

    ListPageBannerForm = forms.models.modelform_factory(ListPageBanner)

    if request.method == 'POST':
        form = ListPageBannerForm(request.POST, request.FILES, instance=b)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Banners/Lists')
    else:
        form = ListPageBannerForm(instance=b)

    return {
        'title': 'Lists Banner',
        'banner': b,
        'form': form,
    }


@simple_view('staff/content/banners/browse_game.html')
def add_lists_banner(request):
    ListPageBannerForm = forms.models.modelform_factory(ListPageBanner)

    if request.method == 'POST':
        form = ListPageBannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Banners/Lists')
    else:
        form = ListPageBannerForm()

    return {
        'title': 'Lists',
        'form': form,
    }


def delete_lists_banner(request, id):
    b = get_object_or_404(ListPageBanner, id=id)
    b.delete()
    return redirect('staff:page', 'Content/Banners/Lists')


def muze_db__updates(request, **kwargs):
    return {
        'title': 'Muze DB: Updates',
        'paged_qs': MuzeUpdateLog.objects.all(),
    }, None, ('rows', )



@simple_view('staff/content/campaigns.html')
def campaigns(request, **kwargs):
    campaigns = Campaign.objects.all()
    return {
        'title': 'Campaigns',
        'campaigns': campaigns,
    }


@simple_view('staff/content/campaign_form.html')
def add_campaign(request):
    CampaignForm = forms.models.modelform_factory(Campaign)

    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Campaigns')
    else:
        form = CampaignForm()
    return {
        'title': 'Add Campaign',
        'form': form,
    }

@simple_view('staff/content/campaign_form.html')
def edit_campaign(request, cid):
    campaign = get_object_or_404(Campaign, pk=cid)
    CampaignForm = forms.models.modelform_factory(Campaign)

    if request.method == 'POST':
        form = CampaignForm(request.POST, instance=campaign)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/Campaigns')
    else:
        form = CampaignForm(instance=campaign)
    return {
        'title': 'Edit Campaign',
        'form': form,
    }

def del_campaign(request, cid):
    campaign = get_object_or_404(Campaign, pk=cid)
    campaign.delete()
    return redirect('staff:page', 'Content/Campaigns')

@simple_view('staff/content/subscribers.html')
@paged('subscribers', 50)
def subscribers(request, **kwargs):
    return {
        'title': 'Subscribers',
        'paged_qs': Subscriber.objects.all(),
    }


@simple_view('staff/content/offer_terms.html')
def offer_terms(request):
    offer_terms = OfferTerm.objects.all()
    to_render = dict(title="Offer Terms", offer_terms=offer_terms)
    return to_render

@simple_view('staff/content/offer_term_form.html')
def add_offer_term(request):
    OfferTermForm = forms.models.modelform_factory(OfferTerm)
    if request.method == 'POST':
        form = OfferTermForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/OfferTerms')
    else:
        form = OfferTermForm()
    to_render = dict(title="Offer Terms", form=form)
    return to_render

@simple_view('staff/content/offer_term_form.html')
def edit_offer_term(request, id):
    offer_term = get_object_or_404(OfferTerm, pk=id)
    OfferTermForm = forms.models.modelform_factory(OfferTerm)
    if request.method == 'POST':
        form = OfferTermForm(request.POST, instance=offer_term)
        if form.is_valid():
            form.save()
            return redirect('staff:page', 'Content/OfferTerms')
    else:
        form = OfferTermForm(instance=offer_term)
    to_render = dict(title="Offer Terms", form=form)
    return to_render

def del_offer_term(request, id):
    offer_term = get_object_or_404(OfferTerm, pk=id)
    offer_term.delete()
    return redirect('staff:page', 'Content/OfferTerms')

