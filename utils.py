import cv2, numpy as np, pyautogui, time, win32api, win32con, os, json
from datetime import datetime
from config import IMG_DIR, SCREENSHOT_DIR, STATS_FILE, STATS_DIR, KEY_PRESS_DURATION

# สร้างโฟลเดอร์พื้นฐาน
for path in [IMG_DIR, SCREENSHOT_DIR, STATS_DIR]:
    if not os.path.exists(path): os.makedirs(path)

def find_best_match(image_list, threshold, step_label=None):
    """
    ค้นหาภาพที่แมตช์ที่สุดจากรายการ พร้อมจับเวลาที่ใช้ในการค้นหา
    """
    start_time = time.perf_counter()  # เริ่มจับเวลา
    
    # จับภาพหน้าจอและเตรียมภาพสำหรับ Template Matching
    screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 150, 250)
    best = None
    
    for img_name in image_list:
        img_path = os.path.join(IMG_DIR, img_name)
        if not os.path.exists(img_path): continue
        try:
            # โหลดรูปภาพต้นแบบ (Template)
            img_array = np.fromfile(img_path, np.uint8)
            temp = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if temp is None: continue
            
            # ทำ Canny Edge Detection เพื่อความแม่นยำ
            e_temp = cv2.Canny(temp, 150, 250)
            res = cv2.matchTemplate(edged, e_temp, cv2.TM_CCOEFF_NORMED)
            _, mVal, _, mLoc = cv2.minMaxLoc(res)
            
            # เก็บค่าที่ดีที่สุดที่เกิน threshold
            if best is None or mVal > best[0]:
                if mVal >= threshold: 
                    best = (mVal, mLoc, e_temp.shape[:2], img_name)
        except: 
            continue

    if best:
        # คำนวณเวลาที่ใช้ในการค้นหาจนเจอ
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        acc, loc, (rH, rW), name = best
        
        # ถ้ามีการส่ง step_label มา ให้บันทึกสถิติลงไฟล์ทันที
        if step_label:
            # เรียกใช้ฟังก์ชันที่มีอยู่แล้วใน utils.py เพื่ออัปเดต bot_stats.json
            update_step_stats(step_label, elapsed, is_end=False)
            
        return (int(loc[0] + rW/2), int(loc[1] + rH/2), acc, name)
        
    return None

def update_step_stats(step_label, elapsed_time, is_end, actual_post_delay=0, is_step_back=False):
    """
    บันทึกสถิติของแต่ละ step
    """
    # --- สร้างชื่อไฟล์ตามชั่วโมงปัจจุบัน ---
    hourly_timestamp = datetime.now().strftime("%Y-%m-%d_%H")
    hourly_stats_file = os.path.join(STATS_DIR, f"stats_{hourly_timestamp}.json")
    
    # --- อ่านข้อมูลจากไฟล์ชั่วโมง หรือสร้างใหม่ ---
    if os.path.exists(hourly_stats_file):
        with open(hourly_stats_file, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: data = {"steps_data": {}, "total_rounds": 0, "start_time": datetime.now().isoformat()}
    else: 
        data = {"steps_data": {}, "total_rounds": 0, "start_time": datetime.now().isoformat()}
    
    # --- Initialize หรือ Update step entry ---
    if step_label not in data["steps_data"]:
        data["steps_data"][step_label] = {
            "latencies": [],
            "total_searches": 0,
            "fail_count": 0,
            "success_count": 0,
            "step_back_count": 0,
            "avg_post_delay": 0
        }
    
    step_entry = data["steps_data"][step_label]
    
    # --- Ensure all keys exist ---
    for key in ["latencies", "total_searches", "fail_count", "success_count", "step_back_count", "avg_post_delay"]:
        if key not in step_entry:
            step_entry[key] = [] if key == "latencies" else 0
    
    # --- บันทึกข้อมูล ---
    if is_step_back:
        step_entry["step_back_count"] = step_entry.get("step_back_count", 0) + 1
    else:
        if is_end: 
            data["total_rounds"] = data.get("total_rounds", 0) + 1
        step_entry["success_count"] = step_entry.get("success_count", 0) + 1
        step_entry["total_searches"] = step_entry.get("total_searches", 0) + 1
        
        # บันทึก latency
        if 0.01 <= elapsed_time < 30:
            lats = step_entry.get("latencies", [])
            lats.append(round(elapsed_time, 2))
            if len(lats) > 10: lats.pop(0)
            step_entry["latencies"] = lats
            avg = round(sum(lats) / len(lats), 2)
            step_entry["avg_latency"] = avg
            step_entry["current_optimized_delay"] = max(0.1, round(avg * 1.1, 2))
        
        # บันทึก actual post_delay (แบบหาค่าเฉลี่ย)
        if actual_post_delay > 0:
            delays = step_entry.get("post_delays_list", [])
            delays.append(round(actual_post_delay, 2))
            if len(delays) > 10: delays.pop(0)
            step_entry["post_delays_list"] = delays
            step_entry["avg_actual_delay"] = round(sum(delays) / len(delays), 2)
            step_entry["last_actual_delay"] = round(actual_post_delay, 2)
            # เปรียบเทียบกับค่า config (ถ้าเกิน post_delay จะแสดงเป็นบวก)
            configured_delay = next(
                (s.get("post_delay", 0) for s in __import__('config').FARM_STEPS if s["label"] == step_label), 0
            )
            if configured_delay > 0:
                step_entry["delay_diff_avg"] = round(step_entry["avg_actual_delay"] - configured_delay, 2)
    
    # --- บันทึกลงไฟล์ชั่วโมง ---
    data["last_update"] = datetime.now().isoformat()
    with open(hourly_stats_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    # --- บันทึกลงไฟล์ bot_stats.json ด้วย ---
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    return step_entry.get("current_optimized_delay", 0.2), data.get("total_rounds", 0)

def press_key(key):
    special_keys = {'ALT': win32con.VK_MENU, 'ENTER': win32con.VK_RETURN, 'ESC': win32con.VK_ESCAPE, 'CTRL': win32con.VK_CONTROL}
    if isinstance(key, str) and key.upper() in special_keys:
        k = special_keys[key.upper()]
    elif isinstance(key, str):
        k = ord(key.upper())
    else: k = key
    win32api.keybd_event(k, 0, 0, 0)
    time.sleep(KEY_PRESS_DURATION)
    win32api.keybd_event(k, 0, win32con.KEYEVENTF_KEYUP, 0)

def save_error_screenshot(label):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"FAIL_{label}_{timestamp}.png"
    pyautogui.screenshot().save(os.path.join(SCREENSHOT_DIR, filename))


def find_image_with_stats(image_path, step_name, confidence=0.8):
    start_time = time.perf_counter()  # เริ่มจับเวลา
    
    # สมมติว่าใช้ pyautogui หรือ opencv ในการค้นหา
    location = pyautogui.locateOnScreen(image_path, confidence=confidence)
    
    if location:
        end_time = time.perf_counter()
        duration = end_time - start_time  # เวลาที่ใช้จริง (วินาที)
        
        # บันทึกลงใน stats (ตัวอย่างโครงสร้าง)
        save_stats(step_name, duration)
        return location
    return None

def save_stats(step_label, duration, success=True):
    """
    บันทึกสถิติการค้นหารูปลงใน bot_stats.json
    :param step_label: ชื่อ Step (เช่น 'Station', 'Hero Battle')
    :param duration: เวลาที่ใช้ในการค้นหา (วินาที)
    :param success: ผลการค้นหาว่าเจอหรือไม่
    """
    # ตรวจสอบว่าไฟล์มีอยู่หรือไม่ ถ้าไม่มีให้สร้างโครงสร้างพื้นฐาน
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"steps_data": {}}
    else:
        data = {"steps_data": {}}

    # เตรียมโครงสร้างข้อมูลสำหรับ Step นั้นๆ
    if step_label not in data["steps_data"]:
        data["steps_data"][step_label] = {
            "latencies": [],
            "total_searches": 0,
            "fail_count": 0,
            "success_count": 0,
            "avg_latency": 0.0
        }

    step_stats = data["steps_data"][step_label]
    
    # อัปเดตตัวเลขสถิติ
    step_stats["total_searches"] += 1
    if success:
        step_stats["success_count"] += 1
        step_stats["latencies"].append(round(duration, 4))
        # เก็บเฉพาะ 20 ค่าล่าสุดเพื่อไม่ให้ไฟล์ใหญ่เกินไปและสะท้อนประสิทธิภาพปัจจุบัน
        if len(step_stats["latencies"]) > 20:
            step_stats["latencies"].pop(0)
        
        # คำนวณค่าเฉลี่ยใหม่ (avg_latency)
        step_stats["avg_latency"] = round(sum(step_stats["latencies"]) / len(step_stats["latencies"]), 4)
    else:
        step_stats["fail_count"] += 1

    # บันทึกกลับลงไฟล์
    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)