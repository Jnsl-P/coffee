from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Load models
m_segment = YOLO("latest_best_seg.pt")  
m_classify = YOLO(r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\last11.pt")  

# Load image
image_path = r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\cee8e6ba-ce54-4c06-b7ed-8b79048a9bce.jpg"
img = cv2.imread(image_path)

# Perform segmentation
res = m_segment.predict(image_path)  

# Process each detected object
for r in res:
    img_name = Path(r.path).stem
    
    for ci, c in enumerate(r):
        # label = c.names[int(c.boxes.cls[0])]  # Get class label

        # Extract contour points
        if not c.masks.xy:
            continue  # Skip if no mask

        contour = np.array(c.masks.xy[0], np.int32).reshape(-1, 1, 2)

        # Create mask directly using fillPoly (faster)
        b_mask = np.zeros_like(img[:, :, 0], dtype=np.uint8)
        cv2.fillPoly(b_mask, [contour], 255)

        # Extract isolated object
        isolated = cv2.bitwise_and(img, img, mask=b_mask)
    
        # Perform classification
        r_classify = m_classify(isolated)

        if len(r_classify[0].boxes.cls) > 0:
            class_id = int(r_classify[0].boxes.cls[0])
            if not class_id == None:    
                classification_label = m_classify.names[class_id]
        
                # Draw segmentation contours
                cv2.drawContours(img, [contour], -1, (0, 0, 255), thickness=2)
                # Get bounding box for text placement
                x, y, w, h = cv2.boundingRect(contour)
                cv2.putText(img, classification_label, (x, y - 10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 2)

# Display image
target_width = 800
h, w = img.shape[:2]
aspect_ratio = h / w
img = cv2.resize(img, (target_width, int(target_width * aspect_ratio)))

cv2.imshow("Segmented & Classified", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
