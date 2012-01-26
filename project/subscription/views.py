from django import forms
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.shortcuts import redirect
from django.template.context import RequestContext
from django.template.loader import render_to_string

from django_snippets.views.json_response import JsonResponse
from django_snippets.views import simple_view

from project.utils.mailer import mail
from models import Subscriber


def subscribe(request):
    class SubscriptionForm(forms.Form):
        email = forms.EmailField()
    form = SubscriptionForm(request.GET)
    if form.is_valid():
        subscriber = Subscriber()
        subscriber.email = form.cleaned_data['email']
        subscriber.campaign_cid = request.campaign_id
        subscriber.save()
        
        ctx = {
            'email': subscriber.email,
            'guid': subscriber.guid,
            'confirmation_url': 'http://%s%s' % (
                Site.objects.get_current().domain,
                reverse('subscription:confirm', kwargs={'guid': subscriber.guid}),
            ), 
        }
        mail(subscriber.email, 'subscription/confirmation_email.html', ctx, subject='GameMine. E-mail confirmation')

        return JsonResponse({'success': True})
    return JsonResponse({'success': False})


@simple_view('subscription/thankyou.html', 
             cookies=[{'key': 'subscription-done', 'value': True}])
def thankyou(request):
    if not request.is_ajax():
        return redirect('/')
    return {
        'show_title': request.GET.get('show_title'),
        'refresh_after_dialog_close': True,
    }


@simple_view('subscription/confirmed.html')
def confirm(request, guid):
    try:
        subscriber = Subscriber.objects.get(guid=guid)
    except:
        return redirect('catalog:index')
    subscriber.active = True
    subscriber.save()
    return {
        'email': subscriber.email,
    }


@simple_view('subscription/signup.html')
def signup(request):
    class Form(forms.Form):
        email = forms.EmailField()
        email2 = forms.EmailField(label='Verify Email Address', required=False)
        
        def clean_email2(self):
            d1 = self.cleaned_data.get('email')
            d2 = self.cleaned_data.get('email2')
            if d1 and d2 != d1:
                raise forms.ValidationError('The email you entered do not match.')
            return d2
    
    if not request.is_ajax():
        return redirect('/')
    if request.method == 'POST':
        form = Form(request.POST)
        if form.is_valid():
            return JsonResponse({'goto_url': reverse('subscription:thankyou') + '?show_title=True'})
        result = render_to_string('subscription/signup.html', {
                'form': form,
            }, RequestContext(request))
        return JsonResponse({'form': result})
    return {'form': Form()}
