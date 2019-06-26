from django.conf.urls import re_path
from app import views

urlpatterns = [
    re_path(r'^pc-geetest/register', views.pcgetcaptcha, name='pcgetcaptcha'),
    re_path(r'^mobile-geetest/register', views.mobilegetcaptcha, name='mobilegetcaptcha'),
    re_path(r'^pc-geetest/validate$', views.pcvalidate, name='pcvalidate'),
    re_path(r'^pc-geetest/ajax_validate', views.pcajax_validate, name='pcajax_validate'),
    re_path(r'^mobile-geetest/ajax_validate', views.mobileajax_validate, name='mobileajax_validate'),
    re_path(r'/', views.home, name='home'),
]
