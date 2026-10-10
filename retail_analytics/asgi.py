"""
ASGI config for retail_analytics project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retail_analytics.settings')

application = get_asgi_application()


# asgi.py is similar to wsgi.py but supports asynchronous requests
# in this project it is not actively used as the system runs on standard
# synchronous HTTP requests handled via wsgi.py
# however if the system were extended in the future to support real time
# dashboard updates or live data streaming, asgi.py would become the
# entry point for handling those requests via an asynchronous web server