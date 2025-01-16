from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

class DisqualificationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Only track requests for the test page
        if "/quiz/" in request.path or "/quiz_summary" in request.path:
            referer = request.META.get("HTTP_REFERER", "")
            allowed_domain = request.get_host()  # Your site's domain
            if not referer or allowed_domain not in referer:
                print("=============Custom Middleware Disqualification Occured=============")
                print("host: ",request.get_host())
                print("referer: ",referer)
                return redirect("quiz:disqualify")