"""
WSGI config for retail_analytics project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'retail_analytics.settings')

application = get_wsgi_application()

# it is the standard interface between a web server and a Python web application
# when a user makes a request to the application in the browser
# in this project the WSGI server is used when running the development server
# via python manage.py runserver — Django's built in development server
# acts as both the web server and the WSGI server during development