from image import ImageLink

import os
import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
# Load the image
imagelink = ImageLink() 
model = imagelink.modeli
image_path = imagelink.image_path
im0 = cv2.imread(image_path)

# Resize image while maintaining aspect ratio
target_width = 800
h, w = im0.shape[:2]
aspect_ratio = h / w
new_height = int(target_width * aspect_ratio)
im0 = cv2.resize(im0, (target_width, new_height))

# Run inference
results = model.predict(im0)

# Annotate results with bounding boxes
annotator = Annotator(im0, line_width=2)
names = model.model.names

if results[0].boxes is not None:
    boxes = results[0].boxes.xyxy.cpu().tolist()
    clss = results[0].boxes.cls.cpu().tolist()
    confs = results[0].boxes.conf.cpu().tolist()

    for box, cls, conf in zip(boxes, clss, confs):
        # if names[int(cls)] == "good":    
        #     if conf > 0.35:
        #         label = f"{names[int(cls)]} {conf:.2f}"
        #         annotator.box_label(box, label, color=colors(int(cls), True))
        # if names[int(cls)] == "bad":    
        #     if conf > 0.35:
        #         label = f"{names[int(cls)]} {conf:.2f}"
        #         annotator.box_label(box, label, color=colors(int(cls), True))
        if conf > 0.5:
            label = f"{names[int(cls)]} {conf:.2f}"
            annotator.box_label(box, label, color=colors(int(cls), True))

# Display the output image
filename = os.path.join(r"C:\Users\user\OneDrive\Desktop\New folder\prev", f"test_segment.jpg")
cv2.imwrite(filename, im0)
