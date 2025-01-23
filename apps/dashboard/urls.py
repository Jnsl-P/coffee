from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.index, name="index"),
    
    # Dashboard
    path('dashboard/', views.DashboardListView.as_view(), name="dashboard"),
    path('dashboard/add_session/', views.AddSession.as_view(), name="add_session"),
    path('scan/delete/<pk>', views.DeleteSessionView.as_view(), name="delete_session"),
    
    # Scan List
    path('dashboard/view/<int:batch_id>/<str:title>/', views.ScanListView.as_view(), name="view_scans"),
    path('dashboard/view/scan-delete/<int:defect_id>/', views.DeleteViewScans, name="delete_view_scans"),
    
    # Scan Camera Session
    path('scan/<int:batch_id>/<str:title>/', views.ScanView.as_view(), name="scan"),
    path('camera_buttons/', views.start_capture, name="start_capture"),
    
    # Summary
    path('dashboard/view/<int:batch_id>/<str:title>/summary/', views.SummaryView.as_view(), name="view_summary"),
    
    # Object Detection
    path('check_camera', views.check_camera, name="check_camera"),
    path('video_feed', views.video_feed, name="video_feed"),
    path('stop_object_py', views.stop_object_py, name="stop_object_py"),
    path('get_defects', views.get_defects, name="get_defects"),
    # path('update_annotated_object/<int:confidence>', views.update_annotated_object, name="update_annotated_object"),
]  
