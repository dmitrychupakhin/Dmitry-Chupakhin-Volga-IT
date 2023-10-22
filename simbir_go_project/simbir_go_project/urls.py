from django.contrib import admin
from django.urls import path, include
from .yasg import urlpatterns as doc_urls


urlpatterns = [
    path('', include('simbir_go_app.urls'))
]

urlpatterns += doc_urls