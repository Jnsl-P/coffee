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
    
        final_annotated_image = camera_obj.get_frames()
        img_array = cv2.imdecode(np.frombuffer(final_annotated_image, dtype=np.uint8), cv2.IMREAD_COLOR)
        
        if img_array is None:
            raise ValueError("Failed to decode image bytes")
        
        path = r".\static\final_detected_images"

            
        if not os.path.exists(path):
            os.makedirs(path)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        frame_name = f"{self.request.user}_{timestamp}_image.jpg"  # Change extension to .png if needed
        


        # Full path to save the frame
        save_path = os.path.join(path, frame_name)
        # ======save frame
        success = cv2.imwrite(save_path, img_array)
        print("Saved:", success, "Path:", save_path)
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
        newScan.save()
        
        message="Data had been added"
        return self.get(request, *args, **kwargs)