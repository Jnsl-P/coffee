import ast
from collections import defaultdict
import json
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
import numpy as np
from ultralytics import settings
from .models import BatchSession, DefectsDetected
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from .forms import BatchSessionForm, ProfileForm
from django.urls import reverse, reverse_lazy
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from PIL import Image

import cv2  
from .object_detection.object import ObjectDetection
from django.http import JsonResponse, StreamingHttpResponse
import base64
import os
from datetime import datetime
from django.core.paginator import Paginator

# global camera_obj
# camera_obj = ObjectDetection()

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
        query = Q(user=self.request.user)
        
        # Get filters
        month = self.request.GET.get("month", "")
        bean_types = self.request.GET.get("type")  # Multiple values
        bean_types = str(bean_types).split("-")
        year = self.request.GET.get("year","")
        farm = self.request.GET.get("farm")
        title = self.request.GET.get("title")
        
        if title:
            query &= Q(title__contains=title)
            
        if month.isdigit():
            query &= Q(date_created__month=int(month))
        
        if year.isdigit():
            query &= Q(date_created__year=int(year))

        if bean_types != ['None']:
            query &= Q(bean_type__in=bean_types)
            
        if farm:
            query &= Q(farm__contains=farm)
        
        queryset = BatchSession.objects.filter(query).order_by("-date_created")
        
        return queryset
        
    def get_context_data(self, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)                            
        context['current_time'] = datetime.now().strftime("%H:%M:%S")
 
        queryset = object_list if object_list is not None else self.object_list
        page_size = self.get_paginate_by(queryset)

        print("PAGESIZE:", page_size)
        if page_size:
            paginator, page, queryset, is_paginated = self.paginate_queryset(
                queryset, page_size
            )
            context = {
                "paginator": paginator,
                "page_obj": page,
                "is_paginated": is_paginated,
                "object_list": queryset,
            }
        else:
            context = {
                "paginator": None,
                "page_obj": None,
                "is_paginated": False,
                "object_list": queryset,
            }
        page_obj = context['page_obj']
        paginator = page_obj.paginator

        # Custom page range calculation
        start_index = max(1, page_obj.number - 2)
        end_index = min(paginator.num_pages + 1, page_obj.number + 3)
        context['page_range'] = range(start_index, end_index)
        return context
        
    def render_to_response(self, context, **response_kwargs):
        # Check if request is AJAX
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            new_batch = self.get_context_data()
            # new_batch = new_batch['page_obj'] 
            html = render_to_string('dashboard/partials/filter_batch.html', {'filtered_batch': new_batch}, request=self.request)
            return JsonResponse({"html": html}, safe=False)

        return super().render_to_response(context, **response_kwargs)
    
class DeleteSessionView(LoginRequiredMixin, DeleteView):
    model = BatchSession
    template_name = "dashboard/partials/deleteSessionView.html"
    success_url = reverse_lazy("dashboard")
    
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    

class AddSession(LoginRequiredMixin, CreateView):
    model = BatchSession
    template_name = "dashboard/addSession.html"
    form_class = BatchSessionForm
    
    def form_valid(self, form):
        batch = form.save(commit=False)
        batch.user = self.request.user
        batch.save()
        self.success_url = reverse_lazy("scan_option", kwargs={"batch_id":batch.batch_id, "title": batch.title})
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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batchSession = BatchSession.objects.get(batch_id=self.kwargs["batch_id"])
        context["objects"] = batchSession
        context["scan_number"] = DefectsDetected.objects.filter(batch=batchSession).order_by("-date_scanned").first()
    
        defects_detected = self.request.POST.getlist("defect")
        defects_array = {}
    
        if self.request.POST.get("defects_count"):
            defects_count = self.request.POST.getlist("defects_count")
            defects_count = list(map(int, defects_count))
            
            for index, defect in enumerate(defects_detected):
                # insert in dict
                defects_array[defect] = defects_count[index]
        
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
        context["first_defects"] = defects_array
        return context
    
    def get_success_url(self):
        batch = get_object_or_404(BatchSession, batch_id=self.kwargs["batch_id"])

        # session scan ends
        if self.request.method == "POST" and self.kwargs["scan_number"] == 2:
            return reverse('camera_next', kwargs={
        "batch_id": batch.batch_id,
        "title": batch.title
    })

        if self.request.method == "POST" and self.kwargs["scan_number"] == 1:
            next_scan_number = 2
        
            return reverse_lazy('scan', kwargs={
                "batch_id": batch.batch_id,
                "title": batch.title,
                "scan_number": next_scan_number
            })
        
    def post(self, request, *args, **kwargs):
        last_scan = DefectsDetected.objects.filter(batch_id=self.kwargs["batch_id"]).order_by('-scan_number').first()
        
        if last_scan:
            last_scan_number = last_scan.scan_number
        else:
            last_scan_number = 0
        
        scan_number = last_scan_number + 1
    
        final_annotated_image = camera_obj.get_frames()
        img_array = cv2.imdecode(np.frombuffer(final_annotated_image, dtype=np.uint8), cv2.IMREAD_COLOR)
        
        if img_array is None:
            raise ValueError("Failed to decode image bytes")
        
        path = r".\static\temp"

            
        if not os.path.exists(path):
            os.makedirs(path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_name = f"{self.request.user}_{timestamp}_image.jpg"  # Change extension to .png if needed

        # Full path to save the frame
        save_path = os.path.join(path, frame_name)
        
        # ======save frame
        success = cv2.imwrite(save_path, img_array)
        
        defects_detected = self.request.POST.getlist("defect")
        defects_array = {}
    
        if self.request.POST.get("defects_count"):
            defects_count = self.request.POST.getlist("defects_count")
            defects_count = list(map(int, defects_count))
            
            for index, defect in enumerate(defects_detected):
                # insert in dict
                defects_array[defect] = defects_count[index]
        
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
        
        with open("static/temp_defects/defects.txt", "a") as file:
            for defect, count in defects_array.items():
                file.write(f"{defect}: {count}\n")
            
        message="Data had been added"
        return redirect(self.get_success_url())
    
class CameraNext(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/camera_next.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        frames = []
        
        temp_path = r".\static\temp"
        image_filenames = [f for f in os.listdir(temp_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        for filename in image_filenames:
            image_path = os.path.join(temp_path, filename)
            
            # store files in variable
            frames.append(filename)

            result = []            
            with open(r".\static\temp_defects\defects.txt", "r") as file:
                for line in file:
                    line = line.strip()
                    if line:  
                        key, value = line.split(":")
                        result.append({key.strip(): value.strip()})
  
        combined = defaultdict(int)

        for d in result:
            for key, value in d.items():
                if not key == "none":
                    combined[key] += int(value)

        # Convert back to normal dict if needed
        result = dict(combined)
        print("RESULTS", result)
        context["frames"] = frames
        context["defects"] = result
        return context

    def post(self, *args, **kwargs):
        frames = []
        final_annotated_images = []
        
        last_scan = DefectsDetected.objects.filter(batch_id=self.kwargs["batch_id"]).order_by('-scan_number').first()
        
        if last_scan:
            last_scan_number = last_scan.scan_number
        else:
            last_scan_number = 0

        scan_number = last_scan_number + 1

        path = r".\static\final_detected_images" 
        temp_path = r".\static\temp"
        image_filenames = [f for f in os.listdir(temp_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]


        for filename in image_filenames:
            image_path = os.path.join(temp_path, filename)
    
            # Read using OpenCV
            image = cv2.imread(image_path)
        
            save_path = os.path.join(path, filename)
            
            # ====== save frame ========
            cv2.imwrite(save_path, image)
            frames.append(filename)
            
            defects_detected = self.request.POST.getlist("defect")
            defects_array = {}

            # remove the image in temp
            os.remove(image_path)
            
            # remove in txt file
            with open("./static/temp_defects/defects.txt", "w") as file:
                pass 
                
        # saving defects
        if self.request.POST.get("defects_count"):
           defects_array = self.request.POST.get("defects_count")
           defects_array = ast.literal_eval(defects_array)
           
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
                
        newScan = DefectsDetected(
            scan_number=scan_number,
            defects_detected=defects_array,
            scanned_image=frames[0],
            batch_id = self.kwargs["batch_id"],
            scanned_image2 = frames[1]
        )
        
        # save frame
        newScan.save()

        message="Data had been added"
        return redirect(self.get_success_url())
        
    def get_success_url(self):
        batch = get_object_or_404(BatchSession, batch_id=self.kwargs["batch_id"])
        return reverse_lazy('view_scans', kwargs={'batch_id': batch.batch_id, 'title': batch.title})
            
class ScanUploadView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan_upload_view.html"
    # success_url=reverse_lazy("scan")
    
    def post(self, request, *args, **kwargs):
        # path = r".\static\final_detected_images"
        # if not os.path.exists(path):
        #     os.makedirs(path)
        frames = []
        final_annotated_images = []
        
        last_scan = DefectsDetected.objects.filter(batch_id=self.kwargs["batch_id"]).order_by('-scan_number').first()
        
        if last_scan:
            last_scan_number = last_scan.scan_number
        else:
            last_scan_number = 0

        scan_number = last_scan_number + 1

        path = r".\static\final_detected_images" 
        temp_path = r".\static\temp"
        image_filenames = [f for f in os.listdir(temp_path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]


        for filename in image_filenames:
            image_path = os.path.join(temp_path, filename)
    
            # Read using OpenCV
            image = cv2.imread(image_path)
        
            save_path = os.path.join(path, filename)
            
            # ====== save frame ========
            cv2.imwrite(save_path, image)
            frames.append(filename)
            
            defects_detected = request.POST.getlist("defect")
            defects_array = {}

            # remove the image in temp
            os.remove(image_path)
                
        # saving defects
        if request.POST.get("defects_count"):
           defects_array = request.POST.get("defects_count")
           defects_array = ast.literal_eval(defects_array)
           
        if not len(defects_array) > 0:
            defects_array = {"none": "none"}
                
        newScan = DefectsDetected(
            scan_number=scan_number,
            defects_detected=defects_array,
            scanned_image=frames[0],
            batch_id = self.kwargs["batch_id"],
            scanned_image2 = frames[1]
        )
        
        # save frame
        newScan.save()

        message="Data had been added"
        return self.get(request, *args, **kwargs)
        

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batchSession = BatchSession.objects.get(batch_id=self.kwargs["batch_id"])
        context["objects"] = batchSession
        return context
    
def ScanUploadDetect(request, *args, **kwargs):
    global camera_obj
    camera_obj = ObjectDetection()
    batch_id = kwargs.get("batch_id")

    batchSession = BatchSession.objects.get(batch_id=batch_id)
    
    annotated_images = []

    path = r".\static\temp"
    if not os.path.exists(path):
            os.makedirs(path)
    
    if request.method == "POST":
        files = request.FILES.getlist('files')
        for idx, uploaded_file in enumerate(files):
            # Reset pointer before multiple reads
            uploaded_file.seek(0)
            file_bytes = np.frombuffer(uploaded_file.read(), np.uint8)

            # Decode using OpenCV
            cv2_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

            # run detection (replace with your logic)
            cv2_image = camera_obj.start_detects(cv2_image)
            
            # save to tmp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            frame_name = f"{request.user}_{timestamp}{idx}_image.jpg"  # Change extension to .png if needed
            
            save_path = os.path.join(path, frame_name)
            cv2.imwrite(save_path, cv2_image)

            
            # Convert to base64 for frontend
            _, buffer = cv2.imencode('.jpg', cv2_image)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')
            
            # Store processed image
            annotated_images.append(frame_b64)

        return render(request, "dashboard/scan_upload_next.html", context={"annotated_images": annotated_images, "defects": camera_obj.defects, "objects": batchSession})

        # return JsonResponse(data={"success":True, "captured_frame":frame_b64})
    
def start_capture(request):
    return render(request, "dashboard/partials/camera_buttons.html")

class ScanOptionView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/scan_option.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        batchSession = BatchSession.objects.get(batch_id=self.kwargs["batch_id"])
        context["objects"] = batchSession   
        return context
  
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
            "full black":[1, "1:1"]
            ,"fsour":[1, "1:1"]
            ,"dried cherry":[1, "1:1"]
            ,"fungus":[1, "1:1"]
            ,"foreign matter":[1, "1:1"]
            ,"sev insect":[5, "5:1"]
            ,"partial black":[3, "3:1"]
            ,"psour":[3, "3:1"]
            ,"parchment":[5, "5:1"]
            ,"floater":[5, "5:1"]
            ,"immature":[5, "5:1"]
            ,"withered":[5, "5:1"]
            ,"shell":[5, "5:1"]
            ,"broken":[5, "5:1"]
            ,"husk":[5, "5:1"]
            ,"slight insect":[10, "10:1"]
            }
        
        defects_list_sum = {}
        
        if all_defects:
            for defects in all_defects:
                defects_detected = defects.defects_detected
                
                # loop through defects detected
                for key, value in defects_detected.items():
                    # sum up all defect count
                    if key in defects_list_sum: 
                        defects_list_sum[key] += value
                    else:
                        if key != "none":
                            defects_list_sum[key] = value
                    
                    

        
        # average
        for defects in defects_list_sum:
            defects_list_sum[defects] = round(defects_list_sum[defects]/2)
                        
        # equivalent full defect values
        for key in defects_list_sum:
            if key in equivalent_values:
                divide = defects_list_sum[key] // equivalent_values[key][0]
                defects_list_sum[key] = defects_list_sum[key], divide, equivalent_values[key][1]
        
        # count full defect
        full_defect_count = 0
        for item in defects_list_sum:
            if type(defects_list_sum[item]) == tuple:
                full_defect_count += defects_list_sum[item][1]
        
        # separate primary defects
        primary_defects_list = {}
        keys_to_delete = []
        for key in defects_list_sum:
            if key in primary_defects_name:
                primary_defects_list[key] = defects_list_sum[key]
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del defects_list_sum[key]
            
        # GRADING
        grading = None
        if len(primary_defects_list) == 0 and full_defect_count < 5:
            grading = "Specialty Grade"
        
        elif full_defect_count <= 8:
            grading = "Premium Grade"
            
        elif full_defect_count <= 23:
            grading = "Exchange Grade"
        
        else:
            grading = "Off-grade"
        context["batch_id"] = batch_id
        context["batch_title"] = batch_title
        context["defects_list_sum"] = defects_list_sum
        context["primary_defects_list"] = primary_defects_list
        context["grading"] = grading
        return context
    
    
# PROFILE VIEW
class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/profile_view.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user        
        context["form"] = ProfileForm(instance=user)
        
        return context

class ProfileEditView(LoginRequiredMixin, FormView):
    template_name = "dashboard/profile_edit.html"
    success_url = reverse_lazy("profile_view") 
    form_class = ProfileForm

    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        form_class = ProfileForm(self.request.POST)
        return form_class

    def form_valid(self, form):
        user_instance = get_object_or_404(User, id=self.request.user.id)
        user_instance.first_name = form.cleaned_data.get("first_name")
        user_instance.last_name = form.cleaned_data.get("last_name")
        user_instance.email = form.cleaned_data.get("email")
        
        if len(form.cleaned_data.get("password")) > 0:
            if form.cleaned_data.get("password") == form.cleaned_data.get("reenter_password"):                
                user_instance.set_password(form.cleaned_data.get("password"))
                user_instance.save()
                update_session_auth_hash(self.request, user_instance)
            else:
                messages.add_message(self.request, messages.WARNING, "Password did not match!")
                self.success_url = reverse_lazy("profile_edit")
            
        user_instance.save()
        if not messages.get_messages(self.request):
            messages.add_message(self.request, messages.SUCCESS, "Profile updated!")
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ProfileForm(instance=self.request.user)
        return context

# OBJECT DETECTION
def check_camera(request):
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2296)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 4080)
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
    
    
    
    

    
