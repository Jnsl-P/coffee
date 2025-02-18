from pathlib import Path

import cv2
import numpy as np

from ultralytics import YOLO

m = YOLO("best-seg2.pt")  
res = m.predict(r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\422c69cd-4043-471f-9708-9f164b391172.jpg")  

m_classify = YOLO(r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\last11.pt")

results = []
# Iterate detection results
for r in res:
    img = np.copy(r.orig_img)
    img_name = Path(r.path).stem

    # Iterate each object contour
    for ci, c in enumerate(r):
        label = c.names[c.boxes.cls.tolist().pop()]

        b_mask = np.zeros(img.shape[:2], np.uint8)
        
        # Create contour mask 
        contour = c.masks.xy.pop().astype(np.int32).reshape(-1, 1, 2)
        _ = cv2.drawContours(b_mask, [contour], -1,  (255, 255, 255), cv2.FILLED)
        # _ = cv2.drawContours(img, [contour], -1,  (0, 255, 0), 3)
        
        # Choose one:
        mask3ch = cv2.cvtColor(b_mask, cv2.COLOR_GRAY2BGR)
        isolated = cv2.bitwise_and(mask3ch, img)
        
        # OPTIONAL: detection crop (from either OPT1 or OPT2)
        # x1, y1, x2, y2 = c.boxes.xyxy.cpu().numpy().squeeze().astype(np.int32)
                
        # _ = cv2.putText(img, "fedex")
        # if ci == len(r) -1:
        _ = cv2.imwrite(f"{img_name}_{label}-{ci}.png", isolated)
        
        # end of segment result
       
        r_classify = m_classify(isolated)
        detections = r_classify[0]
        print(detections)