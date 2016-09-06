from django.conf.urls import patterns, include, url
from rest_framework import routers
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from quickstart import views
admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'mysite.views.home', name='home'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^zettaknight/api/', views.zettaknightview.as_view()),
    url(r'^zettaknight/user/share/', views.zettaknightshareview.as_view()),
    url(r'^zettaknight/group/share/', views.zettaknightshareview.as_view()),
    url(r'^zettaknight/user/quota/', views.zettaknightquotaview.as_view()),
    url(r'^zettaknight/group/quota/', views.zettaknightquotaview.as_view())
)
