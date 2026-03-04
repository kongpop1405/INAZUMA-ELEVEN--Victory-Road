import pyautogui, time, gc, random
import win32con
from config import *
from utils import update_step_stats, find_best_match, press_key, save_error_screenshot

state = {
    "cur": 0, 
    "retry": 0, 
    "last_time": time.time(), 
    "in_match": False,
    "next_click_count": 0, 
    "consecutive_back_steps": 0, 
    "last_back_step_idx": -1, 
    "rounds": 0,
    "formation_retry_count": 0,  # <--- ตัวนับจำนวนครั้งที่ติดลูปครึ่งแรก
    "skip_match_wait": False,     # <--- ข้าม wait phase เมื่อ Step Back มาจาก step อื่น
    "step_back_occurred": False,  # <--- ข้าม check interval เมื่อเพิ่ง Step Back
    "force_normal_wait": False    # <--- ใช้ MAX_WAIT_TIME ปกติ (5 ครั้ง) แทน match phase (40 ครั้ง)
}

def handle_success(step, res, step_start_time):
    global state
    state["consecutive_back_steps"] = 0
    state["last_back_step_idx"] = -1
    state["formation_retry_count"] = 0  # รีเซ็ตตัวนับลูป Formation เมื่อสำเร็จ
    state["force_normal_wait"] = False  # รีเซ็ต limit กลับเป็น match phase ปกติ
    
    now = time.time()
    elapsed = now - step_start_time
    x, y, acc, name = res
    
    # ดึงค่า delay จาก config
    post_delay = step.get("post_delay", DEFAULT_POST_DELAY)

    # 1. สั่งคลิกเป้าหมาย
    pyautogui.click(x, y)
    
    # 2. ตรวจสอบว่ามีปุ่มคีย์บอร์ดที่ต้องกดหรือไม่
    if 'post_key' in step:
        print(f"   ∟ ⌨️ Action: กดปุ่ม {step['post_key']}")
        press_key(step['post_key'])
        
    # 3. 🖱️ ย้ายเมาส์หลบไปตรงกลางจอ เพื่อไม่ให้บังภาพหรือติด Hover Effect
    pyautogui.moveTo(CX, CY)
    
    # 4. รอตาม config
    time.sleep(post_delay)

    # ⏱️ หยุดนับ — actual_delay นับตั้งแต่เริ่ม step จนถึงหลัง sleep ครบทั้งกระบวนการ
    actual_delay = time.time() - step_start_time

    # Clear บรรทัด 🔍 เช็ครูป ก่อนพิมพ์ผลสำเร็จ
    print(f"\r{' ' * 80}\r", end="")
    print(f"✅ เจอภาพ: {step['label']} | Acc: {acc:.2f} | ใช้เวลาหา: {elapsed:.2f}s")
    print(f"   ∟ ⏱️ Delay จริง: {actual_delay:.2f}s (ตั้งไว้: {post_delay}s)")

    # เช็คว่าเป็นขั้นตอนสุดท้ายหรือไม่ เพื่อให้นับ total_rounds ได้ถูกต้อง
    is_final_step = (step['label'] == "Final Result")

    # อัปเดตสถิติ (ส่งพารามิเตอร์แบบระบุชื่อเพื่อป้องกัน Error)
    update_step_stats(
        step_label=step['label'], 
        elapsed_time=elapsed, 
        is_end=is_final_step, 
        actual_post_delay=actual_delay,
        is_step_back=False
    )
    
    # เคลียร์ Memory (RAM) ทุกครั้งที่จบ 1 รอบ ป้องกันบอท [Awakening] ค้างตอนรันยาวๆ
    if is_final_step:
        gc.collect()
        print(f"   ∟ ⏸️ หน่วงเวลา 5s หลังจบรอบ...")
        time.sleep(5.0)

    # เลื่อนไปยัง Step ถัดไป (และวนลูปกลับไป 0 หากถึงขั้นสุดท้าย)
    state["cur"] = (state["cur"] + 1) % len(FARM_STEPS)

def handle_failure(step, available_keys):
    global state
    state["retry"] += 1
    limit = MATCH_WAIT_LIMIT if state["in_match"] else NORMAL_WAIT_LIMIT

    if state["retry"] >= limit:
        # --- 🔄 ลองเช็ครูปของ step ก่อนหน้าก่อน Step Back ---
        prev_idx = (state["cur"] - 1) % len(FARM_STEPS)
        prev_step = FARM_STEPS[prev_idx]
        
        print(f"\n🔄 [RETRY] ลองเช็ครูป {prev_step['label']} (ก่อนหน้า) ก่อน Step Back")
        res = find_best_match(prev_step["files"], prev_step["thresh"])
        
        if res:
            print(f"✅ เจอรูป {prev_step['label']} ขณะค้น Step Back - ย้อนกลับไป")
            state["cur"] = prev_idx
            state["retry"] = 0
            state["last_time"] = time.time()
            # 🖱️ เพิ่มการย้ายเมาส์กลับตรงกลางเผื่อไว้
            pyautogui.moveTo(CX, CY) 
            time.sleep(0.5)
            return
        
        # --- ถ้าไม่เจอ ให้ทำการ Step Back ตามปกติ ---
        update_step_stats(
            step_label=step['label'], 
            elapsed_time=0.0, 
            is_end=False, 
            is_step_back=True
        )

        if state["last_back_step_idx"] == state["cur"]:
            state["consecutive_back_steps"] += 1
        else:
            state["consecutive_back_steps"] = 1
            state["last_back_step_idx"] = state["cur"]

        print(f"❌ [LOG] พลาด {step['label']} ต่อเนื่องครั้งที่ {state['consecutive_back_steps']}")

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
        state["step_back_occurred"] = True  # เช็ครูปทันทีในรอบถัดไป
        state["force_normal_wait"] = True   # ใช้ limit 5 ครั้งแทน 40 ครั้ง
        
        # --- ถ้า step ใหม่เป็น match_phase ให้ข้ามจังหวะรอ และเช็ครูปเลย ---
        next_step = FARM_STEPS[state["cur"]]
        if next_step.get("is_match_phase"):
            state["skip_match_wait"] = True  # ข้าม wait phase ทั้งหมดเลย
        else:
            state["retry"] = 0
        
        state["next_click_count"] = 0
        state["in_match"] = False
        state["last_time"] = time.time()
        
        # 🖱️ ย้ายเมาส์ไปตรงกลางหลังจบกระบวนการ Step Back (อันนี้มีอยู่เดิมแล้ว ทำงานได้ถูกต้องครับ)
        pyautogui.moveTo(CX, CY)

    time.sleep(0.2 if not state["in_match"] else 1.0)

def main_loop():
    print("="*65 + "\n🚀 [Awakening] System: Check Image Every 3s (Match Phase Support)\n" + "="*65)
    available_keys = list(set([step.get('post_key') for step in FARM_STEPS if 'post_key' in step] + ['U']))
    last_step_idx = -1
    step_start_time = time.time()
    wait_count = 0  
    check_count = 0 

    while True:
        step = FARM_STEPS[state["cur"]]
        
        # ✅ 1. รีเซ็ตเมื่อเปลี่ยน Step (หรือเมื่อเพิ่ง Step Back)
        if last_step_idx != state["cur"] or state.get("step_back_occurred"):
            wait_count = 0
            check_count = 0
            step_start_time = time.time()
            last_step_idx = state["cur"]
            state["step_back_occurred"] = False

        # ✅ 2. ช่วงรอ (Wait Phase) สำหรับ Match Phase (รอ 120/120)
        if step.get("is_match_phase") and state.get("skip_match_wait"):
            wait_count = MATCH_PHASE_WAIT_COUNT  # ข้ามไปเช็ครูปเลย
            state["skip_match_wait"] = False
            step_start_time = time.time()
        if step.get("is_match_phase") and wait_count < MATCH_PHASE_WAIT_COUNT:
            wait_count += 1
            print(f"⏳ {step['label']}: ช่วงแข่ง (รอ {wait_count}/{MATCH_PHASE_WAIT_COUNT})   ", end="\r")
            time.sleep(MATCH_PHASE_WAIT_TIME)
            if wait_count == MATCH_PHASE_WAIT_COUNT:
                print()
                step_start_time = time.time() # รีเซ็ตเวลาเพื่อเริ่มนับช่วงเช็ครูป
            continue
        
        # ✅ 3. ช่วงเช็ครูป (Check Phase)
        elapsed_in_step = time.time() - step_start_time
        is_forced_normal = state.get("force_normal_wait") and step.get("is_match_phase")
        max_wait = MAX_WAIT_TIME if (not step.get("is_match_phase") or is_forced_normal) else MAX_WAIT_TIME_MATCH_PHASE
        
        if elapsed_in_step < max_wait:
            check_point = (check_count * CHECK_INTERVAL)
            
            if elapsed_in_step >= check_point:
                check_count += 1
                max_checks = int(max_wait / CHECK_INTERVAL)
                print(f"🔍 เช็ครูป {step['label']}: ครั้งที่ {check_count}/{max_checks} ({elapsed_in_step:.1f}s)   ", end="\r")
                
                res = find_best_match(step["files"], step["thresh"])
                if res:
                    print() # 🛠️ ล็อกข้อความ "เช็ครูป" ล่าสุดไว้บนหน้าจอไม่ให้โดนทับ
                    handle_success(step, res, step_start_time)
                    continue 
                
            time.sleep(0.1) 
            
        else:
                # Step อื่นๆ ให้ถอยหลังทันที (พิมพ์ข้อความแค่ครั้งเดียว)
                print(f"\n❌ หมดเวลา {max_wait}s ที่ {step['label']}")
                
                # 🛠️ บังคับตั้งค่า retry ให้เต็ม limit เพื่อให้ฟังก์ชัน handle_failure 
                # ทำการ Step Back ทันทีโดยไม่ต้องวนลูปพิมพ์ซ้ำ 5 รอบ
                limit = MATCH_WAIT_LIMIT if state["in_match"] else NORMAL_WAIT_LIMIT
                state["retry"] = limit 
                
                handle_failure(step, available_keys)

if __name__ == "__main__":
    time.sleep(2)
    try: main_loop()
    except KeyboardInterrupt: print("\n🔍 หยุดการทำงานโดยผู้ใช้")