# import cv2

# from ultralytics import YOLO
# from ultralytics.utils.plotting import Annotator, colors

# model = YOLO("yolo11n-seg.pt")  # segmentation model
# names = model.model.names
# cap = cv2.VideoCapture(r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\Traffic IP Camera video.mp4")
# w, h, fps = (int(cap.get(x)) for x in (cv2.CAP_PROP_FRAME_WIDTH, cv2.CAP_PROP_FRAME_HEIGHT, cv2.CAP_PROP_FPS))

# out = cv2.VideoWriter("instance-segmentation.avi", cv2.VideoWriter_fourcc(*"MJPG"), fps, (w, h))

# while True:
#     ret, im0 = cap.read()
#     if not ret:
#         print("Video frame is empty or video processing has been successfully completed.")
#         break

#     results = model.predict(im0)
#     annotator = Annotator(im0, line_width=2)

#     if results[0].masks is not None:
#         clss = results[0].boxes.cls.cpu().tolist()
#         masks = results[0].masks.xy
#         for mask, cls in zip(masks, clss):
#             color = colors(int(cls), True)
#             txt_color = annotator.get_txt_color(color)
#             annotator.seg_bbox(mask=mask, mask_color=color, label=names[int(cls)], txt_color=txt_color)

#     out.write(im0)
#     cv2.imshow("instance-segmentation", im0)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

# out.release()
# cap.release()
# cv2.destroyAllWindows()


import cv2
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors

# Load the YOLO segmentation model
model = YOLO("best-seg2.pt")  # Replace with your trained model path

# Load the image
image_path = r"C:\Users\user\OneDrive\Desktop\django_coffee\coffee\apps\dashboard\object_detection\e04be9e5-bcb4-4740-b322-0ecfe876aaab.jpg" 
im0 = cv2.imread(image_path)

# Resize image while maintaining aspect ratio
target_width = 1000
h, w = im0.shape[:2]
aspect_ratio = h / w
new_height = int(target_width * aspect_ratio)
im0 = cv2.resize(im0, (target_width, new_height))

# Run inference
results = model.predict(im0)

# Annotate results
annotator = Annotator(im0, line_width=1)
names = model.model.names

if results[0].masks is not None:
    clss = results[0].boxes.cls.cpu().tolist()
    masks = results[0].masks.xy
    for mask, cls in zip(masks, clss):
        color = colors(int(cls), True)
        # txt_color = annotator.get_txt_color(color)
        annotator.seg_bbox(mask=mask, mask_color=color)

# Display the output image
cv2.imshow("Instance Segmentation", im0)
cv2.waitKey(0)
cv2.destroyAllWindows()