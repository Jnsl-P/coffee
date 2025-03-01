from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, DetailView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import BatchSession, DefectsDetected
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView
from .forms import BatchSessionForm, ProfileForm
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash

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
    
    # def get_context_data(self, *args, **kwargs):
    #     context = super().get_context_data(**kwargs)                            
    #     # context['current_time'] =  datetime.now()        
    #     context['current_time'] = datetime.now().strftime("%H:%M:%S")
        
    #     page_obj = context['page_obj']
    #     print(page_obj)
    #     paginator = page_obj.paginator

    #     # Custom page range calculation
    #     start_index = max(1, page_obj.number - 2)
    #     end_index = min(paginator.num_pages + 1, page_obj.number + 3)
    #     context['page_range'] = range(start_index, end_index)
    #     return context
    
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
            "full black":[1, "1:1"]
            ,"full sour":[1, "1:1"]
            ,"dried cherry":[1, "1:1"]
            ,"fungus":[1, "1:1"]
            ,"foreign matter":[1, "1:1"]
            ,"severe insect Damage":[5, "5:1"]
            ,"partial black":[3, "3:1"]
            ,"partial sour":[3, "3:1"]
            ,"parchment":[5, "5:1"]
            ,"floater":[5, "5:1"]
            ,"immature":[5, "5:1"]
            ,"withered":[5, "5:1"]
            ,"shell":[5, "5:1"]
            ,"broken":[5, "5:1"]
            ,"husk":[5, "5:1"]
            ,"slight insect damage":[10, "10:1"]
            }
        
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
        for key in defects_list_sum:    
            if key in equivalent_values:
                divide = defects_list_sum[key] // equivalent_values[key][0]
                defects_list_sum[key] = defects_list_sum[key], divide, equivalent_values[key][1]
        
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
    
    
    
    

    
