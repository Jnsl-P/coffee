from ultralytics import YOLO
class ImageLink():
    def __init__(self):
        self.image_path = r"c:\Users\user\OneDrive\Downloads\ad94d596-81c6-4561-9586-14a50ec482ac.jpg"
        self.modeli = YOLO(r"c:\Users\user\OneDrive\Desktop\good_bad_bean_models\segment_1\exp1_retrain4\weights\best.pt")
        self.modelii = YOLO(r"c:\Users\user\OneDrive\Desktop\model_versions\a_6\goodbad-exp3\weights\last.pt")
        self.modeliii = YOLO(r"c:\Users\user\OneDrive\Desktop\model_versions\segment2\retrain_exp2\weights\best.pt")