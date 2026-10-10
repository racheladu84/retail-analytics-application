
# defines the five URL patterns for the analytics application
# each path() maps a URL to a view function and assigns a named identifier
# named URLs enable views and templates to reference URLs by name
# if a URL path changes only this file needs updating

from django.urls import path
from .import views

#login = root -  first page presented to any user
#logout - logout URL maps to logout_view — terminates user session

urlpatterns = [
    path('',views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    ## trend URL maps to trend_dashboard view
    # accessible to both store manager and store worker

    path('trend/', views.trend_dashboard, name='trend_dashboard'),

    # forecast URL maps to forecast_dashboard view
    # restricted to store manager only
    path('forecast/', views.forecast_dashboard, name='forecast_dashboard'),
    
    # password-reset URL maps to password_reset_view
    # renders a placeholder page directing users to contact the system administrator
    path('password-reset/', views.password_reset_view, name ='password_reset')

]

