from ultralytics import YOLO
class ImageLink():
    def __init__(self):
        self.image_path = r"c:\Users\user\OneDrive\Desktop\Cvsu beans test\20250519_145451.jpg"
        self.modeli = YOLO(r"c:\Users\user\OneDrive\Downloads\amen.pt")
        self.modelii = YOLO(r"c:\Users\user\OneDrive\Desktop\model_versions\a_6\goodbad-exp3\weights\last.pt")
        self.modeliii = YOLO(r"c:\Users\user\OneDrive\Downloads\last (1).pt")