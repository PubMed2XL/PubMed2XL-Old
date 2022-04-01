"""."""
from django.urls import path, re_path

from .views import download_excel, download_xml, faq

app_name = 'pubmed2xl'
urlpatterns = [
    re_path(r'^xml/((?P<pmid>((\d{1,8}){1}(,\s?\d{1,8})*)?))?$', download_xml, name="download_xml"),
    re_path(r'^((?P<pmid>((\d{1,8}){1}(,\s?\d{1,8})*)?))?$', download_excel, name="download_excel"),
    path('faq/', faq, name="faq"),
]
