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

config_file_path = r"C:\Users\user\OneDrive\Desktop\CoffeeBeanProject\object\yolov3.cfg"
weights_file_path = r"C:\Users\user\OneDrive\Desktop\CoffeeBeanProject\object\yolov3.weights"
labels_path = r"C:\Users\user\OneDrive\Desktop\CoffeeBeanProject\object\coco.names"

# Temporary directory for saving the stop signal and detected objects
temp_dir = tempfile.gettempdir()
stop_signal_file = os.path.join(temp_dir, "stop_signal.txt")
detected_objects_file = os.path.join(temp_dir, "detected_objects.json")

detected_labels = []
detected_objects = []  # List to store detailed object info
screenshot_dir = "./static/images/"
os.makedirs(screenshot_dir, exist_ok=True)  # Ensure the directory exists
screenshot_path = os.path.join(screenshot_dir, "latest_screenshot.jpg")

# Load COCO class labels
with open(labels_path, "r") as f:
    classes = [line.strip() for line in f.readlines()]

class ObjectDetection:
    def __init__(self, video):
        global config_file_path, weights_file_path, labels_path, temp_dir, stop_signal_file,detected_objects_file, detected_labels, detected_objects,screenshot_dir,screenshot_path, classes
        self.video = video
        self.thread = threading.Thread(target=self.capture,daemon=True)
        self.start_capture = 0

        # Load YOLO
        self.net = cv2.dnn.readNet(weights_file_path, config_file_path)

    def __del__(self):
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
        print(f"Screenshot saved to {screenshot_path}")
        self.write_detected_objects(detected_objects)

    def start_detects(self, frame):
        height, width = frame.shape[:2]

        # Convert the frame to a YOLO-compatible blob
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        self.net.setInput(blob)

        # Get YOLO layer names
        layer_names = self.net.getLayerNames()
        output_layers = [layer_names[i - 1] for i in self.net.getUnconnectedOutLayers()]

        # Forward pass to get detections
        detections = self.net.forward(output_layers)

        # Convert detections to NumPy for vectorized processing
        boxes, confidences, class_ids = [], [], []
        for output in detections:
            output = np.array(output)  # Ensure output is a NumPy array
            confidences_all = output[:, 5:]  # Confidence scores for all classes
            class_ids_all = np.argmax(confidences_all, axis=1)  # Best class ID per detection
            confidence_values = confidences_all[np.arange(len(confidences_all)), class_ids_all]  # Max confidence values

            # Filter detections by confidence threshold
            mask = confidence_values > 0.5
            filtered_detections = output[mask]
            filtered_class_ids = class_ids_all[mask]
            filtered_confidences = confidence_values[mask]

            # Calculate bounding boxes
            filtered_boxes = filtered_detections[:, 0:4] * np.array([width, height, width, height])
            filtered_boxes = filtered_boxes.astype("int")

            for box, class_id, confidence in zip(filtered_boxes, filtered_class_ids, filtered_confidences):
                (centerX, centerY, box_width, box_height) = box
                x = int(centerX - (box_width / 2))
                y = int(centerY - (box_height / 2))

                boxes.append([x, y, int(box_width), int(box_height)])
                confidences.append(float(confidence))
                class_ids.append(class_id)

        # Apply Non-Maximum Suppression (NMS)
        indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        # Draw bounding boxes and labels
        if len(indices) > 0:
            for i in indices.flatten():
                x, y, w, h = boxes[i]
                label = classes[class_ids[i]]
                confidence = confidences[i]
                label_text = f"{label}: {confidence:.2f}"
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    frame,
                    label_text,
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2,
                )

                # Avoid duplicates in detected labels and objects
                if label not in detected_labels:
                    detected_labels.append(label)
                detected_objects.append(
                    {"object_name": label, "confidence": f"{confidence:.2f}"}
                )
        return frame


    def stop(self):
        # cv2.imwrite(screenshot_path, self.start_detects(self.frame))
        print("VIDEO RELEASE STHREAD STOP")
        self.start_capture = 0
        self.thread.join()
        self.video.release()
        
    # ======================== custom ========================

    # Function to write the stop signal
    def set_stop_signal(self):
        with open(stop_signal_file, "w") as f:
            f.write("stop")

    # Function to clear the stop signal
    def clear_stop_signal(self):
        if os.path.exists(stop_signal_file):
            os.remove(stop_signal_file)

    # Function to check if the stop signal exists
    def check_stop_signal(self):
        return os.path.exists(stop_signal_file)

    # Function to write detected objects to a shared file
    def write_detected_objects(self, objects):
        with open(detected_objects_file, "w") as f:
            json.dump(objects, f)

    def speech(self, text):
        if text:
            tts = gTTS(text=text, lang="en")
            temp_path = os.path.join(tempfile.gettempdir(), "speech.mp3")
            tts.save(temp_path)
            playsound(temp_path)
            os.remove(temp_path)

# if __name__ == "__main__":
    # detect_objects_and_generate_speech()
