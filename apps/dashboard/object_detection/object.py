import random
import cv2
import numpy as np
import os
import threading
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors

# path = r"apps\dashboard\object_detection\yolo11n-seg.pt"
# model = YOLO(path)  # Load a pretrained model (e.g., yolov8n.pt, yolov8s.pt, etc.)

screenshot_dir = "./static/images/"
os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
screenshot_path = os.path.join(screenshot_dir, "latest_screenshot.jpg")

class ObjectDetection:
    global screenshot_dir,screenshot_path, model_segmentation, model
    
    def __init__(self, video):
        self.defects = {}
        self.video = video
        self.thread = threading.Thread(target=self.capture,daemon=True)
        self.start_capture = 0
        
        self.model_segmentation = YOLO(r"c:\Users\user\OneDrive\Desktop\segmentation_models\segment11\train\weights\last.pt")
        self.model_good_bad = YOLO(r"c:\Users\user\OneDrive\Desktop\good_bad_bean_models\b_4\train\weights\last.pt")
        self.model_classification = YOLO(r"c:\Users\user\OneDrive\Desktop\model_versions\a_2\train\weights\last.pt")

    def __del__(self):
        self.video.release()
        print("RELEASE...")
        self.stop()

    def start(self):
        self.start_capture = 1
        self.ret, self.frame = self.video.read()
        self.thread.start()

    def capture(self):
        if self.video:
            while self.start_capture:
                ret, frame = self.video.read()
                self.frame = frame

    def get_frames(self):
        ret, img = cv2.imencode('.jpg', self.frame)
        return img.tobytes()

    def get_last_frame(self):
        captured = self.start_detects()
        return captured
    
        # # for custom percent confidence
        # self.final_annotated_image = captured
        # return self.final_annotated_image
    
    def unsharp_mask(image, sigma=1.0, strength=1.5, kernel_size=(5, 5)):
        # Apply Gaussian blur with specified kernel size
        blurred = cv2.GaussianBlur(image, kernel_size, sigma)
        # Subtract the blurred image from the original
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        return sharpened
    
    def lab(img):
        # Convert to LAB color space
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

        # Split into L, A, B
        l, a, b = cv2.split(lab)

        # Apply CLAHE to Lightness only
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        l_clahe = clahe.apply(l)

        # Merge and convert back to BGR
        enhanced_lab = cv2.merge((l_clahe, a, b))
        enhanced_img = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        return enhanced_img
    
    def sharpness2(image):

    # Define sharpening kernel
        kernel = np.array([[0, -1, 0],
                        [-1, 5,-1],
                        [0, -1, 0]])

        # Apply sharpening filter
        sharpened = cv2.filter2D(image, -1, kernel)
        return sharpened
        
    def apply_nms(self, boxes, confidences):
        nms_indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        
        if len(nms_indices) > 0:
            nms_indices = nms_indices.flatten()
        return nms_indices   

    def start_detects(self, confidence_threshold=0.2):
        try:
            # uncomment the following lines to test with an image file
            # ==================== test image ====================
            
            # image_name = r"c:\Users\user\OneDrive\Downloads\116af4ec-8c06-4533-858a-3e60fabe0e61.jpg"
            # imagepath = "apps/dashboard/object_detection/" + image_name
            # sample_image = cv2.imread(image_name)
            
            # ==================== test image ====================


            # ==================== YOLO Model Inference ====================

            labeling_infos = []
            # **** SEGMENTATION ****
            # segment_results = self.model_segmentation(sample_image)[0] 
            segment_results = self.model_segmentation(self.frame)[0] 
            boxes = []
            confidences = []
            
            for box in segment_results.boxes:
                confidence = float(box.conf)  
                if confidence >= 0.9:  # Filter by confidence threshold
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    boxes.append([x1, y1, x2 - x1, y2 - y1])  # OpenCV expects width and height format
                    confidences.append(confidence)
                    
            # Apply NMS (Non-Maximum Suppression) 
            segment_nms_indices = self.apply_nms(boxes, confidences)
            
            # Draw the bounding boxes for the filtered indices
            for idx, i in enumerate(segment_nms_indices):
                x, y, w, h = boxes[i]
                            
                b_mask = np.zeros_like(self.frame[:, :, 0], dtype=np.uint8)
                
                cv2.rectangle(b_mask, (x, y), ((x + w), (h + y)), 255, -1)
                isolated = cv2.bitwise_and(self.frame, self.frame, mask=b_mask)
                
                # Crop image to object region
                iso_crop = isolated[y:(h + y), x:(x + w)]
                
                # resize isolated img
                target_width = 640
                h, w = iso_crop.shape[:2]
                aspect_ratio = h / w
                new_height = int(target_width * aspect_ratio)
                iso_crop = cv2.resize(iso_crop, (target_width, new_height))
                
                # iso_crop = self.unsharp_mask(iso_crop, sigma=3.0, strength=5.5, kernel_size=(7, 7))
                # iso_crop = unsharp_mask(iso_crop, sigma=3.0, strength=5.5, kernel_size=(7, 7))
                
                # ======== CLASSIFY GOOD OR BAD BEAN ========
                
                good_bad_output = self.model_good_bad(iso_crop)[0]

                if hasattr(good_bad_output, "boxes") and len(good_bad_output.boxes) > 0:
                    top_box = good_bad_output.boxes[0]
                    if float(top_box.conf) > 0.5:
                        gb_label = self.model_good_bad.model.names[int(top_box.cls)]
                        x, y, w, h = boxes[i]
                        
                        labeling_infos.append({"text": gb_label, "org_point": (x, y - 10), "boxes": [(x, y), (x + w, y + h)]})
                
                        # ======== CLASSIFY TYPES OF DEFECT ========
                        if gb_label != "good":
                            classification_results = self.model_classification(iso_crop)

                            c_boxes = []
                            c_confidences = []
                            c_class_ids = []

                            if hasattr(classification_results[0], "boxes") and len(classification_results[0].boxes) > 0:
                                for c_box in classification_results[0].boxes:
                                    confidence = float(c_box.conf)
                                    if confidence > 0.6:
                                        class_id = int(c_box.cls)
                                        x1, y1, x2, y2 = map(int, c_box.xyxy[0])
                                        c_boxes.append([x1, y1, x2 - x1, y2 - y1])
                                        c_confidences.append(confidence)
                                        c_class_ids.append(class_id)

                                if len(c_boxes) > 0:
                                    c_nms = self.apply_nms(c_boxes, c_confidences)
                                    for i in c_nms:
                                        class_id = int(c_class_ids[i])
                                        label = self.model_classification.model.names[class_id]
                                        label_text = f"{label} {round(c_confidences[i], 2)}"
                                        labeling_infos.append({
                                            "text": label_text,
                                            "org_point": (x, y - 10),
                                            "boxes": [(x, y), (x + w, y + h)]
                                        })
                                        self.defects[label] = self.defects.get(label, 0) +1
            annotated_frame = self.frame
            
            for item in labeling_infos:
                cv2.rectangle(annotated_frame, item["boxes"][0], item["boxes"][1], (0, 0, 0), 1)
                cv2.putText(annotated_frame, item["text"], item["org_point"], cv2.FONT_HERSHEY_SIMPLEX,  0.2, (0, 0, 0), 1) 
                # if item["text"] == "bad":
                #     cv2.rectangle(annotated_frame, item["boxes"][0], item["boxes"][1], (0, 0, 0), 1)
                #     cv2.putText(annotated_frame, "", item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 0, 0), 1)
                # if item["text"] != "good" and item["text"] !=  "bad": 
                #     cv2.rectangle(annotated_frame, item["boxes"][0], item["boxes"][1], (0, 0, 0), 1)
                #     cv2.putText(annotated_frame, item["text"], item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.2, (0, 0, 0), 1)

                
            return annotated_frame
        except Exception as err:
            print("ERROR:", err)
            

         
    def stop(self):
        print("VIDEO RELEASE STHREAD STOP")
        self.start_capture = 0
        self.thread.join()
        self.video.release()