import torch
import cv2
import os
from ultralytics import YOLO
import numpy as np
from random import randint

def random_with_N_digits(n):
    """Generate a random number with N digits"""
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

# Load the YOLOv11 model_classification (adjust the path to your trained weights)
model_classification = YOLO(r"last.pt")  # Replace with your trained YOLO model_classification

# Input and output folders
input_folder = r"C:\Users\user\OneDrive\Desktop\New folder (3)\New good"
output_folder = r"C:\Users\user\OneDrive\Desktop\all_defects\2\zpreveiw"
os.makedirs(output_folder, exist_ok=True)

# Process each image in the input folder
for img_name in os.listdir(input_folder):
    img_path = os.path.join(input_folder, img_name)
    img = cv2.imread(img_path)
    

    # Run YOLOv11 inference
    results_classification = model_classification(img)[0]

    for box in results_classification.boxes.data:
        x1, y1, x2, y2, score, class_id = box.tolist()
        if(score > 0.7):
            # Draw bounding box
            # cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), 2)

            # Crop detected object
            iso_crop = img[int(y1):int(y2), int(x1):int(x2)]

            # Save the cropped image
            crop_filename = f"iso_{random_with_N_digits(8)}.jpg"
            crop_path = os.path.join(output_folder, crop_filename)
            cv2.imwrite(crop_path, iso_crop)
            print(f"Saved cropped image: {crop_path}")

print("Processing completed.")
