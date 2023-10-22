from django.urls import path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework_simplejwt.authentication import JWTAuthentication

schema_view = get_schema_view(
   openapi.Info(
      title="Simbir.GO API",
      default_version='v1',
      description="Simbir.GO Project",
      contact=openapi.Contact(email="chupahkin@gmail.com"),
      license=openapi.License(name="Dmitry Chupakhin Lipetsk"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
   authentication_classes=(JWTAuthentication,),
)

urlpatterns = [
   path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]