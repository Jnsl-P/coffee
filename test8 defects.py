import cv2
from ultralytics import YOLO
import numpy as np
import os
from image import ImageLink



path = "C:/Users/user/OneDrive/Desktop/New folder/images_iso"
# image_path = r"C:\Users\user\OneDrive\Desktop\New folder\new_img\test.jpg"
image_link = ImageLink()
image_path = image_link.image_path
m_classify = image_link.modeli
m_classify_good_bad = image_link.modelii
m_classify_ii = image_link.modeliii 
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
    if confidence >= 0.7:  # Filter by confidence threshold
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
        
        # filename = os.path.join(path, f"iso_{idx}.jpg")
        # cv2.imwrite(filename, iso_crop)

        # UNCOMMENT======================================
        
        # # CLASSIFY GOOD BAD
        # r_classify_good_bad = m_classify_good_bad(iso_crop)
    
        # for box_gb in r_classify_good_bad.r_classify[0].boxes:
        #     confidence = float(box_gb.conf)  # Confidence score
        #     if confidence >= 0.6:
        #         x, y, w, h = boxes[i]
                
        #         # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
        #         class_id = int(box.cls)
        #         label = m_classify_good_bad.model.names[class_id]  # Access names from the model
        #         # label_text = f"{label}"
        #         # org_point = (x, y - 10)
        #         # # cv2.putText(img, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2) 

        #         # labeling_infos.append({"text": label_text, "org_point": (x, y - 10), "boxes": [(x, y), (x + w, y + h)]})

        #         if label != "good":
                    
        # UNCOMMENT======================================
                            
        # # CLASSIFY DEFECT
        r_classify = m_classify_ii(iso_crop)
        
        for box in r_classify[0].boxes:
            confidence = float(box.conf)  # Confidence score
            if confidence >= 0.6:
                x, y, w, h = boxes[i]
                
                # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), 2)
                class_id = int(box.cls)
                label = m_classify_ii.model.names[class_id]  # Access names from the model
                label_text = f"{label} {confidence}"
                org_point = (x, y - 10)
                # cv2.putText(img, label_text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2) 

                labeling_infos.append({"text": label_text, "org_point": (x, y - 10), "boxes": [(x, y), (x + w, y + h)]})
                
                filename = os.path.join(path, f"{label_text}_iso_{idx}.jpg")
                cv2.imwrite(filename, iso_crop)

for item in labeling_infos:
    cv2.rectangle(img, item["boxes"][0], item["boxes"][1], (0, 0, 0), 2)
    cv2.putText(img, item["text"], item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) 
    

# target_width = 1000
# h, w = img.shape[:2]
# aspect_ratio = h / w
# new_height = int(target_width * aspect_ratio)
# img = cv2.resize(img, (target_width, new_height))        
filename = os.path.join(r"C:\Users\user\OneDrive\Desktop\New folder\prev", f"test8 defects.jpg")
cv2.imwrite(filename, img)
        
# cv2.imshow("Segmented & Classified", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
