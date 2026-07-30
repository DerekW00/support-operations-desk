from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.staticfiles.views import serve
from django.urls import path, re_path
from support import views

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.queue, name="queue"),
    path("import/", views.import_tickets, name="import"),
    path("tickets/<int:ticket_id>/", views.detail, name="detail"),
    path("tickets/<int:ticket_id>/review/", views.review, name="review"),
    path("tickets/<int:ticket_id>/generate/", views.generate, name="generate"),
    path("jobs/<int:job_id>/cancel/", views.cancel_job, name="cancel_job"),
    path("jobs/<int:job_id>/status/", views.job_status, name="job_status"),
    path("sources/<int:source_id>/", views.source, name="source"),
]
if settings.DEBUG:
    urlpatterns += [re_path(r"^static/(?P<path>.*)$", serve)]
