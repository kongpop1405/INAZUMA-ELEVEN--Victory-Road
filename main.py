import pyautogui, time, gc, random
from config import *
from utils import update_step_stats, find_best_match, press_key, save_error_screenshot

state = {
    "cur": 0, "retry": 0, "last_time": time.time(), "in_match": False,
    "next_click_count": 0, "consecutive_back_steps": 0, "last_back_step_idx": -1, "rounds": 0
}

def handle_success(step, res):
    global state
    state["consecutive_back_steps"] = 0
    state["last_back_step_idx"] = -1
    
    now = time.time()
    elapsed = now - state["last_time"]
    x, y, acc, name = res
    is_end = (state["cur"] == len(FARM_STEPS) - 1)
    
    new_delay, total_rounds = update_step_stats(step['label'], elapsed, is_end)
    state["rounds"] = total_rounds
    
    print(f"\n✅ เจอภาพ: {step['label']} | ใช้เวลา: {elapsed:.2f}s | Acc: {acc:.2f}")
    pyautogui.click(x, y)
    pyautogui.moveTo(CX, CY, duration=0) 

    if "post_key" in step:
        time.sleep(new_delay) 
        print(f"   ∟ ⌨️ Action: กดปุ่ม {step['post_key']}")
        press_key(step['post_key'])
    
    if is_end:
        gc.collect()
        print(f"\n🏆 จบรอบที่ {state['rounds']} | พัก {POST_MATCH_REST}s\n" + "🏆"*20)
        time.sleep(POST_MATCH_REST)

    state["cur"] = (state["cur"] + 1) % len(FARM_STEPS)
    state["in_match"] = FARM_STEPS[state["cur"]].get("is_match_phase", False)
    state["retry"] = 0
    state["last_time"] = time.time()
    state["next_click_count"] = 0
    time.sleep(step.get("post_delay", DEFAULT_POST_DELAY))

def handle_failure(step, available_keys):
    global state
    state["retry"] += 1
    limit = MATCH_WAIT_LIMIT if state["in_match"] else NORMAL_WAIT_LIMIT
    
    if "Next" in step['label'] and state["retry"] % NEXT_CLICK_INTERVAL == 0:
        state["next_click_count"] += 1
        print(f"👉 [Action] คลิกย้ำครั้งที่ {state['next_click_count']} ที่ {step['label']}")
        pyautogui.click(CX, CY + 150)

    if state["retry"] >= limit:
        # save_error_screenshot(step['label'])
        update_step_stats(step['label'], is_step_back=True)

        if state["last_back_step_idx"] == state["cur"]:
            state["consecutive_back_steps"] += 1
        else:
            state["consecutive_back_steps"] = 1
            state["last_back_step_idx"] = state["cur"]

        print(f"\n❌ [LOG] พลาด {step['label']} ต่อเนื่องครั้งที่ {state['consecutive_back_steps']}")

        if state["consecutive_back_steps"] >= CONSECUTIVE_BACK_LIMIT:
            print(f"⚠️ [BREAK LOOP] ทำการ Hard Reset ไปหน้า Station")
            state["cur"] = 0
            state["consecutive_back_steps"] = 0
        else:
            if state["cur"] == 0:
                state["cur"] = len(FARM_STEPS) - 1
                print(f"🔙 [LOG] ย้อนจากหน้าแรก ไปขั้นตอนสุดท้าย")
            else:
                state["cur"] -= 1
                print(f"🔙 [LOG] ย้อนกลับไป {FARM_STEPS[state['cur']]['label']}")
        
        state["retry"] = 0
        state["next_click_count"] = 0
        state["in_match"] = False
        state["last_time"] = time.time()
        pyautogui.moveTo(CX, CY)

    time.sleep(0.2 if not state["in_match"] else 1.0)

def main_loop():
    print("="*65 + "\n🚀 Awakening System: Optimized Function Structure\n" + "="*65)
    available_keys = list(set([step['post_key'] for step in FARM_STEPS if 'post_key' in step] + ['U']))
    last_step_idx = -1

    while True:
        step = FARM_STEPS[state["cur"]]
        
        # ✅ เช็คว่าถ้าเปลี่ยน Step ใหม่ ให้รีเซ็ต retry เฉพาะกิจสำหรับ match_phase
        if last_step_idx != state["cur"]:
            if step.get("is_match_phase"):
                state["retry"] = 0  # บังคับเริ่มนับ 1 ใหม่สำหรับช่วงแข่ง
            last_step_idx = state["cur"]

        limit = MATCH_WAIT_LIMIT if state["in_match"] else NORMAL_WAIT_LIMIT

        # --- 🛡️ เพิ่มระบบ Wait for 50 before Scan ---
        if step.get("is_match_phase") and state["retry"] < 50:
            state["retry"] += 1
            # แสดง Label ให้ชัดเจนว่ากำลังรอกดของขั้นตอนไหน
            print(f"⏳ {step['label']}: ช่วงแข่ง ({state['retry']}/50) ", end="\r")
            time.sleep(1.0) 
            continue
            
        print(f"🔍 กำลังหาภาพ: {step['label']} | ครั้งที่: {state['retry'] + 1}/{limit}  ", end="\r")
        res = find_best_match(step["files"], step["thresh"])
        
        if res:
            handle_success(step, res)
        else:
            handle_failure(step, available_keys)

if __name__ == "__main__":
    time.sleep(2)
    try: main_loop()
    except KeyboardInterrupt: print("\n🔍 หยุดการทำงานโดยผู้ใช้")