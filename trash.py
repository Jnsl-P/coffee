# import cv2
# import numpy as np

# def high_pass_filter(image, sigma=1.0):
#     # Apply Gaussian blur
#     blurred = cv2.GaussianBlur(image, (0, 0), sigma)
#     # Subtract the blurred image from the original
#     high_pass = cv2.subtract(image, image)
#     # Add the high-pass image back to the original
#     sharpened = cv2.addWeighted(image, 1.0, high_pass, 1.0, 0)
#     return sharpened

# # Load the image
# image = cv2.imread(r'c:\Users\user\OneDrive\Desktop\New folder\images_iso\severe insect 0.93_iso_4877581.jpg')
# # Apply high-pass filter
# sharpened_image = high_pass_filter(image)
# # Save the result
# cv2.imwrite('sharpened_image.jpg', sharpened_image)

import cv2
import numpy as np

# Load image
def sharpness2(image):

# Define sharpening kernel
    kernel = np.array([[0, -1, 0],
                    [-1, 5,-1],
                    [0, -1, 0]])

    # Apply sharpening filter
    sharpened = cv2.filter2D(image, -1, kernel)
    return sharpened

image = cv2.imread(r"c:\Users\user\OneDrive\Desktop\New folder\images_iso\fungus 0.87_iso_2285856.jpg")
kernel = np.array([[0, -1, 0],
                    [-1, 5,-1],
                    [0, -1, 0]])
denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
sharpened = cv2.filter2D(denoised, -1, kernel)
cv2.imwrite("denoised_sharpened.jpg", sharpened)
