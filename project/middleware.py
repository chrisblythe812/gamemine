from django.conf import settings
from django.shortcuts import render_to_response


class CampaignTrackerMiddleware:
    def process_request(self, request):
        r = {}
        for k, v in request.REQUEST.items():
            r[k.lower()] = v

        cid = r.get("cid") or request.COOKIES.get("CampaignID") or "0"
        request.campaign_id = cid.encode("ascii", "ignore")

        sid = r.get("pid") or r.get("PID") or r.get("subid") or r.get("siteid") or request.COOKIES.get("CampaignSubID") or "0"
        request.sid = sid.encode("ascii", "ignore")

        affiliate = r.get("affiliate") or request.COOKIES.get("CampaignAffiliate") or "0"
        request.affiliate = affiliate.encode("ascii", "ignore")

    def process_response(self, request, response):
        if hasattr(request, "campaign_id") and request.campaign_id:
            response.set_cookie("CampaignID", request.campaign_id, 60 * 60 * 24 * 7 * 2)
        if hasattr(request, "sid") and request.sid:
            response.set_cookie("CampaignSubID", request.sid, 60 * 60 * 24 * 7 * 2)
        if hasattr(request, "affiliate") and request.affiliate:
            response.set_cookie("CampaignAffiliate", request.affiliate, 60 * 60 * 24 * 7 * 2)
        return response


class MaintenanceMiddleware:
    def process_request(self, request):
        if not settings.MAINTENANCE:
            return None
        p = request.path
        if (p.startswith("/area51/") or p.startswith("/Staff/")) and request.user.is_superuser:
            return None
        return render_to_response("maintenance.html", {"STATIC_URL": settings.STATIC_URL})
