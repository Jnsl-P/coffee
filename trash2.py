import cv2

# Open the default camera (index 0)
capture = cv2.VideoCapture(0)

# Check if the camera opened successfully
if not capture.isOpened():
    raise IOError("Cannot open webcam")

while(True):
    # Read a frame from the camera
    ret, frame = capture.read()
    if not ret:
        break
    
    # Display the resulting frame
    cv2.imshow('Live Camera Feed', frame)

    # Press 'q' to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the capture object and close all windows
capture.release()
cv2.destroyAllWindows()