import numpy as np
import cv2
class ViewTransformer():
    def __init__(self):
        court_width = 68
        court_length = 23.32

        self.pixel_verticies = np.array({
            [110,1035]
            [265,275],
            [910,260],
            [1640,915]
        })