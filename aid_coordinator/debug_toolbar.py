import ipaddress
import sys

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, SuspiciousOperation
from django.http import HttpRequest


def show_toolbar(request: HttpRequest):
    # No debug = no toolbar
    if not settings.DEBUG:
        return False

    # Extract the remote address, and no address = no toolbar
    try:
        remote_addr = ipaddress.ip_address(request.META.get('REMOTE_ADDR', '::'))
        if remote_addr.is_unspecified:
            return False
    except ValueError:
        # Unparseable IP address? We don't trust you!
        raise SuspiciousOperation(f'Remote IP address {request.META["REMOTE_ADDR"]} cannot be parsed')

    for internal_ip in settings.INTERNAL_IPS:
        try:
            net = ipaddress.ip_network(internal_ip)
            if remote_addr in net:
                # The prefix is on the list
                return True
        except ValueError:
            raise ImproperlyConfigured(f'INTERNAL_IP {internal_ip} cannot be parsed')

    sys.stdout.flush()

    # No toolbar then
    return False
