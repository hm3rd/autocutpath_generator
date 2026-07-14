import numpy as np
# pyrefly: ignore [missing-import]
from PIL import Image
import numpy as np
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import svgwrite

def create_svg():
    print()

def input_image_def(input_image):
    img = Image.open(input_image)
    img_array = np.array(img)
    img = img_array.shape[:2]
    print(img)
    img = img_array[:,:,:]
    print(img)

input_image_def(r"C:\Users\tsuda\AppData\Roaming\inkscape\extensions\test\SVGGenerator\core\input.png")