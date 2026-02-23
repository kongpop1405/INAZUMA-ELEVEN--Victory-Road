import cv2
import numpy as np
import pyautogui
import time
import win32api
import win32con
import os
import json
from datetime import datetime

# --- ⚙️ ตั้งค่าพื้นฐาน ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

# ระบุโฟลเดอร์ที่เก็บรูปภาพ
IMAGE_DIR = os.path.join(BASE_DIR, "img") 
SCREENSHOT_DIR = os.path.join(BASE_DIR, "logs_screenshots")
STATS_FILE = os.path.join(BASE_DIR, "bot_stats.json")

if not os.path.exists(SCREENSHOT_DIR):
    os.makedirs(SCREENSHOT_DIR)

# --- 📋 ลำดับขั้นตอนการฟาร์ม (เพิ่ม Path img/ ให้อัตโนมัติ) ---
RAW_STEPS = [
    {"files": ['station1.png', 'station2.png', 'station3.png', 'station4.png'], "thresh": 0.1, "label": "Station", "post_delay": 0.4},
    {"files": ['HeroBattle.png'], "thresh": 0.22, "label": "Hero Battle", "post_delay": 0.4},
    {"files": ['StartMatch.png'], "thresh": 0.25, "label": "Start Match", "post_delay": 1.4}, 
    {"files": ['Yes.png'], "thresh": 0.25, "label": "Yes", "post_delay": 0.4},
    {"files": ['Press.png'], "thresh": 0.25, "label": "Press", "post_delay": 1.5}, 
    {"files": ['set1.png', 'set2.png', 'Confirm.png'], "thresh": 0.25, "label": "Formation", "post_delay": 1.5}, 
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 1", "post_delay": 0.3}, 
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 2", "post_delay": 1.2}, 
    {"files": ['kickoff.png'], "thresh": 0.25, "label": "Kickoff", "post_delay": 0.5, "post_key": 'U'},
    {"files": ['set1.png', 'set2.png', 'Confirm.png'], "thresh": 0.25, "label": "Formation (จบครึ่งแรก)", "post_delay": 1.0, "is_match_phase": True},
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "next (จบครึ่งหลัง)", "post_delay": 1.0, "is_match_phase": True},
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 2", "post_delay": 1.2}, 
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Result 3", "post_delay": 1.0},
]

# แปลงชื่อไฟล์ให้มี Path ของโฟลเดอร์ img/ นำหน้า
FARM_STEPS = []
for step in RAW_STEPS:
    step["files"] = [os.path.join(IMAGE_DIR, f) for f in step["files"]]
    FARM_STEPS.append(step)

# --- 📊 ฟังก์ชันจัดการสถิติ ---
def update_step_stats(label, elapsed_time, is_round_end=False):
    data = {"steps_data": {}, "total_rounds": 0}
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: pass

    if "total_rounds" not in data: data["total_rounds"] = 0
    if "steps_data" not in data: data["steps_data"] = {}

    if is_round_end:
        data["total_rounds"] += 1

    optimized_delay = None
    if elapsed_time < 30: # ไม่นับรวมช่วงเวลาแข่งที่นานเกินไป
        if label not in data["steps_data"]:
            data["steps_data"][label] = {"latencies": []}
        
        data["steps_data"][label]["latencies"].append(round(elapsed_time, 2))
        if len(data["steps_data"][label]["latencies"]) > 10:
            data["steps_data"][label]["latencies"].pop(0)

        avg_latency = sum(data["steps_data"][label]["latencies"]) / len(data["steps_data"][label]["latencies"])
        optimized_delay = max(0.3, round(avg_latency * 1.2, 2))
        data["steps_data"][label]["current_optimized_delay"] = optimized_delay

    data["last_update"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        
    return optimized_delay, data["total_rounds"]

# --- 🖼️ ฟังก์ชันตรวจจับภาพและควบคุม ---
def find_best_match(image_list, threshold):
    screenshot = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    gray_screen = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
    edged_screen = cv2.Canny(gray_screen, 100, 200)
    
    best_match = None 
    for img_path in image_list:
        if not os.path.exists(img_path): continue
        
        # --- เปลี่ยนจาก cv2.imread เป็นวิธีนี้เพื่อรองรับภาษาไทย ---
        img_array = np.fromfile(img_path, np.uint8)
        template = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
        # --------------------------------------------------

        if template is None: continue
        
        edged_template = cv2.Canny(template, 100, 200)
        res = cv2.matchTemplate(edged_screen, edged_template, cv2.TM_CCOEFF_NORMED)
        (_, maxVal, _, maxLoc) = cv2.minMaxLoc(res)
        
        if best_match is None or maxVal > best_match[0]:
            if maxVal >= threshold:
                best_match = (maxVal, maxLoc, edged_template.shape[:2], img_path)
                
    if best_match:
        acc, loc, (rH, rW), name = best_match
        return (int(loc[0] + rW / 2), int(loc[1] + rH / 2), acc, name)
    return None

def press_key(key_code):
    if isinstance(key_code, str): key_code = ord(key_code.upper())
    win32api.keybd_event(key_code, 0, 0, 0)
    time.sleep(0.05)
    win32api.keybd_event(key_code, 0, win32con.KEYEVENTF_KEYUP, 0)

def log(msg, type="INFO"):
    icons = {"INFO": "🔍", "SUCCESS": "✅", "MATCH": "⚽", "GAP": "⏱️", "RETRY": "⚠️", "SAVE": "📸"}
    print(f"{icons.get(type, '🔹')} {msg}")

def save_error_screenshot(label):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FAIL_{label}_{timestamp}.png"
    filepath = os.path.join(SCREENSHOT_DIR, filename)
    pyautogui.screenshot().save(filepath)
    return filename

# --- 🔄 Main Loop ---
def main_loop():
    log("เริ่มต้นกระบวนการ Awakening...", "SUCCESS")
    current_step = 0
    retry_count = 0 
    last_action_time = time.time()
    in_match_phase = False 

    while True:
        now = time.time()
        elapsed = now - last_action_time 
        step = FARM_STEPS[current_step]
        result = find_best_match(step["files"], step["thresh"])

        if result:
            x, y, acc, name = result
            is_end = (current_step == len(FARM_STEPS) - 1)
            
            # อัปเดตสถิติและรับค่า Delay ที่ปรับจูนแล้ว
            new_delay, total_rounds = update_step_stats(step['label'], elapsed, is_round_end=is_end)
            
            current_delay = new_delay if new_delay else step.get("post_delay", 0.5)
            log(f"พบ {step['label']}! (ใช้เวลาโหลด: {elapsed:.2f}s, Delay ต่อไป: {current_delay}s)", "GAP")
            
            pyautogui.click(x, y)
            retry_count = 0
            in_match_phase = False 
            
            time.sleep(current_delay)
            if "post_key" in step:
                log(f"Action: กดปุ่ม {step['post_key']}", "MATCH")
                press_key(step["post_key"])
            
            # ถ้าจบรอบ ให้พักสักครู่
            next_idx = (current_step + 1) % len(FARM_STEPS)
            if next_idx == 0:
                round_pause = 5.0
                log(f"✅ จบ Awakening รอบที่ {total_rounds} | พัก {round_pause} วินาที", "SUCCESS")
                time.sleep(round_pause)

            if FARM_STEPS[next_idx].get("is_match_phase"):
                in_match_phase = True

            last_action_time = time.time()
            current_step = next_idx
            
        else:
            retry_count += 1
            # ถ้าอยู่ในช่วงแข่ง จะรอภาพนานกว่าปกติ (เช่น รอภาพจบครึ่งหลัง)
            wait_limit = 250 if in_match_phase else 15
            
            if retry_count % 10 == 0:
                log(f"กำลังหา {step['label']}... ({retry_count}/{wait_limit})", "INFO")
            
            if retry_count >= wait_limit:
                save_error_screenshot(step['label'])
                log(f"⚠️ ไม่พบ {step['label']} ย้อนกลับไปขั้นตอนก่อนหน้า", "RETRY")
                retry_count = 0
                in_match_phase = False
                current_step = (current_step - 1) if current_step > 0 else 0
                last_action_time = time.time()
            
            time.sleep(1.5 if in_match_phase else 0.8)

if __name__ == "__main__":
    # ให้เวลา User สลับหน้าจอไปที่เกม 3 วินาที
    time.sleep(3)
    try:
        main_loop()
    except KeyboardInterrupt:
        log("หยุดการทำงานโดยผู้ใช้", "INFO")