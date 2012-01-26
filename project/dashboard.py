#@PydevCodeAnalysisIgnore
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from admin_tools.dashboard.models import *
from django.core import urlresolvers

from project.catalog.admin import ItemAdmin

from project.buy_orders.models import BuyOrder, BuyOrderStatus
from project.rent.models import RentList, RentOrder, RentOrderStatus

# to activate your index dashboard add the following to your settings.py:
#
# ADMIN_TOOLS_INDEX_DASHBOARD = 'gamemine.dashboard.CustomIndexDashboard'

class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for gamemine.
    """ 
    def __init__(self, **kwargs):
        Dashboard.__init__(self, **kwargs)

        from django.core.urlresolvers import reverse


        self.children.append(LinkListDashboardModule(
            title=_('Orders Actions'),
            layout='inline',
            draggable=False,
            deletable=False,
            collapsible=False,
            children=[
                {
                    'title': 'Pending BUY orders (%d)' % BuyOrder.objects.filter(status=BuyOrderStatus.Pending).count(),
                    'url': '/area51/buy_orders/buyorder/?status__exact=1',
                },
                {
                    'title': 'Pending RENT orders (%d)' % RentOrder.objects.filter(status=RentOrderStatus.Pending).count(),
                    'url': '/area51/rent/rentorder/?status__exact=0',
                },
                {
                    'title': 'Rent pick list', #len(list(RentList.pending_list())),
                    'url': reverse('project.rent.admin.pick_list'),
                },
            ]
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Orders'),
            include_list=('project.buy_orders', 'project.rent.models.RentGameOnHand', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Rent'),
            include_list=('project.rent.models.MemberRentalPlan', 
                          'project.rent.models.RentalPlan', 
                          'project.rent.models.RentOrder', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Discounts'),
            include_list=('project.discount', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Catalog'),
            include_list=('project.catalog', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Banners'),
            include_list=('project.banners', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Members'),
            include_list=('project.members', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Taxes'),
            include_list=('project.taxes', ),
            deletable=False,
        ))

        self.children.append(ModelListDashboardModule(
            title=_('Inventory'),
            include_list=('project.inventory', ),
            deletable=False,
        ))

#        self.children.append(AppListDashboardModule(
#            title=_('Applications'),
#            exclude_list=('django.contrib', 'project.discount', ),
#        ))

        # append an app list module for "Administration"
        self.children.append(AppListDashboardModule(
            title=_('Administration'),
            include_list=('django.contrib.users',),
        ))

        # append a recent actions module
        #self.children.append(RecentActionsDashboardModule(
        #    title=_('Recent Actions'),
        #    limit=5
        #))

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        pass


# to activate your app index dashboard add the following to your settings.py:
#
# ADMIN_TOOLS_APP_INDEX_DASHBOARD = 'gamemine.dashboard.CustomAppIndexDashboard'

class CustomAppIndexDashboard(AppIndexDashboard):
    """
    Custom app index dashboard for gamemine.
    """ 
    def __init__(self, *args, **kwargs):
        AppIndexDashboard.__init__(self, *args, **kwargs)

        # we disable title because its redundant with the model list module
        self.title = ''

        # append a model list module
        self.children.append(ModelListDashboardModule(
            title=self.app_title,
            include_list=self.models,
        ))

        # append a recent actions module
        self.children.append(RecentActionsDashboardModule(
            title=_('Recent Actions'),
            include_list=self.get_app_content_types(),
        ))

    def init_with_context(self, context):
        """
        Use this method if you need to access the request context.
        """
        pass
