import cv2
import time
import numpy as np
from cvlib.object_detection import draw_bbox
from gtts import gTTS
from playsound import playsound
import os
import tempfile
import json
import threading
from ultralytics import YOLO

path = r"object2/best4.pt"
model = YOLO(path)  # Load a pretrained model (e.g., yolov8n.pt, yolov8s.pt, etc.)
screenshot_dir = "./static/images/"
os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
screenshot_path = os.path.join(screenshot_dir, "latest_screenshot.jpg")

class ObjectDetection:
    def __init__(self, video):
        global config_file_path, weights_file_path, labels_path, temp_dir, stop_signal_file,detected_objects_file, detected_labels, detected_objects,screenshot_dir,screenshot_path, classes
        global model
        self.defects = {}
        self.video = video
        self.thread = threading.Thread(target=self.capture,daemon=True)
        self.start_capture = 0


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
        # processed_frame = self.start_detects(self.frame)
        ret, img = cv2.imencode('.jpg', self.frame)
        return img.tobytes()

    def get_last_frame(self):
        cv2.imwrite(screenshot_path, self.start_detects(self.frame))
        
        # print(f"Screenshot saved to {screenshot_path}")
        # self.write_detected_objects(detected_objects)
        
        # ==================== test image ====================
        # cv2.imwrite(screenshot_path, self.start_detects())
        # ==================== test image end ====================

    def start_detects(self,frame):
        # ==================== test image ====================
        # remove frame parameter
        # yolo_path = r"C:\Users\user\OneDrive\Desktop\runs\coffeeebean\best4.pt"
        # model = YOLO(yolo_path)  # Load a pretrained model (e.g., yolov8n.pt, yolov8s.pt, etc.)
        # imagepath = r"object2\467474020_1131571705068305_5639011367866307380_n.jpg"
        # frame = cv2.imread(imagepath, cv2.IMREAD_COLOR)
        # ==================== test image end ====================
        
        results = model(frame)
        annotated_frame = frame.copy()
        detections = results[0]  # First result corresponds to the current frame/image
        
        for box in detections.boxes:
            confidence = float(box.conf)  # Confidence score
            if confidence >= 0.2:  # Filter objects with confidence above 60%
                class_id = int(box.cls)  # Class ID
                label = model.names[class_id]  # Map class ID to the label name
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates

                # Draw the bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 0), 2)  # Green box

                label_text = f"{label}: {confidence:.2f}"
                cv2.putText(annotated_frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
                self.defects[label] = self.defects.get(label, 0) +1
                
        return annotated_frame
         
    def stop(self):
        # cv2.imwrite(screenshot_path, self.start_detects(self.frame))
        print("VIDEO RELEASE STHREAD STOP")
        self.start_capture = 0
        self.thread.join()
        self.video.release()