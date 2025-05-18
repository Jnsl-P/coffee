import cv2
from ultralytics import YOLO
import numpy as np
import os
from image import ImageLink
from ultralytics.utils.plotting import Annotator, colors

def unsharp_mask(image, sigma=1.0, strength=1.5, kernel_size=(5, 5)):
    # Apply Gaussian blur with specified kernel size
    blurred = cv2.GaussianBlur(image, kernel_size, sigma)
    # Subtract the blurred image from the original
    sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
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

df_boxes = []          # (x, y, w, h) in the crop
df_confidences = []
df_cls_ids = []

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
        # iso_crop = unsharp_mask(iso_crop, sigma=3.0, strength=5.5, kernel_size=(7, 7))
        
        
        # CLASSIFY GOOD BAD
        r_classify_good_bad = m_classify_good_bad(iso_crop)
        
        gb_boxes = []
        gb_confidences = []
        gb_cls_ids = []
    
        for box_gb in r_classify_good_bad[0].boxes:
            conf = float(box_gb.conf)
            if conf >= 0.4:
                x1g, y1g, x2g, y2g = map(int, box_gb.xyxy[0])
                gb_boxes.append([x1g, y1g, x2g - x1g, y2g - y1g])  # (x, y, w, h)
                gb_confidences.append(conf)
                gb_cls_ids.append(int(box_gb.cls))
        
        idxs_gb = cv2.dnn.NMSBoxes(gb_boxes, gb_confidences, score_threshold=0.5,
                           nms_threshold=0.45)
        
        if len(idxs_gb) > 0:
            idxs_gb = idxs_gb.flatten()

            for j in idxs_gb:
                # absolute coords on the crop
                xg, yg, wg, hg = gb_boxes[j]
                x2, y2 = xg + wg, yg + hg
                cls_id_gb = gb_cls_ids[j]
                conf = gb_confidences[j]


                label_gb = m_classify_good_bad.model.names[cls_id_gb]
                

                # CLASSIFY DEFECT
                if label_gb != "good":
                    r_classify_def = m_classify_ii(iso_crop)

                    for box_d in r_classify_def[0].boxes:
                        conf_d = float(box_d.conf)
                        if conf_d >= 0.0:                     # your defect threshold
                            xd1, yd1, xd2, yd2 = map(int, box_d.xyxy[0])
                            df_boxes.append([xd1, yd1, xd2 - xd1, yd2 - yd1])
                            df_confidences.append(conf_d)
                            df_cls_ids.append(int(box_d.cls))

                    # ---------- NMS on defect boxes ----------
                    idxs_df = cv2.dnn.NMSBoxes(df_boxes, df_confidences,
                                            score_threshold=0.5,
                                            nms_threshold=0.45)

                    if len(idxs_df) > 0:
                        idxs_df = idxs_df.flatten()
                        for k in idxs_df:
                            xd, yd, wd, hd = df_boxes[k]
                            x2d, y2d = xd + wd, yd + hd
                            cls_id_d = df_cls_ids[k]
                            conf_d   = df_confidences[k]

                            # draw on iso_crop
                            lab_d = m_classify_ii.model.names[cls_id_d]
                            text_d = f"{lab_d}"
                            cv2.putText(iso_crop, text_d, (xd, max(25, yd - 10)),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)                          

                            labeling_infos.append({"text": text_d, 
                                                   "org_point": (x, y - 10), 
                                                   "boxes": [(x, y), (x + w, y + h)]
                                                   })
                            
                            filename = os.path.join(path, f"iso_{idx}_{text_d}.jpg")
                            cv2.imwrite(filename, iso_crop)
                    
for item in labeling_infos:
    cv2.rectangle(img, item["boxes"][0], item["boxes"][1], (0, 0, 0), 2)
    cv2.putText(img, item["text"], item["org_point"], cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) 
    

# target_width = 1000
# h, w = img.shape[:2]
# aspect_ratio = h / w
# new_height = int(target_width * aspect_ratio)
# img = cv2.resize(img, (target_width, new_height))        
filename = os.path.join(r"C:\Users\user\OneDrive\Desktop\New folder\prev", f"good_bad.jpg")
cv2.imwrite(filename, img)
        
# cv2.imshow("Segmented & Classified", img)
# cv2.waitKey(0)
# cv2.destroyAllWindows()
