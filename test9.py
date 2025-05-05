import cv2
from ultralytics import YOLO
import numpy as np
import os
from image import ImageLink
import random


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

def unsharp_mask(image, sigma=1.0, strength=1.5, kernel_size=(5, 5)):
    # Apply Gaussian blur with specified kernel size
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    # Subtract the blurred image from the original
    sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
    return sharpened

def sharpness2(image):

# Define sharpening kernel
    kernel = np.array([[0, -1, 0],
                    [-1, 5,-1],
                    [0, -1, 0]])

    # Apply sharpening filter
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

path = "C:/Users/user/OneDrive/Desktop/New folder/images_iso"
imagelink = ImageLink()

m_classify = imagelink.modeli
m_classify_good_bad = imagelink.modelii
m_classify_ii = imagelink.modeliii
image_path = imagelink.image_path
img = cv2.imread(image_path)
classify = m_classify(img)

detections = classify[0]  # First result corresponds to the current frame/image

# Extract bounding boxes, confidence scores, and class IDs
boxes = []
boxes2 = []
confidences = []
class_ids = []

labeling_infos = []

for box in detections.boxes:
    confidence = float(box.conf)  # Confidence score
    if confidence >= 0.8:  # Filter by confidence threshold
        class_id = int(box.cls)  # Class ID
        x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
        boxes.append([x1, y1, x2 - x1, y2 - y1])  # OpenCV expects width and height format
        boxes2.append([x1, y1, x2, y2]) # for isolation
        confidences.append(confidence)
        class_ids.append(class_id)

# Apply Non-Maximum Suppression (NMS)
nms_indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

# Check if there are any indices returned by NMS
if len(nms_indices) > 0:
    # Flatten `nms_indices` if it's a 2D array
    nms_indices = nms_indices.flatten()

    # Draw the bounding boxes for the filtered indices
    for idx, i in enumerate(nms_indices):
        x, y, w, h = boxes[i]
        x1, y1, x2, y2 = boxes2[i] # for isolation
                    
        b_mask = np.zeros_like(img[:, :, 0], dtype=np.uint8)
        
        cv2.rectangle(b_mask, (x1, y1), (x2, y2), 255, -1)
        isolated = cv2.bitwise_and(img, img, mask=b_mask)
        
        # Crop image to object region
        iso_crop = isolated[y1:y2, x1:x2]
        
        # resize isolated img
        target_width = 640
        h, w = iso_crop.shape[:2]
        aspect_ratio = h / w
        new_height = int(target_width * aspect_ratio)
        iso_crop = cv2.resize(iso_crop, (target_width, new_height))
        
        # iso_crop = unsharp_mask(iso_crop, sigma=3.0, strength=1.5, kernel_size=(7, 7))
        # iso_crop = sharpness2(iso_crop)
        # iso_crop = lab(iso_crop)
        # filename = os.path.join(path, f"iso_{idx}.jpg")
        # cv2.imwrite(filename, iso_crop)

        # CLASSIFY GOOD BAD
        r_classify_good_bad = m_classify_good_bad(iso_crop)
        for box_gb in r_classify_good_bad[0].boxes:
            confidence = float(box_gb.conf)  # Confidence score
            if confidence >= 0.4:
                gb_x, gb_y, gb_w, gb_h = boxes[i]
                
                # cv2.rectangle(img, (x, y), (x + w, y + h), (255, 255, 255), 2)
                class_id = int(box_gb.cls)
                gb_label = m_classify_good_bad.model.names[class_id]  # Access names from the model
                # label_text = f"{label}"
                # cv2.putText(img, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2) 

                # labeling_infos.append({"text": label_text, "org_point": (x, y - 10), "boxes": [(x, y), (x + w, y + h)]})
                labeling_infos.append({"text": gb_label, "org_point": (gb_x, gb_y - 10), "boxes": [(gb_x, gb_y), (gb_x + gb_w, gb_y + gb_h)]})
                
                if gb_label != "good":
                    
        # UNCOMMENT======================================
                            
        # CLASSIFY DEFECT
                    r_classify = m_classify_ii(iso_crop)
                    
          
                    for box in r_classify[0].boxes:
                        confidence = float(box.conf)  # Confidence score
                        if confidence >= 0.0:
                            x, y, w, h = boxes[i]
                            
                            # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
                            class_id = int(box.cls)
                            label = m_classify_ii.model.names[class_id]  # Access names from the model
                            label_text = f"{label} {round(confidence, 2)}"
                            org_point = (x, y - 10)
                            # cv2.putText(img, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2) 
                            
                                
                            
                            labeling_infos.append({"text": label_text, "org_point": org_point, "boxes": [(x, y), (x + w, y + h)]})
                            filename = os.path.join(path, f"{label_text}_iso_{random.randrange(1234324, 12343249)}.jpg")
                            cv2.imwrite(filename, iso_crop)
                        
                                                        


for item in labeling_infos:

    if item["text"] == "bad":
        cv2.rectangle(img, item["boxes"][0], item["boxes"][1], (0, 219, 51), 2)
        cv2.putText(img, "", item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 219, 51), 2)
    if item["text"] != "good" and item["text"] !=  "bad": 
        cv2.rectangle(img, item["boxes"][0], item["boxes"][1], (0, 219, 51), 2)
        cv2.putText(img, item["text"], item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 219, 51), 2)

# target_width = 1000
# h, w = img.shape[:2]
# aspect_ratio = h / w
# new_height = int(target_width * aspect_ratio)
# img = cv2.resize(img, (target_width, new_height))        
filename = os.path.join(r"C:\Users\user\OneDrive\Desktop\New folder\prev", f"good_bad_2.jpg")
cv2.imwrite(filename, img)
        
# cv2.imshow("Segmented & Classified", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
