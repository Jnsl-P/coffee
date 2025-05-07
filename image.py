from ultralytics import YOLO
class ImageLink():
    def __init__(self):
        self.image_path = r"c:\Users\user\OneDrive\Desktop\ORIG_IMAGES\20250501_171114.jpg"
        self.modeli = YOLO(r"c:\Users\user\OneDrive\Desktop\segmentation_models\segment11\train\weights\last.pt")
        self.modelii = YOLO(r"c:\Users\user\OneDrive\Desktop\good_bad_bean_models\b_4\train\weights\last.pt")
        self.modeliii = YOLO(r"c:\Users\user\OneDrive\Desktop\model_versions\a_2\train\weights\last.pt")