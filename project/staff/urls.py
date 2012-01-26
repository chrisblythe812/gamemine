from logging import debug #@UnusedImport

from django.conf.urls.defaults import patterns, url
from django.core.urlresolvers import get_callable
from django.utils.http import urlquote
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect

from project.members.models import Group
from project.staff.menu import main_menu, section, menu
from project.crm.models import PersonalGameTicket, CaseStatus
from project.claims.models import Claim, SphereChoice
from project.trade.models import TradeOrder

def get_personal_games_tickets_amount():
    c = PersonalGameTicket.objects.filter(status=CaseStatus.New).count()
    return c or ''


def get_shipping_problems_tickets_amount():
    c = Claim.objects.filter().count()
    return c or ''


def get_trade_claims_amount():
    c = Claim.objects.filter(status__lt=CaseStatus.Closed, sphere_of_claim=SphereChoice.Trade).count()
    return c or ''


def get_rent_claims_amount():
    c = Claim.objects.filter(status__lt=CaseStatus.Closed, sphere_of_claim=SphereChoice.Rent).count()
    return c or ''

def get_pending_arrival_count():
    orders = TradeOrder.objects.filter(received_date=None).exclude(items__processed=True)
    c = orders.count()
    return c or ''


staff_main_menu = main_menu(
    section('Personnel',
        menu('Staff', '/Staff/Personnel/Staff/', []),
    ),
    section('CRM',
        menu('Feedbacks', '/Staff/CRM/Feedbacks/', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent]),
        section('Tickets',
            menu('Personal Games', '/Staff/CRM/Tickets/Personal-Games/', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent],
                 status=get_personal_games_tickets_amount),
#            menu('Shipping Problems', '/Staff/CRM/Tickets/Shipping-Problems/', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent],
#                 status=get_shipping_problems_tickets_amount),
        ),
    ),
    section('Distribution',
        menu('Management', '/Staff/Distribution/Management/', [Group.Accounting, Group.Executive]),
        menu('Purchases', '/Staff/Distribution/Purchases/', [Group.Accounting, Group.Executive],
             menu('Create Purchase', '/Staff/Distribution/Create-Purchase/', [Group.PurchaseManager, Group.Accounting, Group.Executive]),
        ),
        menu('Operations', '/Staff/Distribution/Operations/', [Group.DC_Manager]),
    ),
    section('Inventory',
#        menu('Manage Games', '/Staff/Inventory/Manage-Games', [Group.PurchaseManager]),
        menu('Check-In Games', '/Staff/Inventory/Check-In/', [Group.PurchaseManager, Group.DC_Operator]),
        menu('Inventory Admin', '/Staff/Inventory/Admin/', [Group.PurchaseManager]),
        menu('DC Queue', '/Staff/Inventory/DC-Queue/', [Group.PurchaseManager, Group.DC_Operator, Group.DC_Manager]),
        menu('Physical Games', '/Staff/Inventory/Physical/', [Group.PurchaseManager, Group.DC_Manager]),
        menu('Process Games', '/Staff/Inventory/Check/', [Group.PurchaseManager, Group.DC_Operator, Group.DC_Manager]),
#        section('Distributors',
#            menu('New Game Distributors', '/Staff/Inventory/Distributors/New-Games/', [Group.PurchaseManager]),
#            menu('Used Game Distributors', '/Staff/Inventory/Distributors/Used-Games/', [Group.PurchaseManager]),
#        ),
        section('Upload',
            menu('Master Product List', '/Staff/Inventory/Upload/Master-Product-List/', []),
            menu('New Inventory Feed', '/Staff/Inventory/Upload/New/', []),
            menu('Used Inventory Feed', '/Staff/Inventory/Upload/Used/', []),
            menu('Used Inventory Prices', '/Staff/Inventory/Upload/Used-Prices/', []),
        ),
    ),
    section('Price Adjustments',
        menu('Adjustments', '/Staff/Discounts/Adjustments/', [],
            menu('By Platform', '/Staff/Discounts/Platform/', []),
            menu('By Genre', '/Staff/Discounts/Genre/', []),
            menu('By Tag', '/Staff/Discounts/Tag/', []),
            menu('By Group', '/Staff/Discounts/Group/', []),
        ),
    ),
    section('Buy',
        menu('Orders', '/Staff/Buy/Orders/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
            menu('Pre-Ordered', '/Staff/Buy/Orders/Pre-Ordered/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Not In Stock', '/Staff/Buy/Orders/Not-In-Stock/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Shipped', '/Staff/Buy/Orders/Shipped/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
#            menu('Returns', '/Staff/Buy/Orders/Returns/', []),
        ),
#        menu('Shipping Methods', '/Staff/Buy/Shipping-Methods/', []),
        menu('Game Weight Matrix', '/Staff/Buy/Game-Weight-Matrix/', []),
        menu('Ingram', '/Staff/Buy/Ingram/', []),
    ),
    section('Trade',
        menu('Orders', '/Staff/Trade/Orders/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
             menu('Pending Arrival', '/Staff/Trade/Orders/Pending-Arrival/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
                  status=get_pending_arrival_count),
             menu('Processed Items', '/Staff/Trade/Orders/Processed-Items/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
#            menu('Transfers', '/Staff/Trade/Orders/Transfers/', []),
        ),
        menu('Claims / Disputes', '/Staff/Trade/Claims-and-Disputes/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
             status=get_trade_claims_amount),
#        menu('Trade Value Calculator', '/Staff/Trade/Value-Calculator/', []),
    ),
    section('Rent',
        menu('Orders', '/Staff/Rent/Orders/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
            menu('Shipped', '/Staff/Rent/Orders/Shipped/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Returns', '/Staff/Rent/Orders/Returns/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
#            menu('Claims', '/Staff/Rent/Orders/Claims/', []),
        ),
#        menu('Subscription Packages', '/Staff/Rent/Subscription-Packages/', []),
#        menu('Availability Statuses', '/Staff/Rent/Availability-Statuses/', []),
        menu('Claims / Disputes', '/Staff/Rent/Claims-and-Disputes/?status=0', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
             status=get_rent_claims_amount),
        menu('Allocation Factors', '/Staff/Rent/Allocation-Factors/', []),
        menu('DC Maintenance', '/Staff/Rent/DC-Maintenance/', []),
    ),
    section('Payments',
        menu('Transactions', '/Staff/Payments/Transactions/', [Group.DC_Manager, Group.CS_Manager, Group.CS_Agent]),
        section('Taxes',
            menu('By County', '/Staff/Payments/Taxes/By-County/', []),
            menu('By State', '/Staff/Payments/Taxes/By-State/', []),
        ),
    ),
    section('Reports',
        menu('Purchase Forecast', '/Staff/Reports/Purchase-Forecast/', [Group.PurchaseManager]),
        menu('Shipping Problems', '/Staff/Rent/Claims-and-Disputes/', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager],
            menu('Lost Games (sent)', '/Staff/Rent/Claims-and-Disputes/?type=2', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Lost Games (returned)', '/Staff/Rent/Claims-and-Disputes/?type=4', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Damaged Games', '/Staff/Rent/Claims-and-Disputes/?type=0', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
            menu('Wrong Games (received)', '/Staff/Rent/Claims-and-Disputes/?type=1', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager]),
        ),
        menu('Soft Launch', '/Staff/Reports/Soft-Launch/', []),
        menu('Sales Tax Report', '/Staff/Reports/Sales-Tax-Report/', []),
        #menu('Recurring Income Report', '/Staff/Reports/Recurring-Income-Report/', []),
        menu('Recurring Billing Report', '/Staff/Reports/Recurring-Billing-Report/', []),
        menu('Inventory', '/Staff/Reports/Inventory/', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager]),
        menu('Games', '/Staff/Reports/Games/', []),
        menu('Inactive Items', '/Staff/Reports/Inactive-Items/', []),
#        section('Shipping Problems',
#            menu('Lost Games (sent)', '/Staff/Reports/Problems/Lost-Games-Sent/', []),
#            menu('Lost Games (returned)', '/Staff/Reports/Problems/Lost-Games-Returned/', []),
#            menu('Damaged Games', '/Staff/Reports/Problems/Damaged-Games/', []),
#            menu('Wrong Games (received)', '/Staff/Reports/Problems/Wrong-Games-Received)/', []),
#        ),

        section('Affiliates',
            menu('Compliance Report', '/Staff/Reports/Affiliates/Compliance', [])
        ),

        section('Membership',
            menu('Membership by Summary', '/Staff/Reports/Membership/By-Summary/', []),
            menu('Membership by Business', '/Staff/Reports/Membership/By-Business/', []),
#            menu('Members', '/Staff/Reports/Membership/Members/', []),
            menu('Rent (subscribers)', '/Staff/Reports/Membership/Rent-Subscribers/', [],
                 menu('Future Billings', '/Staff/Reports/Membership/Rent-Subscribers/Future-Billings', []),
                 menu('2xSPEED Activation', '/Staff/Reports/Membership/Rent-Subscribers/Double-Speed-Activation', []),
                 menu('Top Rentals', '/Staff/Reports/Membership/Rent-Subscribers/Top-Rentals', []),
                 menu('No Games On List', '/Staff/Reports/Membership/Rent-Subscribers/No-Games-On-List', []),
                 menu('Canceled', '/Staff/Reports/Membership/Rent-Subscribers/Canceled', [],
                      menu('By Active Days', '/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Active-Days', [],),
                      menu('By Affiliate', '/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Affiliate', [],),
                      menu('By Reason', '/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Reason', [],),
                 ),
                 menu('Collections', '/Staff/Reports/Membership/Rent-Subscribers/Collections', []),
            ),
            menu('Buy (paid users)', '/Staff/Reports/Membership/Buy/', [],
                 menu('Best Sellers', '/Staff/Reports/Membership/Buy/Best-Sellers', []),
            ),
            menu('Trade-Ins', '/Staff/Reports/Membership/Trade-Ins/', [],
                 menu('Top Trades', '/Staff/Reports/Membership/Trade-Ins/Top-Trades', []),
            ),
        ),
        menu('Channel Advisor', '/Staff/Reports/Channel-Advisor/', []),
    ),
    section('Content',
        section('Banners',
            menu('Featured Games', '/Staff/Content/Featured-Games/', []),
#            menu('Browse Games', '/Staff/Content/Banners/Browse-Games/', []),
            menu('Lists', '/Staff/Content/Banners/Lists/', []),
        ),
        section('Muze DB',
            menu('Updates', '/Staff/Content/Muze-DB/Updates/', []),
        ),
        menu('Campaigns', '/Staff/Content/Campaigns/', []),
        menu('Subscribers', '/Staff/Content/Subscribers/', []),
        menu('Offer Terms', '/Staff/Content/OfferTerms/', []),
    ),
)

def staff_url(pattern, view, perms, name, **kwargs):
    def real_view(request, *args, **kwargs):
        if not request.user.is_staff:
            path = urlquote(request.get_full_path())
            tup = settings.LOGIN_URL, 'next', path
            return HttpResponseRedirect('%s?%s=%s' % tup)
        if not request.user.is_superuser and Group.All not in perms and request.user.get_profile().group not in perms:
            return HttpResponseForbidden('Access Denied')
        callback = get_callable('project.staff.views.' + view)
        return callback(request, *args, **kwargs)
    return url(pattern, real_view, name=name)

urlpatterns = patterns('project.staff.views',
    staff_url('^$', 'common.index', [Group.All], name='index'),
    staff_url('^Customer/$', 'common.customer', [Group.All], name='customer'),

    staff_url('^Customer-View/(?P<user_id>\d+)/$', 'customer.view', [Group.All], name='customer_view'),
    # Workarround for non existing members
    staff_url('^Customer-View/0/$', 'customer.view', [Group.All], name='customer_view'),
    staff_url('^Customer-View/(?P<user_id>.*)/$', 'customer.view', [Group.All], name='customer_view'),
    # --
    staff_url('^Customer-Set-Password/(?P<user_id>\d+)/$', 'customer.set_password', [Group.All], name='customer_set_password'),
    staff_url('^Customer-Addresses/(?P<user_id>\d+)/$', 'customer.addresses', [Group.All], name='customer_addresses'),
    staff_url('^Customer-Orders/(?P<user_id>\d+)/$', 'customer.orders', [Group.All], name='customer_orders'),
    staff_url('^Customer-Lists/(?P<user_id>\d+)/$', 'customer.lists', [Group.All], name='customer_lists'),
    staff_url('^Customer-Lists/(?P<user_id>\d+)/Rent/$', 'customer.rent_list', [Group.All], name='customer_rent_list'),
    staff_url('^Customer-Shopping-Cart/(?P<user_id>\d+)/$', 'customer.shopping_cart', [Group.All], name='customer_shopping_cart'),
    staff_url('^Customer-Product-Reviews/(?P<user_id>\d+)/$', 'customer.product_reviews', [Group.All], name='customer_product_reviews'),
    staff_url('^Customer-Product-Ratings/(?P<user_id>\d+)/$', 'customer.product_ratings', [Group.All], name='customer_product_ratings'),
    staff_url('^Customer-Shipping-Problems/(?P<user_id>\d+)/$', 'customer.shipping_problems', [Group.All], name='customer_shipping_problems'),
    staff_url('^Customer-Billing-History/(?P<user_id>\d+)/$', 'customer.billing_history', [Group.All], name='customer_billing_history'),
    staff_url('^Customer-Credits-History/(?P<user_id>\d+)/$', 'customer.credits_history', [Group.All], name='customer_credits_history'),
    staff_url('^Customer-Feedbacks/(?P<user_id>\d+)/$', 'customer.feedbacks', [Group.All], name='customer_feedbacks'),

    staff_url('^Customer/(?P<user_id>\d+)/Cancel-Rent-Account/$', 'customer.cancel_rent_account', [], name='cancel_customer_rent_account'),
    staff_url('^Customer/(?P<user_id>\d+)/E-mails/$', 'customer.emails', [Group.All], name='customer_emails'),
    staff_url('^Customer/(?P<user_id>\d+)/E-mail/(?P<email_id>\d+)/$', 'customer.email', [Group.All], name='customer_email'),
    staff_url('^Customer/(?P<user_id>\d+)/E-mail/(?P<email_id>\d+)/Body/$', 'customer.email_body', [Group.All], name='customer_email_body'),

    staff_url('^Personnel/Staff/New/$', 'personnel.new_user', [], name='new_user'),
    staff_url('^Personnel/Staff/(?P<id>[0-9]+)/Edit/$', 'personnel.edit_user', [], name='edit_user'),
    staff_url('^Personnel/Staff/(?P<id>[0-9]+)/Change-Password/$', 'personnel.change_user_password', [], name='change_user_password'),

    staff_url('^CRM/Feedbacks/(?P<id>[0-9]+)/$', 'crm.feedback_details', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent], name='feedback_details'),
    staff_url('^CRM/Feedbacks/(?P<id>[0-9]+)/Reply/$', 'crm.reply_to_feedback', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent], name='reply_to_feedback'),
    staff_url('^CRM/Tickets/Personal-Games/(?P<id>[0-9]+)/$', 'crm.personal_game_details', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent], name='personal_game_details'),
    staff_url('^CRM/Claims/(?P<id>[0-9]+)/$', 'crm.claim_details', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent], name='claim_details'),
    staff_url('^CRM/Claims/(?P<id>[0-9]+)/Reply$', 'crm.reply_to_claim', [Group.DC_Manager, Group.DC_Operator, Group.CS_Manager, Group.CS_Agent], name='reply_to_claim'),

    staff_url('^Fulfillment/$', 'common.fulfillment', [Group.All], name='fulfillment'),

    staff_url('^Inventory/Physical/(?P<dc_code>\w{2})/', 'inventory.physical', [Group.PurchaseManager, Group.DC_Operator, Group.DC_Manager], name='physical_inventory'),
    staff_url('^Inventory/Admin/Entries/(?P<item_id>\d+)/', 'inventory.admin_entries', [Group.PurchaseManager], name='inventory_admin_entries'),

    staff_url('^Purchase-Order/(?P<purchase_id>\d+)/$', 'common.purchase_order', [Group.PurchaseManager], name='purchase_order'),
    staff_url('^Check-UPC/(?P<upc>.*)/$', 'common.check_upc', [Group.PurchaseManager, Group.DC_Operator], name='check_upc'),
    staff_url('^Entries/(?P<dc_code>.+)/(?P<item_id>\d+)/$', 'inventory.entries', [Group.PurchaseManager, Group.DC_Operator, Group.DC_Manager], name='entries'),

    staff_url('^Rent/Orders/Pick-List/(?P<item_id>\d+)/(?P<dc>\d+)/$', 'rent.rent_pick_list_details', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='rent_pick_list_details'),
    staff_url('^Rent/Orders/Mark-As-Shipped/$', 'rent.mark_shipped', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='rent_mark_shipped'),
    staff_url('^Rent/Orders/(?P<order_id>\d+)/$', 'rent.order_details', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='rent_order_details'),
    staff_url('^Rent/Orders/Returns/(?P<order_id>\d+)/(?P<dc>\w{2})/$', 'rent.do_rent_returns', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='do_rent_returns'),

    staff_url('^Buy/Orders/Pick-List/(?P<item_id>\d+)/(?P<dc>\d+)/$', 'buy.buy_pick_list_details', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='buy_pick_list_details'),
    staff_url('^Buy/Orders/Mark-As-Shipped/$', 'buy.mark_shipped', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='buy_mark_shipped'),
    staff_url('^Buy/Orders/(?P<order_id>\d+)/$', 'buy.buy_order_details', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='buy_order_details'),
    staff_url('^Buy/Orders/Not-in-Stock/(?P<item_id>\d+)/(?P<condition>NG|UG)/$', 'buy.buy_orders_not_in_stock_details', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='buy_orders_details'),
    staff_url('^Buy/Orders/Pre-Released/(?P<item_id>\d+)/$', 'buy.buy_orders_pre_ordered_details', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='buy_orders_details_po'),

    staff_url('^Trade/Orders/Details/(?P<id>\d+)/$', 'trade.order_details', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='trade_order_details'),
    staff_url('^Trade/Orders/Details/(?P<order_id>\d+)/(?P<item_id>\d+)/$', 'trade.order_details_item', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='trade_order_details_item'),
    staff_url('^Trade/Orders/Details/(?P<order_id>\d+)/(?P<item_id>\d+)/Assign/$', 'trade.trade_order_assign_item', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='trade_order_assign_item'),
    # Workarround for missing orders
    staff_url('^Trade/Orders/Details/(?P<id>.*)/$', 'trade.order_details', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='trade_order_details'),

    staff_url('^Labels/Rent/$', 'labels.rent', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='rent_labels'),
    staff_url('^Labels/Buy/$', 'labels.buy', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='buy_labels'),
    staff_url('^Labels/Buy/Pack-Slips/$', 'labels.buy_pack_slips', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='buy_pack_slips'),
    staff_url('^Labels/Trade/$', 'labels.trade', [Group.DC_Operator, Group.DC_Manager, Group.PurchaseManager], name='trade_labels'),

    staff_url('^Payments/Transactions/(?P<id>\d+)/$', 'payments.transaction_details', [Group.DC_Manager, Group.CS_Manager, Group.CS_Agent], name='transaction_details'),
    staff_url('^Payments/Transactions/(?P<id>\d+)/Refund/$', 'payments.refund_transaction', [Group.DC_Manager, Group.CS_Manager, Group.CS_Agent], name='refund_transaction'),
    staff_url('^Payments/Taxes/By-County/Add/$', 'payments.add_county_tax', [], name='add_county_tax'),
    staff_url('^Payments/Taxes/By-County/(?P<id>\d+)/Edit/$', 'payments.edit_county_tax', [], name='edit_county_tax'),
    staff_url('^Payments/Taxes/By-County/(?P<id>\d+)/Delete/$', 'payments.delete_county_tax', [], name='delete_county_tax'),
    staff_url('^Payments/Taxes/By-State/Add/$', 'payments.add_state_tax', [], name='add_state_tax'),
    staff_url('^Payments/Taxes/By-State/(?P<id>\d+)/Edit/$', 'payments.edit_state_tax', [], name='edit_state_tax'),
    staff_url('^Payments/Taxes/By-State/(?P<id>\d+)/Delete/$', 'payments.delete_state_tax', [], name='delete_state_tax'),

    staff_url('^Content/Featured-Game/Add/$', 'content.featured_game_add', [], name='content_featured_game_add'),
    staff_url('^Content/Featured-Game/(?P<id>\d+)/Edit/$', 'content.featured_game_edit', [], name='content_featured_game_edit'),
    staff_url('^Content/Featured-Game/(?P<id>\d+)/Delete/$', 'content.featured_game_delete', [], name='content_featured_game_delete'),

#    staff_url('^Content/Banners/Browse-Games/Add/$', 'content.add_browse_game_banner', [], name='add_browse_game_banner'),
#    staff_url('^Content/Banners/Browse-Games/(?P<id>\d+)/Edit$', 'content.edit_browse_game_banner', [], name='edit_browse_game_banner'),
#    staff_url('^Content/Banners/Browse-Games/(?P<id>\d+)/Delete$', 'content.delete_browse_game_banner', [], name='delete_browse_game_banner'),

    staff_url('^Content/Campaigns/$', 'content.campaigns', [], name='campaigns'),
    staff_url('^Content/Campaigns/(?P<cid>[\d\w]+)/Delete$', 'content.edit_campaign', [], name='edit_campaign'),
    staff_url('^Content/Campaigns/(?P<cid>[\d\w]+)/Edit$', 'content.del_campaign', [], name='del_campaign'),
    staff_url('^Content/Campaigns/Add/$', 'content.add_campaign', [], name='add_campaign'),
    staff_url('^Content/Banners/Lists/Add/$', 'content.add_lists_banner', [], name='add_lists_banner'),
    staff_url('^Content/Banners/Lists/(?P<id>\d+)/Edit$', 'content.edit_lists_banner', [], name='edit_lists_banner'),
    staff_url('^Content/Banners/Lists/(?P<id>\d+)/Delete$', 'content.delete_lists_banner', [], name='delete_lists_banner'),
    staff_url('^Content/Subscribers/$', 'content.subscribers', [], name='subscribers'),
    staff_url('^Content/OfferTerms/$', 'content.offer_terms', [], name='offer_terms'),
    staff_url('^Content/OfferTerms/Add$', 'content.add_offer_term', [], name='add_offer_term'),
    staff_url('^Content/OfferTerms/(?P<id>[\d\w]+)/Delete$', 'content.del_offer_term', [], name='del_offer_term'),
    staff_url('^Content/OfferTerms/(?P<id>[\d\w]+)/Edit$', 'content.edit_offer_term', [], name='edit_offer_term'),

    staff_url('^Discounts/Tag/Add/$', 'discounts.add_tag_discount', [], name='add_tag_discount'),
    staff_url('^Discounts/Group/Add/$', 'discounts.add_group_discount', [], name='add_group_discount'),

    staff_url('^Reports/Inventory/(?P<id>\d+)/History/$', 'reports.inventory_history', [Group.DC_Operator, Group.DC_Manager, Group.CS_Agent, Group.PurchaseManager], name='inventory_history'),

    url('^(?P<path>.*)/$', 'common.page', name='page'),
)
