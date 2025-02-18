from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO

# Load segmentation and classification models
m_segment = YOLO("best-seg2.pt")  
m_classify = YOLO(r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\last11.pt")  

# Load the input image
image_path = r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\422c69cd-4043-471f-9708-9f164b391172.jpg"
res = m_segment.predict(image_path)  

# Read the original image
img = cv2.imread(image_path)


# Iterate through detected objects
for r in res:
    img_name = Path(r.path).stem
    for ci, c in enumerate(r):
        label = c.names[c.boxes.cls.tolist().pop()]  # Get class label
        
        # Create an empty mask for segmentation
        b_mask = np.zeros(img.shape[:2], np.uint8)
        
        # Extract the contour points
        contour = c.masks.xy.pop().astype(np.int32).reshape(-1, 1, 2)

        # Draw the segmentation contour (thinnest possible line)
        # cv2.drawContours(b_mask, [contour], -1, (255), thickness=1)  # Binary mask
        cv2.drawContours(b_mask, [contour], -1,  (255, 255, 255), cv2.FILLED)
        
        
        # Convert to 3-channel mask
        mask3ch = cv2.cvtColor(b_mask, cv2.COLOR_GRAY2BGR)
        
        # Extract isolated object
        isolated = cv2.bitwise_and(mask3ch, img)
        
        # ===================== END SEGEMENTATION / CLASSIFICATION STARTS ===================
        
        # Perform classification on the segmented object
        r_classify = m_classify(isolated)
        
        cv2.drawContours(img, [contour], -1, (0, 0, 255), thickness=10)  # Overlay contour on the image


        if len(r_classify[0].boxes.cls) != 0:
            class_id = int(r_classify[0].boxes.cls)
            classification_label = m_classify.names[class_id]
        else:
            classification_label = "Unknown"  # Fallback label if no prediction is made

        
        # Draw classification result on the image
        x, y, w, h = cv2.boundingRect(contour)
        cv2.putText(img, classification_label, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 0, 0), 2)


# Display the final output with contours and classification labels
target_width = 800
h, w = img.shape[:2]
aspect_ratio = h / w
new_height = int(target_width * aspect_ratio)
img = cv2.resize(img, (target_width, new_height))

cv2.imshow("Segmented and Classified", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
