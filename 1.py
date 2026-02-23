import pyautogui
import time
import win32api
import win32con
import random
import os

# 📂 ตั้งค่า Path (เผื่อไว้สำหรับขยายสคริปต์ในอนาคต)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def log(message):
    """ฟังก์ชันพิมพ์สถานะพร้อมอิโมจิ"""
    print(f"{message}")

def press_key(key_code, key_name):
    """ฟังก์ชันกลางสำหรับกดปุ่มคีย์บอร์ด"""
    log(f"⌨️  กำลังกดปุ่ม: {key_name}")
    win32api.keybd_event(key_code, 0, 0, 0) # กดปุ่มลง
    time.sleep(random.uniform(0.1, 0.2))
    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0) # ปล่อยปุ่ม

def farm_loop():
    log("🚀 ระบบ: เริ่มต้นการทำงาน (โหมดกดปุ่มเปิดลิสต์)...")
    
    # 1. กดปุ่ม 'V' เพื่อเปิดลิสต์คู่แข่ง (V key code คือ 0x56)
    log("🔍 กำลังเปิดลิสต์คู่แข่ง...")
    press_key(0x56, "V")
    time.sleep(2) # รอหน้าเมนูลิสต์คู่แข่งโหลด
    
    log("📂 ระบบ: เข้าสู่โหมดฟาร์มเพื่อ Awakening ตัวละคร")
    
    match_count = 0
    while True:
        try:
            log(f"📊 สถานะ: กำลังประมวลผลเมนู (รอบที่ {match_count + 1})")
            
            # 2. กดปุ่ม ENTER เพื่อเลือกคู่แข่งและเริ่มแมตช์
            press_key(0x0D, "ENTER")
            time.sleep(1)
            
            # 3. กดปุ่ม ENTER ซ้ำเพื่อยืนยันการเริ่มแมตช์
            press_key(0x0D, "ENTER (Confirm)")
            
            match_count += 1
            log(f"⚽ แมตช์ที่ {match_count} เริ่มต้นแล้ว! รอระหว่างแข่ง...")
            
            # 4. รอเวลาแข่ง (ควรปรับเวลาตามจริง เช่น 5-10 นาที หรือใช้ 600 วินาที)
            # ในที่นี้ใส่ไว้สั้นๆ เพื่อทดสอบลูป
            time.sleep(10) 
            
            # 5. หลังจบแมตช์ กด ENTER เพื่อข้ามหน้าสรุปผล
            log("🏆 จบแมตช์: กำลังกดข้ามหน้าสรุปผล")
            for _ in range(5): # กดรัวๆ 5 ครั้งเพื่อให้แน่ใจว่าพ้นหน้าสรุปผล
                press_key(0x0D, "ENTER (Result)")
                time.sleep(1)
            
            # 6. กลับมาที่หน้าแผนที่/Station แล้วกด V เพื่อเริ่มรอบใหม่
            log("🔄 กำลังเตรียมเริ่มรอบใหม่...")
            press_key(0x56, "V (Restart List)")
            time.sleep(2)

        except Exception as e:
            log(f"❌ พบปัญหาระหว่างฟาร์ม: {e}")
            time.sleep(5)

if __name__ == "__main__":
    print("="*40)
    log("⚡ Inazuma Eleven: Victory Road Macro ⚡")
    print("="*40)
    log("⏳ กรุณาสลับไปหน้าต่างเกมภายใน 3 วินาที...")
    time.sleep(3)
    
    try:
        farm_loop()
    except KeyboardInterrupt:
        print("\n" + "="*40)
        log("🛑 ระบบ: หยุดการทำงานโดยผู้ใช้")
        print("="*40)