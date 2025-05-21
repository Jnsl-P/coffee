import random
import cv2
import numpy as np
import os
import threading
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
import torchvision.ops as ops
import torch

from ultralytics import YOLO
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


screenshot_dir = "./static/images/"
os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
screenshot_path = os.path.join(screenshot_dir, "latest_screenshot.jpg")

class ObjectDetection:
    global screenshot_dir,screenshot_path, model_segmentation, model
    
    def __init__(self, video=None):
        self.defects = {}
        self.video = video
        self.thread = threading.Thread(target=self.capture,daemon=True)
        self.start_capture = 0
        
        # self.model_segmentation = YOLO(r"c:\Users\user\OneDrive\Desktop\segmentation_models\segment11\train\weights\last.pt")
        self.model_good_bad = YOLO(r'C:\Users\user\OneDrive\Desktop\coffee_test\coffee\apps\dashboard\object_detection\models\new_model\1_good_bad.pt')
        self.model_classification = YOLO(r'C:\Users\user\OneDrive\Desktop\coffee_test\coffee\apps\dashboard\object_detection\models\new_model\2_defect_detection.pt')

    def __del__(self):
        self.video.release()
        print("RELEASE...")
        self.stop()

    def start(self):
        if self.video:
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
        captured = self.start_detects(image_frame=self.frame)
        return captured
    
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
    
    def start_detects(self, image_frame):
        try:
            # ==================== YOLO Model Inference ====================
            self.frame = image_frame
            labeling_infos = []

            # **** SEGMENTATION ****
            segment_results = self.model_good_bad(self.frame)[0] 
            boxes = []
            confidences = []
            boxes_xyxy = []  # [x1, y1, x2, y2]
            scores = []
            class_ids = []
            
            for box in segment_results.boxes:
                confidence = float(box.conf)  
                if confidence >= 0.4:  # Filter by confidence threshold
                    x1, y1, x2, y2 = map(float, box.xyxy[0])
                    boxes_xyxy.append([x1, y1, x2, y2])
                    scores.append(confidence)
                    class_ids.append(int(box.cls))
                    
            # Apply NMS (Non-Maximum Suppression) 
            # segment_nms_indices = self.apply_nms(boxes, confidences)
            
            boxes_tensor = torch.tensor(boxes_xyxy)
            scores_tensor = torch.tensor(scores)
            nms_threshold = 0.4
            keep_indices = ops.nms(boxes_tensor, scores_tensor, nms_threshold)
            
            blurred = cv2.GaussianBlur(self.frame, (71, 71), 0)
            mask = np.zeros_like(self.frame)
            
            for idx in keep_indices:
                x1, y1, x2, y2 = map(int, boxes_tensor[idx])  # Use detection box
                cls_id = class_ids[idx]
                label = self.model_good_bad.model.names[cls_id] 
                conf = scores[idx]
                
                if label == "bad":
                    # KEEP THIS — copies only "bad" beans from original image
                    mask[y1:y2, x1:x2] = self.frame[y1:y2, x1:x2]
            
            # Merge: keep "bad" bean areas from original image, blur the rest
            focused = np.where(mask.any(axis=2, keepdims=True), mask, blurred)

            # defect detect
            df_result = self.model_classification(focused)
            annotator = Annotator(self.frame, line_width=2)  # Use focused image, not img
            names = self.model_classification.model.names

            if df_result[0].boxes is not None:
                boxes = df_result[0].boxes.xyxy.cpu().tolist()
                clss = df_result[0].boxes.cls.cpu().tolist()
                confs = df_result[0].boxes.conf.cpu().tolist()

                for box, cls, conf in zip(boxes, clss, confs):
                    if  conf > 0.3:
                        label = f"{names[int(cls)]}"
                        annotator.box_label(box, label, color=colors(int(cls), True))
                        self.defects[label] = self.defects.get(label, 0) + 1
                        
            annotated_frame = annotator.result()                
            return annotated_frame
        except Exception as err:
            print("ERROR:", err)
         
    def stop(self):
        print("VIDEO RELEASE STHREAD STOP")
        self.start_capture = 0
        self.thread.join()
        self.video.release()