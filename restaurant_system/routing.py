from django.urls import re_path
from menu_management.notification_service import NotificationConsumer

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<user_id>\w+)/$', NotificationConsumer.as_asgi()),
]
