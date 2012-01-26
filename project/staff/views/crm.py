from django.shortcuts import get_object_or_404, redirect
from django import forms
from django.db import transaction
from django.http import Http404

from django_snippets.views import simple_view

from project.crm.models import FeedbackifyFeedback, Reply, PersonalGameTicket,\
    CASE_STATUSES_PUBLIC, CaseStatus
from project.claims.models import Claim, ClaimType,\
    GamemineNotRecieveTradeGameClaim, WrongTradeValueCreditClaim,\
    MailerIsEmptyClaim, GamemineNotReceiveGameClaim, GameIsDamagedClaim,\
    DontReceiveClaim, WrongGameClaim


def feedbacks(self, **kwargs):
    feedbacks = FeedbackifyFeedback.objects.all()
    return {
        'title': 'CRM: Feedbacks',
        'paged_qs': feedbacks,
    }, None, ('feedbacks', 50)


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Reply
        fields = ('status', 'message')

    status = forms.ChoiceField(choices=CASE_STATUSES_PUBLIC)


class FeedbackStatusForm(forms.ModelForm):
    class Meta:
        model = FeedbackifyFeedback
        fields = ('status', )
        
    status = forms.ChoiceField(choices=CASE_STATUSES_PUBLIC)


@simple_view('staff/crm/feedback_details.html')
def feedback_details(request, id):
    feedback = get_object_or_404(FeedbackifyFeedback, id=id)
    if request.method == 'POST':
        status_form = FeedbackStatusForm(request.POST, instance=feedback)
        if status_form.is_valid():
            status_form.save()
        return redirect('staff:feedback_details', feedback.id)
    status_form = FeedbackStatusForm(instance=feedback)
    replies = feedback.get_replies()
    reply_form = ReplyForm()
    return {
        'title': 'Feedback details',
        'page_class': 'crm-feedback-details',
        'feedback': feedback,
        'status_form': status_form,
        'replies': replies,
        'reply_form': reply_form,
    }


@transaction.commit_on_success
def reply_to_feedback(request, id):
    if request.method == 'POST':
        feedback = get_object_or_404(FeedbackifyFeedback, id=id)
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(False)
            reply.case = feedback
            reply.mailed_to = feedback.get_email()
            reply.save()
            feedback.status = reply.status
            feedback.save()
            reply.send_email()
    return redirect('staff:feedback_details', id)


def tickets__personal_games(request, **kwargs):
    return {
        'title': 'Tickets: Personal Games',
        'paged_qs': PersonalGameTicket.objects.all(),
    }, None, ('tickets', 50)


@simple_view('staff/crm/tickets/personal_game_details.html')
def personal_game_details(request, id):
    ticket = get_object_or_404(PersonalGameTicket, id=id)
    return {
        'title': 'Ticket details',
        'page_class': 'crm-personal-game-details',
        'ticket': ticket,
    }


def tickets__shipping_problems(request, **kwargs):
    return {
        'title': 'Tickets: Shipping Problems',
        'paged_qs': Claim.objects.all().order_by('-date'),
    }, None, ('tickets', 50)


@simple_view('staff/crm/claims/details.html')
def claim_details(request, id):
    class StatusForm(forms.ModelForm):
        class Meta:
            model = Claim
            fields = ('status', )
            
        status = forms.ChoiceField(choices=CASE_STATUSES_PUBLIC)

    
    TYPE_MAP = {
        ClaimType.GameIsDamaged: GameIsDamagedClaim,
        ClaimType.WrongGame: WrongGameClaim,
        ClaimType.DontRecieve: DontReceiveClaim,
        ClaimType.MailerIsEmpty: MailerIsEmptyClaim,
        ClaimType.GamemineNotReceiveGame: GamemineNotReceiveGameClaim,
        ClaimType.GamemineNotReceiveTradeGame: GamemineNotRecieveTradeGameClaim,
        ClaimType.WrongTradeValueCredit: WrongTradeValueCreditClaim,
    }
    
    claim = get_object_or_404(Claim, id=id)

    if request.method == 'POST':
        status_form = FeedbackStatusForm(request.POST, instance=claim)
        if status_form.is_valid():
            status_form.save()
        return redirect('staff:claim_details', claim.id)
    if claim.status != CaseStatus.AutoClosed:
        status_form = FeedbackStatusForm(instance=claim)
    else:
        status_form = FeedbackStatusForm(initial={'status': CaseStatus.Closed})
    
    type = TYPE_MAP.get(claim.type)
    if not type:
        raise Http404()
    claim = get_object_or_404(type, id=id)
    
    return {
        'title': 'Claim Details',
        'claim': claim,
        'status_form': status_form,
        'replies': Reply.get_replies(get_object_or_404(Claim, id=id)),
        'reply_form': ReplyForm(initial={'status': claim.status if claim.status != CaseStatus.AutoClosed else CaseStatus.Closed}),
    }
    

@transaction.commit_on_success
def reply_to_claim(request, id):
    if request.method == 'POST':
        claim = get_object_or_404(Claim, id=id)
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(False)
            reply.case = claim
            reply.mailed_to = claim.user.email
            reply.save()
            claim.status = reply.status
            claim.save()
            reply.send_email()
    return redirect('staff:claim_details', id)
