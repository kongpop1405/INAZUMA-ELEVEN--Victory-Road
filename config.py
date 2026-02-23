import pyautogui
import os
import win32con

# --- 🎯 FARM_STEPS: ลำดับขั้นตอนการทำงาน ---
# --- 🎯 FARM_STEPS: ปรับเวลาตามสถิติ JSON ล่าสุด ---
FARM_STEPS = [
    {"files": ['station1.png', 'station2.png', 'station4.png'], "thresh": 0.1, "label": "Station", "post_delay": 2.4}, # สถิติ 2.34s
    {"files": ['HeroBattle.png'], "thresh": 0.22, "label": "Hero Battle", "post_delay": 0.5}, # สถิติ 0.46s
    {"files": ['StartMatch.png'], "thresh": 0.25, "label": "Start Match", "post_delay": 0.7}, # สถิติ 0.63s
    {"files": ['Yes.png'], "thresh": 0.25, "label": "Yes", "post_delay": 7.0},
    {"files": ['Press.png'], "thresh": 0.25, "label": "Press", "post_delay": 6.8}, # สถิติ 6.63s (จุดโหลดนาน)
    {"files": ['set1.png', 'set2.png'], "thresh": 0.25, "label": "Formation", "post_delay": 1.2, "post_key": 'ALT'}, # สถิติ 1.08s
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 1", "post_delay": 2.2}, # สถิติ 4.04s
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 2", "post_delay": 4.9}, # สถิติ 0.86s
    {"files": ['kickoff.png'], "thresh": 0.25, "label": "Kickoff", "post_delay": 3.2, "post_key": 'U'}, # สถิติ 3.18s
    
    # ✅ ระบบ Match Phase: รอให้นับถึง 50 ก่อนเริ่มเช็คภาพ
    {"files": ['set1.png', 'set2.png'], "thresh": 0.25, "label": "Formation (จบครึ่งแรก)", "post_delay": 2.0, "post_key": 'ALT', "is_match_phase": True},
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "next (จบครึ่งหลัง)", "post_delay": 2.0, "is_match_phase": True},

    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 2", "post_delay": 1.0}, 
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Result 3", "post_delay": 1.5}, # สถิติ 1.45s
]

# --- ⚙️ การตั้งค่าระบบ ---

# --- Screen Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
CX, CY = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

# --- File Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")
SCREENSHOT_DIR = os.path.join(BASE_DIR, "logs_screenshots")
STATS_FILE = os.path.join(BASE_DIR, "bot_stats.json")

# --- Limits & Thresholds ---
MATCH_WAIT_LIMIT = 200
NORMAL_WAIT_LIMIT = 20
STATION_STUCK_LIMIT = 10
CONSECUTIVE_BACK_LIMIT = 3   # จำนวนครั้งที่ยอมให้ถอยซ้ำที่เดิมก่อน Hard Reset
NEXT_CLICK_INTERVAL = 5      # ทุกๆ กี่รอบที่หาไม่เจอ ถึงจะทำการคลิกย้ำ

# --- Timings ---
POST_MATCH_REST = 15.0       # เวลาพักหลังจบรอบ
DEFAULT_POST_DELAY = 0.1
KEY_PRESS_DURATION = 0.1     # ระยะเวลาการกดปุ่มค้าง (วินาที)