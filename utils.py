import cv2, numpy as np, pyautogui, time, win32api, win32con, os, json
from datetime import datetime
from config import IMG_DIR, SCREENSHOT_DIR, STATS_FILE, KEY_PRESS_DURATION

# สร้างโฟลเดอร์พื้นฐาน
for path in [IMG_DIR, SCREENSHOT_DIR]:
    if not os.path.exists(path): os.makedirs(path)

def find_best_match(image_list, threshold):
    screen = cv2.cvtColor(np.array(pyautogui.screenshot()), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(gray, 150, 250)
    best = None
    
    for img_name in image_list:
        img_path = os.path.join(IMG_DIR, img_name)
        if not os.path.exists(img_path): continue
        try:
            img_array = np.fromfile(img_path, np.uint8)
            temp = cv2.imdecode(img_array, cv2.IMREAD_GRAYSCALE)
            if temp is None: continue
            e_temp = cv2.Canny(temp, 150, 250)
            res = cv2.matchTemplate(edged, e_temp, cv2.TM_CCOEFF_NORMED)
            _, mVal, _, mLoc = cv2.minMaxLoc(res)
            if best is None or mVal > best[0]:
                if mVal >= threshold: 
                    best = (mVal, mLoc, e_temp.shape[:2], img_name)
        except: continue
    if best:
        acc, loc, (rH, rW), name = best
        return (int(loc[0] + rW/2), int(loc[1] + rH/2), acc, name)
    return None

def update_step_stats(label, elapsed_time=0, is_round_end=False, is_miss=False, is_step_back=False):
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            try: data = json.load(f)
            except: data = {"steps_data": {}, "total_rounds": 0}
    else: data = {"steps_data": {}, "total_rounds": 0}

    if label not in data["steps_data"]: 
        data["steps_data"][label] = {"latencies": [], "total_searches": 0, "fail_count": 0, "success_count": 0, "step_back_count": 0}
    
    step_entry = data["steps_data"][label]
    if is_step_back:
        step_entry["step_back_count"] += 1
    elif is_miss:
        step_entry["fail_count"] += 1
        step_entry["total_searches"] += 1
    else:
        if is_round_end: data["total_rounds"] += 1
        step_entry["success_count"] += 1
        step_entry["total_searches"] += 1
        if 0.01 <= elapsed_time < 30:
            lats = step_entry.get("latencies", [])
            lats.append(round(elapsed_time, 2))
            if len(lats) > 10: lats.pop(0)
            avg = round(sum(lats)/len(lats), 2)
            step_entry["avg_latency"] = avg
            step_entry["current_optimized_delay"] = max(0.1, round(avg * 1.1, 2))

    with open(STATS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    return step_entry.get("current_optimized_delay", 0.2), data["total_rounds"]

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