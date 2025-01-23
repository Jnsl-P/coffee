from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BatchSession, DefectsDetected
from django.views.generic.edit import CreateView, DeleteView
from .forms import BatchSessionForm
from django.urls import reverse_lazy

import cv2  
from .object_detection.object import ObjectDetection
from django.http import JsonResponse, StreamingHttpResponse
import base64
import os
from datetime import datetime
from django.core.paginator import Paginator

def index(request):
    if not request.user.is_authenticated:
        return render(request, "dashboard/index.html")
    return redirect("login")

# DASHBOARD
class DashboardListView(LoginRequiredMixin, ListView):
    model = BatchSession
    template_name = "dashboard/dashboard.html"
    redirect_field_name = "redirect_to"
    paginate_by = 5
    
    def get_queryset(self):
        if self.request.GET.get("search"):
            if len(self.request.GET.get("search").strip()) > 0:         
                search_query = self.request.GET.get("search")
                queryset = BatchSession.objects.filter(user=self.request.user, title__icontains=search_query).order_by("-date_created")
                return queryset
        queryset = BatchSession.objects.filter(user=self.request.user).order_by("-date_created")
        return queryset
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get("search"):
            if len(self.request.GET.get("search").strip()) > 0:            
                context['search_query'] = self.request.GET.get("search")
                
        page_obj = context['page_obj']
        paginator = page_obj.paginator

        # Custom page range calculation
        start_index = max(1, page_obj.number - 2)
        end_index = min(paginator.num_pages + 1, page_obj.number + 3)
        context['page_range'] = range(start_index, end_index)
        return context
    
class DeleteSessionView(LoginRequiredMixin, DeleteView):
    model = BatchSession
    template_name = "dashboard/partials/deleteSessionView.html"
    success_url = reverse_lazy("dashboard")

class AddSession(LoginRequiredMixin, CreateView):
    model = BatchSession
    template_name = "dashboard/addSession.html"
    form_class = BatchSessionForm
    
    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.user = self.request.user
        batch.save()
        self.success_url = reverse_lazy("scan", kwargs={"batch_id":batch.batch_id, "title": batch.title})
        return super().form_valid(form)

# SCAN LIST
class ScanListView(LoginRequiredMixin, ListView):
    model = DefectsDetected
    template_name = "dashboard/scans_view.html"
    paginate_by = 5
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batchSession = BatchSession.objects.get(batch_id=self.kwargs["batch_id"])
        context["objects"] = batchSession
        
        page_obj = context['page_obj']
        paginator = page_obj.paginator

        # Custom page range calculation
        start_index = max(1, page_obj.number - 2)
        end_index = min(paginator.num_pages + 1, page_obj.number + 3)
        context['page_range'] = range(start_index, end_index)
        return context
    
    def get_queryset(self):
        all_defects = DefectsDetected.objects.filter(batch_id=self.kwargs["batch_id"]).order_by("-scan_number")
        self.queryset = all_defects
        
        return super().get_queryset()

def DeleteViewScans(request, defect_id):
    if request.POST:
        defect = get_object_or_404(DefectsDetected, id=defect_id)
        batch = BatchSession.objects.get(batch_id = defect.batch_id)
        scan_lists = DefectsDetected.objects.filter(batch = batch)
        
        if defect:
            file_path = './static/final_detected_images/'+ defect.scanned_image
            if os.path.exists(file_path):
                os.remove(file_path)
                
                defect.delete()
                
                # batch = BatchSession.objects.get(batch_id = defect.batch_id)
                # scan_lists = batch.defects_detected
                for index, scan in enumerate(scan_lists):
                    scan.scan_number = index + 1
                    scan.save()
            
        return redirect("view_scans", batch.batch_id, batch.title)
    scan_number = get_object_or_404(DefectsDetected, id=defect_id)
    return render(request, "dashboard/partials/defectsDeleteView.html", {"scan_number": scan_number})

# START CAMERA SESSION
class ScanView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan_view.html"
    success_url=reverse_lazy("scan")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batchSession = BatchSession.objects.get(batch_id=self.kwargs["batch_id"])
        context["objects"] = batchSession
        context["scan_number"] = DefectsDetected.objects.filter(batch=batchSession).order_by("-date_scanned").first()
        return context
    
    def post(self, request, *args, **kwargs):
        last_scan = DefectsDetected.objects.filter(batch_id=self.kwargs["batch_id"]).order_by('-scan_number').first()

        if last_scan:
            last_scan_number = last_scan.scan_number
        else:
            last_scan_number = 0
        
        scan_number = last_scan_number + 1
    
        final_annotated_image = camera_obj.get_last_frame()
        path = "./static/final_detected_images"
        if not os.path.exists(path):
            os.makedirs(path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_name = f"{self.request.user}_{timestamp}_image.jpg"  # Change extension to .png if needed

        # Full path to save the frame
        save_path = os.path.join(path, frame_name)
        # ======save frame
        
        # last_scan = BatchSession.query.order_by(BatchSession.scan_number.desc()).first()
        
        defects_detected = request.POST.getlist("defect")
        defects_array = {}
        
        if request.POST.get("defects_count"):
            defects_count = request.POST.getlist("defects_count")
            defects_count = list(map(int, defects_count))
            
            for index, defect in enumerate(defects_detected):
                # insert in dict
                defects_array[defect] = defects_count[index]
        
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
            
            
        newScan = DefectsDetected(
            scan_number=scan_number,
            defects_detected=defects_array,
            scanned_image=frame_name,
            batch_id = self.kwargs["batch_id"]
            
        )
        # save frame
        cv2.imwrite(save_path, final_annotated_image)
        newScan.save()
        
        message="Data had been added"
        return self.get(request, *args, **kwargs)
    
def start_capture(request):
    return render(request, "dashboard/partials/camera_buttons.html")

    
# SUMMARY   
class SummaryView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/summary_view.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batch_id = self.kwargs['batch_id']
        batch_title = self.kwargs['title']
        all_defects = DefectsDetected.objects.filter(batch = batch_id)
        
        primary_defects_name = [
            "full black",
            "full sour",
            "dried cherry",
            "fungus",
            "foreign matter",
            "severe insect Damage"]
        
        equivalent_values = {
            "full black":1
            ,"full sour":1
            ,"dried cherry":1
            ,"fungus":1
            ,"foreign matter":1
            ,"severe insect Damage":5
            ,"partial black":3
            ,"partial sour":3
            ,"parchment":5
            ,"floater":5
            ,"immature":5
            ,"withered":5
            ,"shell":5
            ,"broken":5
            ,"husk":5,
            "slight insect damage":10}
        
        defects_list_sum = {}
        
        if all_defects:
            for defects in all_defects:
                defects_detected = defects.defects_detected
                for key, value in defects_detected.items():
                    if key in defects_list_sum:
                        defects_list_sum[key] += value
                        
                    else:
                        # divide = defects_list_sum[key] // equivalent_values[key]
                        defects_list_sum[key] = value
                        
        # equivalent full defect values
        full_defects_count = 0
        for key in defects_list_sum:    
            # error with none value
            if key in equivalent_values:
                divide = defects_list_sum[key] // equivalent_values[key]
                defects_list_sum[key] = defects_list_sum[key], divide
        
        # separate primary defects
        primary_defects_list = {}
        keys_to_delete = []
        for key in defects_list_sum:
            if key in primary_defects_name:
                primary_defects_list[key] = defects_list_sum[key]
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del defects_list_sum[key]
                    
        context["batch_id"] = batch_id
        context["batch_title"] = batch_title
        context["defects_list_sum"] = defects_list_sum
        context["primary_defects_list"] = primary_defects_list
        return context

# OBJECT DETECTION
def check_camera(request):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        # Release the camera if it was not opened
        cap.release()
        # Raise an error and return JSON or render an error page
        return JsonResponse({"error": "Camera not detected. Please check your device and permissions."})
    cap.release()
    return JsonResponse({"success": "Camera not detected. Please check your device and permissions."})

def video_feed(request):    
    vid_cam = cv2.VideoCapture(0)
    if not vid_cam.isOpened():
        # Release the camera if it was not opened
        vid_cam.release()
        # Raise an error and return JSON or render an error page
        return JsonResponse({"error": "Camera not detected. Please check your device and permissions."})
    
    return StreamingHttpResponse(
        gen(vid_cam), content_type="multipart/x-mixed-replace; boundary=frame"
    )
    
def gen(camera):
    global camera_obj
    camera_obj = ObjectDetection(camera)
    camera_obj.start()
    try:
        while True:
            frame = camera_obj.get_frames()
            if frame:
                yield (
                    b"--frame\r\n" b"Content-Type: image/png\r\n\r\n" + frame + b"\r\n"
                )
            else:
                break
    except Exception as err:
        print(err)
        print("NO CAMEREA DETECETED")
        return JsonResponse({"error":"no camera detected"})
    finally:
        print("CLOSING")
        camera_obj.stop()
        
def stop_object_py(request):
    global camera_obj
    try:
        captured_frame = camera_obj.get_last_frame()
        print("SUCCESS UPDATING FRAME FILE")       
        
        _, buffer = cv2.imencode('.jpg', captured_frame)
        # Convert to Base64
        frame_b64 = base64.b64encode(buffer).decode('utf-8')
        return JsonResponse(data={"success":True, "message":"Scanning", "captured_frame":frame_b64})
    except Exception as e:
        return JsonResponse(data={"success":False, "message":str(e)})
    
def get_defects(request):
    global camera_obj
    defect = camera_obj.defects
    html = render(request, 'dashboard/partials/defect_result.html', {"defects":defect}).content.decode("utf-8")
    return JsonResponse({
        "success":True,
        "html":html
    })
    
def update_annotated_object(request, confidence):
    global camera_obj
    captured_frame = camera_obj.custom_annotated_frame_percentage(confidence/100)
    _, buffer = cv2.imencode('.jpg', captured_frame)
    # Convert to Base64
    frame_b64 = base64.b64encode(buffer).decode('utf-8')
    return JsonResponse(success=True, captured_frame=frame_b64)
    
    
    
    

    
