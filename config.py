import pyautogui
import os
import win32con

# --- 🎯 FARM_STEPS: ลำดับขั้นตอนการทำงาน ---
# --- 🎯 FARM_STEPS: ปรับเวลาตามสถิติ JSON ล่าสุด ---
# --- 🎯 FARM_STEPS: ฉบับแก้ไขเพื่อลด Step Back (อ้างอิงจากสถิติ 51 รอบ) ---
FARM_STEPS = [
    {"files": ['station1.png', 'station2.png', 'station4.png'], "thresh": 0.1, "label": "Station", "post_delay": 3.5}, # ตามค่า optimized_delay 2.21
    
    # ✅ จุดแก้วงจร Hero Battle -> Start Match
    {"files": ['HeroBattle.png'], "thresh": 0.80, "label": "Hero Battle", "post_delay": 2.5},
    {"files": ['StartMatch.png'], "thresh": 0.18, "label": "Start Match", "post_delay": 1.3}, # ปรับตามค่า optimized_delay 1.28
    
    {"files": ['Yes.png'], "thresh": 0.25, "label": "Yes", "post_delay": 1.4}, # ตามค่า optimized_delay 1.4
    {"files": ['Press.png'], "thresh": 0.25, "label": "Press", "post_delay": 7.7}, # ตามค่า optimized_delay 7.65
    {"files": ['set1.png', 'set2.png'], "thresh": 0.25, "label": "Formation", "post_delay": 8.0, "post_key": 'ALT'}, # ตามค่า optimized_delay 8.04
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 1", "post_delay": 3.9}, # ตามค่า optimized_delay 3.94
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.25, "label": "Next 2", "post_delay": 1.8}, # ตามค่า optimized_delay 1.79
    
    # ✅ จุดแก้ Kickoff วืด
    {"files": ['kickoff.png'], "thresh": 0.25, "label": "Kickoff", "post_delay": 5.6, "post_key": 'U'}, # ตามค่า optimized_delay 5.59
    
    # ส่วนที่เหลือใช้ตามเดิม...
    {"files": ['set1.png', 'set2.png'], "thresh": 0.25, "label": "Formation (จบครึ่งแรก)", "post_delay": 1.5, "post_key": 'ALT', "is_match_phase": True},
    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.55, "label": "Next (จบครึ่งหลัง)", "post_delay": 2.0, "is_match_phase": True},

    {"files": ['next1.png','next2.png', 'next3.png'], "thresh": 0.33, "label": "Final Result", "post_delay": 2.0}, # ตามค่า optimized_delay 1.97
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
NORMAL_WAIT_LIMIT = 30
STATION_STUCK_LIMIT = 10
CONSECUTIVE_BACK_LIMIT = 3   # จำนวนครั้งที่ยอมให้ถอยซ้ำที่เดิมก่อน Hard Reset
NEXT_CLICK_INTERVAL = 5      # ทุกๆ กี่รอบที่หาไม่เจอ ถึงจะทำการคลิกย้ำ

# --- Timings ---
POST_MATCH_REST = 10.0       # เวลาพักหลังจบรอบ
DEFAULT_POST_DELAY = 0.1
KEY_PRESS_DURATION = 0.1     # ระยะเวลาการกดปุ่มค้าง (วินาที)