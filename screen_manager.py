import cv2
import numpy as np
import pyautogui
import os
from config import IMG_DIR

class ScreenManager:
    def __init__(self):
        self.img_dir = IMG_DIR

    def grab_screen(self):
        # ปัจจุบันใช้ pyautogui ในอนาคตเปลี่ยนเป็น Window Capture ได้ที่นี่
        return cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)

    def find_best_match(self, image_list, threshold):
        screen = self.grab_screen()
        gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
        edged = cv2.Canny(gray, 150, 250)
        best = None
        
        for img_name in image_list:
            img_path = os.path.join(self.img_dir, img_name)
            if not os.path.exists(img_path): continue
            
            img_array = np.fromfile(img_path, np.uint8)
            temp = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if temp is None: continue
            
            e_temp = cv2.Canny(temp, 150, 250)
            res = cv2.matchTemplate(edged, e_temp, cv2.TM_CCOEFF_NORMED)
            _, mVal, _, mLoc = cv2.minMaxLoc(res)
            
            if best is None or mVal > best[0]:
                if mVal >= threshold: 
                    best = (mVal, mLoc, e_temp.shape[:2], img_name)
        
        if best:
            acc, loc, (rH, rW), name = best
            return (int(loc[0] + rW/2), int(loc[1] + rH/2), acc, name)
        return None