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
    # path('dashboard/filter_type', views.filter_type, name="filter_type"),
    
    # Scan List
    path('dashboard/view/<int:batch_id>/<str:title>/', views.ScanListView.as_view(), name="view_scans"),
    path('dashboard/view/scan-delete/<int:defect_id>/', views.DeleteViewScans, name="delete_view_scans"),
    
    # Scan Camera Session
    path('scan/<int:batch_id>/<str:title>/scan_option/', views.ScanOptionView.as_view(), name="scan_option"),
        # upload
    path('scan/<int:batch_id>/<str:title>/upload', views.ScanUploadView.as_view(), name="scan_upload"),
    path('scan/<int:batch_id>/<str:title>/scanUploadDetect', views.ScanUploadDetect, name="scan_upload_detect"),
        # camera    
    path('scan/<int:batch_id>/<str:title>/camera/<int:scan_number>', views.ScanView.as_view(), name="scan"),
    path('scan/<int:batch_id>/<str:title>/camera/next', views.CameraNext.as_view(), name="camera_next"),
    path('camera_buttons/', views.start_capture, name="start_capture"),
    
    # Summary
    path('dashboard/view/<int:batch_id>/<str:title>/summary/', views.SummaryView.as_view(), name="view_summary"),
        
    # Profile
    path('Profile/', views.ProfileView.as_view(), name="profile_view"),
    path('Profile/Edit/', views.ProfileEditView.as_view(), name="profile_edit"),
    
    # Object Detection
    path('check_camera', views.check_camera, name="check_camera"),
    path('video_feed', views.video_feed, name="video_feed"),
    path('stop_object_py', views.stop_object_py, name="stop_object_py"),
    path('get_defects', views.get_defects, name="get_defects"),
    # path('update_annotated_object/<int:confidence>', views.update_annotated_object, name="update_annotated_object"),
]  
