import cv2
import numpy as np
import pyautogui
import time
import win32api
import win32con
import os
import glob
from datetime import datetime
from config import SCREENSHOT_DIR, KEY_PRESS_DURATION

# --- 📂 ส่วนที่ 1: การจัดการไฟล์และระบบพื้นฐาน ---

def ensure_dirs():
    """ตรวจสอบและสร้างโฟลเดอร์ที่จำเป็น"""
    if not os.path.exists(SCREENSHOT_DIR):
        os.makedirs(SCREENSHOT_DIR)

def save_error_screenshot(label):
    """บันทึกภาพหน้าจอพร้อมทำความสะอาดไฟล์เก่า"""
    ensure_dirs()
    
    # ตรวจสอบและลบไฟล์เก่าก่อนบันทึกไฟล์ใหม่
    cleanup_screenshots() 
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FAIL_{label}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    pyautogui.screenshot().save(filepath)
    return filepath

def cleanup_screenshots():
    """จัดการลบรูปภาพที่เก่าที่สุดเมื่อจำนวนไฟล์เกิน MAX_SCREENSHOTS"""
    from config import SCREENSHOT_DIR, MAX_SCREENSHOTS
    
    # ดึงรายชื่อไฟล์ .png ทั้งหมดในโฟลเดอร์
    files = glob.glob(os.path.join(SCREENSHOT_DIR, "*.png"))
    
    # ถ้าจำนวนไฟล์เกินขีดจำกัด
    if len(files) > MAX_SCREENSHOTS:
        # เรียงลำดับไฟล์ตามเวลาที่แก้ไขล่าสุด (เก่าไปใหม่)
        files.sort(key=os.path.getmtime)
        
        # คำนวณจำนวนที่ต้องลบ
        files_to_delete = files[:len(files) - MAX_SCREENSHOTS]
        
        for f in files_to_delete:
            try:
                os.remove(f)
                # print(f"🧹 [Cleanup] ลบไฟล์ภาพเก่า: {os.path.basename(f)}")
            except Exception as e:
                print(f"⚠️ [Cleanup] ไม่สามารถลบไฟล์ {f} ได้: {e}")
                
# --- 🖱️ ส่วนที่ 2: การจัดการ Mouse Input (เตรียมรองรับ Human-like) ---

def perform_click(x, y):
    """
    ฟังก์ชันหลักในการคลิก 
    ในอนาคตจะเปลี่ยนเป็น Human-like Click (mouseDown/Up) ได้ที่นี่
    """
    # ปัจจุบันใช้ระบบเดิมตาม main.py
    pyautogui.click(x, y)
    
    # นำเมาส์กลับไปพักที่กลางจอเพื่อไม่ให้บังปุ่ม
    # หมายเหตุ: CX, CY จะถูกดึงผ่าน parameter หรือ config
    # pyautogui.moveTo(CX, CY, duration=0) 

# --- ⌨️ ส่วนที่ 3: การจัดการ Keyboard Input ---

def press_key(key):
    """ส่งคำสั่งกดปุ่มคีย์บอร์ดแบบกำหนดระยะเวลาค้าง"""
    special_keys = {
        'ALT': win32con.VK_MENU, 
        'ENTER': win32con.VK_RETURN, 
        'ESC': win32con.VK_ESCAPE, 
        'CTRL': win32con.VK_CONTROL
    }
    
    if isinstance(key, str) and key.upper() in special_keys:
        k = special_keys[key.upper()]
    elif isinstance(key, str):
        k = ord(key.upper())
    else:
        k = key
        
    # กดปุ่มลง
    win32api.keybd_event(k, 0, 0, 0)
    # รอตามเวลาที่ตั้งไว้ใน config
    time.sleep(KEY_PRESS_DURATION)
    # ปล่อยปุ่ม
    win32api.keybd_event(k, 0, win32con.KEYEVENTF_KEYUP, 0)

# --- 🧪 ส่วนที่ 4: Image Processing Helpers ---

def get_edged_image(image_gray):
    """แปลงภาพ Gray เป็น Edged (Canny) เพื่อความแม่นยำในการ Match"""
    return cv2.Canny(image_gray, 150, 250)