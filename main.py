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
    print("="*65 + "\n🚀 Awakening System: Check Image Every 3s (15s MAX)\n" + "="*65)
    available_keys = list(set([step['post_key'] for step in FARM_STEPS if 'post_key' in step] + ['U']))
    last_step_idx = -1
    step_start_time = time.time()

    while True:
        step = FARM_STEPS[state["cur"]]
        
        # ✅ เช็คว่าถ้าเปลี่ยน Step ใหม่ ให้รีเซ็ตตัวแปรต่างๆ
        if last_step_idx != state["cur"]:
            state["retry"] = 0
            step_start_time = time.time()
            last_step_idx = state["cur"]

        # --- 🛡️ ระบบ Wait สำหรับ Match Phase (รอ MATCH_PHASE_WAIT_COUNT ครั้งก่อนเช็ครูป) ---
        if step.get("is_match_phase") and state["retry"] < MATCH_PHASE_WAIT_COUNT:
            state["retry"] += 1
            print(f"⏳ {step['label']}: ช่วงแข่ง (รอ {state['retry']}/{MATCH_PHASE_WAIT_COUNT}) ", end="\r")
            time.sleep(1.0)
            continue
        
        # --- 📊 ระบบเช็ครูปทุก 3 วินาที ในช่วง 15 วินาที ---
        elapsed_in_step = time.time() - step_start_time
        
        if elapsed_in_step < MAX_WAIT_TIME:
            # คำนวณจุดเช็ครูป (0, 3, 6, 9, 12)
            check_point = (state["retry"] * CHECK_INTERVAL)
            time_until_next_check = check_point - elapsed_in_step
            
            if time_until_next_check > 0.1:
                # ยังไม่ถึงเวลาเช็ค ให้รอต่อ
                print(f"⏳ {step['label']}: รอ ({elapsed_in_step:.1f}s) ", end="\r")
                time.sleep(0.1)
                continue
            
            # ถึงเวลาเช็ครูปแล้ว
            state["retry"] += 1
            print(f"🔍 เช็ครูป {step['label']}: ครั้งที่ {state['retry']}/5 ({elapsed_in_step:.1f}s) ", end="\r")
            res = find_best_match(step["files"], step["thresh"])
            
            if res:
                handle_success(step, res)
                step_start_time = time.time()
            else:
                # ยังหาไม่เจอ ให้รอการเช็คครั้งถัดไป
                time.sleep(0.2)
        else:
            # หมดเวลา 15 วินาที ให้ทำ step back
            print(f"\n❌ หมดเวลา {MAX_WAIT_TIME}s ที่ {step['label']}")
            handle_failure(step, available_keys)
            step_start_time = time.time()

if __name__ == "__main__":
    time.sleep(2)
    try: main_loop()
    except KeyboardInterrupt: print("\n🔍 หยุดการทำงานโดยผู้ใช้")