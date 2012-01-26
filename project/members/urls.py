from django.conf.urls.defaults import * #@UnusedWildImport

from forms import SetPasswordForm


urlpatterns = patterns('project.members.views',
#    url(r'^signup/$', SignupWizard.create(), name='signup'),
    url(r'^Member-Home/Login/$', 'login', name='login'),
    url(r'^Member-Home/Logout/$', 'logout', name='logout'),
    url(r'^Member-Home/Account/Create/$', 'create_account', name='create_account'),
    url(r'^Member-Home/Account/Create/Complete/$', 'create_account_complete', name='create_account_complete'),
    url(r'^Member-Home/Account/$', 'account', name='account'),
    url(r'^Member-Home/Confirm/(?P<code>[-a-z0-9]+)/$', 'confirm_registration', name='confirm_registration'),

    url(r'^Member-Home/Amnesia/Done/$', 'password_reset_done', name='password_reset_done'),

    url(r'^Account/Name-and-Address/$', 'account_name_and_address', name='name_and_address'),
    url(r'^Account/Payment-Method/$', 'account_payment_method', name='payment_method'),
    url(r'^Account/Login-and-Password/$', 'account_login_and_password', name='login_and_password'),
    url(r'^Account/Billing-History/$', 'account_billing_history', name='billing_history'),
    url(r'^Account/Report-Problems/$', 'account_report_problems', name='report_problems'),
    url(r'^Account/Report-Problems/(?P<sphere>Rent|Trade|Buy)/$', 'report_claim_type', name='report_claim_type'),
    url(r'^Account/Report-Problems/(?P<sphere>Rent|Trade|Buy)/(?P<id>[1-9][0-9]*)/$', 'report_claim', name='report_claim'),
    url(r'^Account/Terms-and-Details/$', 'account_terms_and_details', name='terms_and_details'),
    url(r'^Account/Put-on-Hold/$', 'account_put_on_hold', name='put_on_hold'),
    url(r'^Account/Reactivate/$', 'account_reactivate', name='reactivate'),
    url(r'^Account/Change-Reactivation-Date/$', 'account_change_reactivation_date', name='change_reactivation_date'),

    url(r'^Member-Home/Settings/My-Systems/$', 'settings_my_systems', name='settings_my_systems'),
    url(r'^Member-Home/Settings/Parental-Controls/$', 'settings_parental_controls', name='settings_parental_controls'),

    url(r'^Member-Home/Profile/Personalize-Your-Games/$', 'personalize_your_games', name='personalize_your_games'),
    url(r'^Member-Home/Profile/Image/$', 'profile_image', name='profile_image'),
    url(r'^Member-Home/Profile/Image/Defaults/$', 'profile_image_defaults', name='profile_image_defaults'),
    url(r'^Member-Home/Profile/Favorite-Genre/$', 'profile_favorite_genre', name='profile_favorite_genre'),
    url(r'^Member-Home/Profile/Game-Reviews/$', 'profile_game_reviews', name='profile_game_reviews'),
    url(r'^Member-Home/Profile/Game-Ratings/$', 'profile_game_ratings', name='profile_game_ratings'),

    url(r'^Buy/History/$', 'buy_history', name='buy_history'),
    url(r'^Rent/History/$', 'rent_history', name='rent_history'),
    url(r'^Trade/History/$', 'trade_history', name='trade_history'),

    url(r'^Buy/Order-History/(?P<id>[1-9][0-9]*)/$', 'buy_order_details', name='buy_order_details'),

    url(r'^Buy/List/$', 'buy_list', name='buy_list'),
    url(r'^Buy/Change/(?P<id>[1-9][0-9]*)/$', 'buy_list_change', name='buy_list_change'),

    # Deprecated
    # url(r'^Rent/SignUp/$', 'change_rent_plan', name='rent_sign_up'),
    # url(r'^Rent/Change-Plan-Old/$', 'change_rent_plan', name='change_rent_plan'),
    # url(r'^Rent/SignUp/$', 'change_rent_plan'),
    # --
    url(r'^Rent/Change-Plan2/$', 'change_rent_plan2', name='change_rent_plan2'),
    url(r'^Rent/Cancel-Membership/$', 'cancel_membership', name='cancel_membership'),
    url(r'^Rent/Cancel-Membership/Confirm/$', 'cancel_membership_confirm_message', name='cancel_membership_confirm_message'),
    url(r'^Rent/Cancel-Membership/Confirm/(?P<code>.*?)/$', 'cancel_membership_confirm', name='cancel_membership_confirm'),
    url(r'^Rent/List/$', 'rent_list', name='rent_list'),

    url(r'^Store-Credits/$', 'store_credits', name='store_credits'),
    url(r'^Store-Credits/Cash-Out/$', 'cash_back', name='cash_back'),
    url(r'^Store-Credits/Cash-Out/Delete/(?P<id>\d+)/$', 'cash_back_delete', name='cash_back_delete'),

    url(r'^Genre/(?P<id>[1-9][0-9]*)/Rate/(?P<rating>[1-5])/$', 'rate_genre', name='rate_genre'),
    url(r'^Genre/(?P<id>[1-9][0-9]*)/Rate/Clear/$', 'clear_genre_rating', name='clear_genre_rating'),
)

urlpatterns += patterns('django.contrib.auth.views',
#    (r'^login/$', 'django.contrib.auth.views.login'),
#    (r'^logout/$', 'django.contrib.auth.views.logout'),

#    (r'^password_change/$', 'password_change'),
#    (r'^password_change/done/$', 'password_change_done'),
#    (r'^password_reset/$', 'password_reset'),


    url(r'^Amnesia/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm', name='password_reset_confirm',
        kwargs={'template_name': 'members/password_reset_confirm.html',
                'post_reset_redirect': '/Amnesia/Complete/',
                'set_password_form': SetPasswordForm}),
    url(r'^Amnesia/$', 'password_reset', name='amnesia',
        kwargs={'template_name': 'members/password_reset.html',
                'post_reset_redirect': '/Member-Home/Amnesia/Done/', # it doesn't work with `reverse`. I don'r know why.
                'email_template_name': 'members/password_reset_email.html'}),
    url(r'^Amnesia/Complete/$', 'password_reset_complete', name='password_reset_complete',
        kwargs={'template_name': 'members/password_reset_complete.html'}),
)
