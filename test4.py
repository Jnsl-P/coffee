# video file
import cv2
import numpy as np
from ultralytics import YOLO



video_path = "coffeetest.mp4"
cap = cv2.VideoCapture(video_path)

m_segment = YOLO("best-seg2.pt")
m_classify = YOLO(r"last11.pt")  
w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))

if cap.isOpened():
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    res=(int(width), int(height))
    # this format fail to play in Chrome/Win10/Colab
    # fourcc = cv2.VideoWriter_fourcc(*'MP4V') #codec
    fourcc = cv2.VideoWriter_fourcc(*'H264') #codec
    out = cv2.VideoWriter("COFFEE.avi", cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))
    frame = None
    while True:
        try:
            is_success, frame = cap.read()
        except cv2.error:
            continue
        if not is_success:
            break
        # OPTIONAL: do some processing
        res = m_segment.predict(frame)

        # Read the original image
        img = frame

        for r in res:
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
                
                class_id = int(r_classify[0].boxes.cls[0])
                classification_label = m_classify.names[class_id]
              else:
                  classification_label = "Unknown"  # Fallback label if no prediction is made

              
              # Draw classification result on the image
              x, y, w, h = cv2.boundingRect(contour)
              cv2.putText(img, classification_label, (x, y - 10), cv2.FONT_HERSHEY_DUPLEX, 2, (0, 0, 0), 2)

        # convert cv2 BGR format to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        out.write(img)
        cv2.imshow("instance-segmentation", img)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    out.release()
cap.release()
cv2.destroyAllWindows()