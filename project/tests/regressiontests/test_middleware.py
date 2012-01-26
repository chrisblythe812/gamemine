# -*- coding: utf-8 -*-
from django.test import TestCase


class MiddlewareSiteTests(TestCase):
    def test_campaign_middleware(self):
        response = self.client.get("/?cid=123&pid=1651317­­&affiliate=789")  # -- is non ascii
        self.failUnlessEqual(response.status_code, 200)
        self.failUnlessEqual(response.cookies["CampaignID"].value, "123")
        self.failUnlessEqual(response.cookies["CampaignSubID"].value, "1651317")
        self.failUnlessEqual(response.cookies["CampaignAffiliate"].value, "789")

        response = self.client.get("/")
        self.failUnlessEqual(response.status_code, 200)
