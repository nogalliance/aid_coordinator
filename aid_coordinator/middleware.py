from django.conf import settings
from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin
from django.utils.timezone import now


class LogLocaleMiddleware(MiddlewareMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = open(settings.BASE_DIR / "language.log", "a")

    def process_request(self, request: HttpRequest):
        if "REMOTE_ADDR" in request.META:
            ip = request.META["REMOTE_ADDR"]
        else:
            ip = "unknown"

        if hasattr(request, "LANGUAGE_CODE"):
            lang = request.LANGUAGE_CODE
        else:
            lang = "unset"

        self.log.write(f"{now()} {ip} {lang}\n")
        self.log.flush()
