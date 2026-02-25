import pyautogui
import os
import win32con

# --- 🎯 FARM_STEPS: ลำดับขั้นตอนการทำงาน ---
# --- 🎯 FARM_STEPS: ปรับเวลาตามสถิติ JSON ล่าสุด ---
# --- 🎯 FARM_STEPS: ฉบับแก้ไขเพื่อลด Step Back (อ้างอิงจากสถิติ 51 รอบ) ---
FARM_STEPS = [
    {
        "label": "Station",
        "files": ['station1.png', 'station2.png','station3.png', 'station4.png'],
        "thresh": 0.40, 
        "post_delay": 3.0  # ปรับเพิ่มจาก 2.48s เพื่อให้หน้าจอเมนูหลักนิ่งสนิท ลด Step Back ที่เคยสูงถึง 6 ครั้ง
    },
    {
        "label": "Hero Battle",
        "files": ['HeroBattle.png'],
        "thresh": 0.80,    # คงความเข้มงวดไว้สูงเพื่อกัน "ตาฝาด" ในช่วงรอยต่อหน้าจอ
        "post_delay": 3.6  # ปรับตามค่าเฉลี่ยจริงที่บอทใช้ (3.65s) เพื่อจังหวะที่แม่นยำที่สุด [Awakening]
    },
    {
        "label": "Start Match",
        "files": ['StartMatch.png'],
        "thresh": 0.20,    # ใช้ Thresh ต่ำเพราะปุ่มนี้มักมีแสงเงารบกวนจากพื้นหลังสนาม
        "post_delay": 2.9  # ปรับตามค่าเฉลี่ยจริง 2.9s เพื่อรอให้ปุ่มปรากฏชัดเจนก่อนคลิก
    },
    {
        "label": "Yes",
        "files": ['Yes.png'],
        "thresh": 0.25, 
        "post_delay": 1.6  # ปรับตามค่าเฉลี่ย 1.58s เป็นจุดที่ทำงานได้เสถียรอยู่แล้ว
    },
    {
        "label": "Press",
        "files": ['Press.png'],
        "thresh": 0.25, 
        "post_delay": 7.3  # ปรับตามค่าเฉลี่ย 7.32s เพื่อรองรับจังหวะโหลดเข้าสู่โหมดเตรียมทีม
    },
    {
        "label": "Formation",
        "files": ['set1.png', 'set2.png'],
        "thresh": 0.25, 
        "post_delay": 8.7, # ปรับตามค่าเฉลี่ย 8.71s เพื่อให้มั่นใจว่าหน้าจัดแผนโหลดเสร็จก่อนกด ALT
        "post_key": 'ALT'
    },
    {
        "label": "Next 1",
        "files": ['next1.png'],
        "thresh": 0.25, 
        "post_delay": 9.2  # ปรับตามค่าเฉลี่ย 9.23s เป็นจุดที่ใช้เวลาโหลดนานที่สุดจุดหนึ่ง
    },
    {
        "label": "Next 2",
        "files": ['next1.png'],
        "thresh": 0.25, 
        "post_delay": 4.5  # 🚀 ปรับเพิ่มจาก 3.7s เพื่อแก้ปัญหา Kickoff วืด (ให้หน้าจอ Kickoff มีเวลานิ่งมากขึ้น)
    },
    {
        "label": "Kickoff",
        "files": ['kickoff.png'],
        "thresh": 0.20,    # 🎯 ลด Thresh ลงเพื่อแก้ปัญหา Step Back 20 ครั้ง ให้บอทหาปุ่มเจอแม้แสงในสนามจะเปลี่ยน
        "post_delay": 3.7, 
        "post_key": 'U'
    },
    {
        "label": "Formation (จบครึ่งแรก)",
        "files": ['set1.png'],
        "thresh": 0.25, 
        "post_delay": 2.0, 
        "is_match_phase": True # คงระบบวนลูปสแกนจนกว่าจะจบครึ่งแรก
    },
    {
        "label": "Next (จบครึ่งหลัง)",
        "files": ['next1.png'],
        "thresh": 0.55,    # ตั้งค่าสูงเป็นพิเศษเพื่อกันบอทเผลอไปกดปุ่มอื่นในระหว่างที่บอลยังไม่หยุดนิ่ง
        "post_delay": 2.5, 
        "is_match_phase": True
    },
    {
        "label": "Final Result",
        "files": ['next1.png'],
        "thresh": 0.20, 
        "post_delay": 2.3  # ปรับตามค่าเฉลี่ย 2.25s เป็นขั้นตอนที่เสถียรที่สุด (Step Back แค่ 1 ครั้ง)
    },
]

# --- ⚙️ การตั้งค่าระบบ ---

# --- 🖥️ Screen & Window Settings ---
SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
CX, CY = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
GAME_WINDOW_TITLE = "Inazuma Eleven: Victory Road" # เตรียมไว้สำหรับ Window-Based

# --- 📂 Path Settings ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(BASE_DIR, "img")
LOG_DIR = os.path.join(BASE_DIR, "logs")
SCREENSHOT_DIR = os.path.join(LOG_DIR, "screenshots")
STATS_FILE = os.path.join(BASE_DIR, "bot_stats.json")

# --- ⚙️ Bot Logic Limits ---
MATCH_WAIT_LIMIT = 200
NORMAL_WAIT_LIMIT = 30
CONSECUTIVE_BACK_LIMIT = 3
NEXT_CLICK_INTERVAL = 5      # คลิกย้ำทุกๆกี่ครั้งที่หาภาพไม่เจอ
MATCH_PHASE_SCAN_DELAY = 50  # จำนวนรอบที่ให้รอก่อนเริ่มสแกนจริงใน Match Phase
ENABLE_SCREENSHOT = True     # ✅ เพิ่มที่นี่: True = เปิดการบันทึกภาพเมื่อพลาด, False = ปิด
MAX_SCREENSHOTS = 50         # ✅ เพิ่มที่นี่: จำนวนรูปภาพสูงสุดที่จะเก็บไว้ (เช่น 50 รูป)

# --- ⌨️ Input Settings ---
KEY_PRESS_DURATION = 0.1     # เวลาที่กดปุ่มค้างไว้ (วินาที)
POST_MATCH_REST = 10.0       # พักจบรอบ
DEFAULT_POST_DELAY = 0.1

# --- 🚨 Discord Notify Settings (เตรียมไว้สำหรับระบบใหม่) ---
DISCORD_WEBHOOK_URL = ""     # ใส่ URL เมื่อต้องการใช้งาน
ENABLE_NOTIFY = False        # เปิด-ปิด ระบบแจ้งเตือน