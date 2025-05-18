import cv2
import os
import torch
import numpy as np
from ultralytics import YOLO
from image import ImageLink
from ultralytics.utils.plotting import Annotator, colors
import torchvision.ops as ops

def unsharp_mask(image, sigma=1.0, strength=1.5, kernel_size=(5, 5)):
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
    return sharpened

# Image and model setup
imagelink = ImageLink() 
m_classify = imagelink.modeli 
m_classifyiii = imagelink.modeliii

img_path = imagelink.image_path

img = cv2.imread(img_path)
if img is None:
    raise ValueError(f"Image could not be loaded from path: {img_path}")

# Run classification model
classify = m_classify(img)
detections = classify[0]


boxes_xyxy = []  # [x1, y1, x2, y2]
scores = []
class_ids = []

# Parse detections
for box in detections.boxes:
    conf = float(box.conf)
    if conf >= 0.4:
        x1, y1, x2, y2 = map(float, box.xyxy[0])
        boxes_xyxy.append([x1, y1, x2, y2])
        scores.append(conf)
        class_ids.append(int(box.cls))

# Apply NMS
boxes_tensor = torch.tensor(boxes_xyxy)
scores_tensor = torch.tensor(scores)
nms_threshold = 0.4
keep_indices = ops.nms(boxes_tensor, scores_tensor, nms_threshold)

# Draw bounding boxes with class labels
# for idx in keep_indices:
#     x1, y1, x2, y2 = map(int, boxes_tensor[idx])
#     class_id = m_classify.model.names[class_ids[idx]] 
#     conf = scores[idx]

#     cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

#     label = f"Class {class_id}: {conf:.2f}"
#     (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
#     cv2.rectangle(img, (x1, y1 - text_h - 4), (x1 + text_w, y1), (0, 255, 0), -1)
#     cv2.putText(img, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# output_path = r"C:\Users\user\OneDrive\Desktop\New folder\prev\good_bad.jpg"
# cv2.imwrite(output_path, img)

blurred = cv2.GaussianBlur(img, (71, 71), 0)
mask = np.zeros_like(img)

for idx in keep_indices:
    x1, y1, x2, y2 = map(int, boxes_tensor[idx])  # Use detection box
    cls_id = class_ids[idx]
    label = m_classify.model.names[cls_id] 
    conf = scores[idx]
    
    if label == "bad":
        # KEEP THIS — copies only "bad" beans from original image
        mask[y1:y2, x1:x2] = img[y1:y2, x1:x2]

# Merge: keep "bad" bean areas from original image, blur the rest
focused = np.where(mask.any(axis=2, keepdims=True), mask, blurred)

# defect detect
df_result = m_classifyiii(focused)
annotator = Annotator(focused.copy(), line_width=2)  # Use focused image, not img
names = m_classifyiii.model.names

if df_result[0].boxes is not None:
    boxes = df_result[0].boxes.xyxy.cpu().tolist()
    clss = df_result[0].boxes.cls.cpu().tolist()
    confs = df_result[0].boxes.conf.cpu().tolist()

    for box, cls, conf in zip(boxes, clss, confs):
        if  conf > 0.35:
            label = f"{names[int(cls)]} {conf:.2f}"
            annotator.box_label(box, label, color=colors(int(cls), True))

filename = os.path.join(r"C:\Users\user\OneDrive\Desktop\New folder\prev", f"test_segment2.jpg")
cv2.imwrite(filename, annotator.result())  # Save annotated image



# Save outputs
# cv2.imwrite(r"C:\Users\user\OneDrive\Desktop\New folder\prev\no-blur.jpg", img)
# cv2.imwrite(r"C:\Users\user\OneDrive\Desktop\New folder\prev\focused.jpg", focused)

