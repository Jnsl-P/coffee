from django.urls import path
from . import views
from django.contrib.auth.mixins import LoginRequiredMixin

urlpatterns = [
    path("", views.AdminLoginView.as_view(), name="admin"),
    path("dashboard/", views.AdminListView.as_view(), name="admin_dashboard"),
    path("user_view/<pk>/<str:user>/", views.Admin_UserDetailView.as_view(), name="admin_userview"),
    path("dashboard/delete_user/<pk>", views.DeleteUserView.as_view(), name="delete_user"),
]
    