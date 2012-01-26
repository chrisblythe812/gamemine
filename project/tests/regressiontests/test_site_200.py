# pylint: disable-msg=E,W,C,R
from django.test import TestCase
from django.core.urlresolvers import reverse


class AllSiteTests(TestCase):
    fixtures = ["users.yaml"]

    def test_all_pages_200(self):
        url = reverse("catalog:category", kwargs={"slug": "Xbox-360-Games"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        # TODO(Roman): Invastigate
        # response = self.client.get("/Xbox-360-Games/undefined")
        # self.failUnlessEqual(response.status_code, 404)

        response = self.client.get(reverse("index"))
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("simple-page", kwargs={"page": "How-It-Works"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("catalog:index"))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("project.banners.views.balalayka"), {'2090450': ''})
        self.failUnlessEqual(response.status_code, 302)

        url = reverse("simple-page", kwargs={"page": "Help-FAQs"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("simple-page", kwargs={"page": "Terms"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("simple-page", kwargs={"page": "Privacy"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("staff:index"))
        self.assertRedirects(response, reverse("members:login")+u"?next=/Staff/")

        response = self.client.get(reverse("members:login"), {'next': '/Staff/'})
        self.failUnlessEqual(response.status_code, 200)

        data = {
            "password": u"admin",
            "remember": u"on",
            "email": u"admin@gamemine.com",
            "next": u"/Staff/"
        }
        response = self.client.post(reverse("members:login"), data)
        self.assertRedirects(response, reverse("staff:index")+u"?")

        response = self.client.get(reverse("staff:index"))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("staff:customer"))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("staff:fulfillment"))
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Personnel/Staff"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "CRM/Feedbacks"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "CRM/Tickets/Personal-Games"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Distribution/Management"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Distribution/Purchases"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Distribution/Create-Purchase"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Distribution/Operations"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Check-In"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Admin"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/DC-Queue"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Physical"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Check"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Upload/Master-Product-List"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Upload/New"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Upload/Used"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Inventory/Upload/Used-Prices"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Discounts/Adjustments"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Discounts/Platform"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Discounts/Genre"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Discounts/Tag"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Discounts/Group"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Orders"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Orders/Pre-Ordered"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Orders/Not-In-Stock"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Orders/Shipped"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Game-Weight-Matrix"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Buy/Ingram"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Trade/Orders"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Trade/Orders/Pending-Arrival"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Trade/Orders/Processed-Items"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Trade/Claims-and-Disputes"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Orders"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Orders/Shipped"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Orders/Returns"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url, {'status': '0'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Allocation-Factors"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/DC-Maintenance"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Payments/Transactions"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Payments/Taxes/By-County"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Payments/Taxes/By-State"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Purchase-Forecast"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url, {'type': '2'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url, {'type': '4'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url, {'type': '0'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Rent/Claims-and-Disputes"})
        response = self.client.get(url, {'type': '1'})
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Soft-Launch"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Sales-Tax-Report"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Recurring-Billing-Report"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Inventory"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Inventory?excel", follow=True)
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response["Content-Type"], "application/vnd.ms-excel")

        url = reverse("staff:page", kwargs={"path": "Reports/Games"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Inactive-Items"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/By-Summary"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/By-Business"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Future-Billings")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Future-Billings/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Future-Billings"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Double-Speed-Activation")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Double-Speed-Activation/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Double-Speed-Activation"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Top-Rentals")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Top-Rentals/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Top-Rentals"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/No-Games-On-List")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/No-Games-On-List/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/No-Games-On-List"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Canceled")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Canceled/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Canceled"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Active-Days")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Active-Days/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Canceled-By-Active-Days"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Affiliate")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Affiliate/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Canceled-By-Affiliate"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Reason")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Canceled-By-Reason/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Canceled-By-Reason"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Rent-Subscribers/Collections")
        self.assertRedirects(response, "/Staff/Reports/Membership/Rent-Subscribers/Collections/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Rent-Subscribers/Collections"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Buy"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Buy/Best-Sellers")
        self.assertRedirects(response, "/Staff/Reports/Membership/Buy/Best-Sellers/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Buy/Best-Sellers"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Trade-Ins"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get("/Staff/Reports/Membership/Trade-Ins/Top-Trades")
        self.assertRedirects(response, "/Staff/Reports/Membership/Trade-Ins/Top-Trades/"+u"?", status_code=301)

        url = reverse("staff:page", kwargs={"path": "Reports/Membership/Trade-Ins/Top-Trades"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Reports/Channel-Advisor"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Content/Featured-Games"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Content/Banners/Lists"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        url = reverse("staff:page", kwargs={"path": "Content/Muze-DB/Updates"})
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("staff:campaigns"))
        self.failUnlessEqual(response.status_code, 200)

        response = self.client.get(reverse("staff:subscribers"))
        self.failUnlessEqual(response.status_code, 200)
