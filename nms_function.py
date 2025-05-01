import cv2

def apply_nms(boxes, confidences):
    nms_indices = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
    
    if len(nms_indices) > 0:
        nms_indices = nms_indices.flatten()
    return nms_indices   
