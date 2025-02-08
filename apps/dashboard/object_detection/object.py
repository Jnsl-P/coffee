import cv2
import numpy as np
import os
import threading
from ultralytics import YOLO

path = r"apps\dashboard\object_detection\last.pt"
model = YOLO(path)  # Load a pretrained model (e.g., yolov8n.pt, yolov8s.pt, etc.)
screenshot_dir = "./static/images/"
os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
screenshot_path = os.path.join(screenshot_dir, "latest_screenshot.jpg")

class ObjectDetection:
    global screenshot_dir,screenshot_path, model
    
    def __init__(self, video):
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
        ret, img = cv2.imencode('.jpg', self.frame)
        return img.tobytes()

    def get_last_frame(self):
        captured = self.start_detects()
        self.final_annotated_image = captured
        return self.final_annotated_image
        

    def start_detects(self, confidence_threshold=0.2):
        try:
            # uncomment the following lines to test with an image file
            # ==================== test image ====================
            
            image = "422c69cd-4043-471f-9708-9f164b391172.jpg"
            imagepath = "apps/dashboard/object_detection/" + image
            self.frame = cv2.imread(imagepath, cv2.IMREAD_COLOR)
            
            # ==================== test image ====================


            # ==================== YOLO Model Inference ====================
            self.results = model(self.frame)
            # annotated_frame = self.frame.copy()

            detections = self.results[0]  # First result corresponds to the current frame/image

            # Extract bounding boxes, confidence scores, and class IDs
            boxes = []
            confidences = []
            class_ids = []

            for box in detections.boxes:
                confidence = float(box.conf)  # Confidence score
                if confidence >= confidence_threshold:  # Filter by confidence threshold
                    class_id = int(box.cls)  # Class ID
                    x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                    boxes.append([x1, y1, x2 - x1, y2 - y1])  # OpenCV expects width and height format
                    confidences.append(confidence)
                    class_ids.append(class_id)

            # Apply Non-Maximum Suppression (NMS)
            nms_indices = cv2.dnn.NMSBoxes(boxes, confidences, confidence_threshold, 0.1)

            # Check if there are any indices returned by NMS
            if len(nms_indices) > 0:
                # Flatten `nms_indices` if it's a 2D array
                nms_indices = nms_indices.flatten()

                # Draw the bounding boxes for the filtered indices
                for i in nms_indices:
                    x, y, w, h = boxes[i]
                    class_id = class_ids[i]
                    label = model.names[class_id]
                    confidence = confidences[i]

                    # Draw the bounding box
                    cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 0, 0), 2)

                    # Label the box
                    label_text = f"{label}: {confidence:.2f}"
                    cv2.putText(self.frame, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
                    
                    # Update defects dictionary
                    self.defects[label] = self.defects.get(label, 0) + 1
                    
            return self.frame
        except Exception as err:
            print(err)
        
    def custom_annotated_frame_percentage(self, confidence_threshold):
        annotated_frame = self.frame.copy()
        detections = self.results[0]  # First result corresponds to the current frame/image
        
        for box in detections.boxes:
            confidence = float(box.conf)  # Confidence score
            if confidence >= confidence_threshold:  # Filter objects with confidence above 60%
                class_id = int(box.cls)  # Class ID
                label = model.names[class_id]  # Map class ID to the label name
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates

                # Draw the bounding box
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 0), 2)  # Green box

                label_text = f"{label}: {confidence:.2f}"
                cv2.putText(annotated_frame, label_text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2)
                self.defects[label] = self.defects.get(label, 0) +1
                
        return annotated_frame

         
    def stop(self):
        print("VIDEO RELEASE STHREAD STOP")
        self.start_capture = 0
        self.thread.join()
        self.video.release()