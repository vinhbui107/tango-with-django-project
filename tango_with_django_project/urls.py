from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rango import views

urlpatterns = [
    path('', views.index, name='index'),
    path('rango/', include('rango.urls', namespace='rango')),
    path('admin/', admin.site.urls),
    path('accounts/', include('registration.backends.simple.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
