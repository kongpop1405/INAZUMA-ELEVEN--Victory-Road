import time, gc
from config import *
from screen_manager import ScreenManager
from stats_manager import StatsManager
import utils # สำหรับพวก press_key และ save_screenshot

class AwakeningBot:
    def __init__(self):
        self.screen = ScreenManager()
        self.stats = StatsManager()
        self.state = {
            "cur_idx": 0, "retry": 0, "last_time": time.time(),
            "back_count": 0, "last_back_idx": -1, "total_rounds": 0
        }

    def run(self):
        print("🚀 Awakening System: Standby...")
        time.sleep(2)
        
        while True:
            step = FARM_STEPS[self.state["cur_idx"]]
            is_match = step.get("is_match_phase", False)
            limit = MATCH_WAIT_LIMIT if is_match else NORMAL_WAIT_LIMIT

            # 🛡️ Match Phase Initial Delay (ย้าย logic มาจาก main เดิม)
            if is_match and self.state["retry"] < MATCH_PHASE_SCAN_DELAY:
                self.state["retry"] += 1
                print(f"⏳ {step['label']}: รอกด ({self.state['retry']}/{MATCH_PHASE_SCAN_DELAY})", end="\r")
                time.sleep(1.0)
                continue

            print(f"🔍 หาภาพ: {step['label']} | ครั้งที่: {self.state['retry'] + 1}/{limit}", end="\r")
            res = self.screen.find_best_match(step["files"], step["thresh"])

            if res:
                self._on_success(step, res)
            else:
                self._on_failure(step, limit)

    def _on_success(self, step, res):
        elapsed = time.time() - self.state["last_time"]
        is_end = (self.state["cur_idx"] == len(FARM_STEPS) - 1)
        
        new_delay, rounds = self.stats.update_stats(step['label'], elapsed, is_end)
        print(f"\n✅ เจอ {step['label']} | Acc: {res[2]:.2f} | Time: {elapsed:.2f}s")
        
        utils.perform_click(res[0], res[1]) # ฟังก์ชันใหม่ที่แยกไป utils
        
        if "post_key" in step:
            time.sleep(new_delay)
            utils.press_key(step['post_key'])

        if is_end:
            print(f"\n🏆 จบรอบที่ {rounds} | พัก {POST_MATCH_REST}s")
            time.sleep(POST_MATCH_REST)
            gc.collect()

        self.state.update({"cur_idx": (self.state["cur_idx"]+1)%len(FARM_STEPS), "retry": 0, "last_time": time.time(), "back_count": 0})
        time.sleep(step.get("post_delay", DEFAULT_POST_DELAY))

    def _on_failure(self, step, limit):
        self.state["retry"] += 1
        
        # คลิกย้ำ (เฉพาะปุ่ม Next)
        if "Next" in step['label'] and self.state["retry"] % NEXT_CLICK_INTERVAL == 0:
            utils.perform_click(CX, CY + 150)

        if self.state["retry"] >= limit:
            # ✅ ตรวจสอบ Config ก่อนบันทึกภาพหน้าจอ
            if ENABLE_SCREENSHOT:
                # เรียกใช้ฟังก์ชันบันทึกภาพที่แยกไว้ใน utils
                utils.save_error_screenshot(step['label'])
                print(f"📸 [System] บันทึกภาพความผิดพลาดของ {step['label']} เรียบร้อย")
            
            self.stats.update_stats(step['label'], is_step_back=True)
            self._handle_step_back()

    def _handle_step_back(self):
        # Logic Step Back เดิมจาก main.py
        if self.state["last_back_idx"] == self.state["cur_idx"]:
            self.state["back_count"] += 1
        else:
            self.state["back_count"] = 1
            self.state["last_back_idx"] = self.state["cur_idx"]

        if self.state["back_count"] >= CONSECUTIVE_BACK_LIMIT:
            self.state["cur_idx"] = 0 # Hard Reset
        else:
            self.state["cur_idx"] = max(0, self.state["cur_idx"] - 1)
        
        self.state.update({"retry": 0, "last_time": time.time()})

if __name__ == "__main__":
    bot = AwakeningBot()
    bot.run()