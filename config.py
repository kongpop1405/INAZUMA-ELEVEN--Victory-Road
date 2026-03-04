import pyautogui
import os
import win32con

# --- 🎯 FARM_STEPS: ลำดับขั้นตอนการทำงาน ---
# --- 🎯 FARM_STEPS: ปรับเวลาตามสถิติ JSON ล่าสุด ---
# --- 🎯 FARM_STEPS: ฉบับแก้ไขเพื่อลด Step Back (อ้างอิงจากสถิติ 55 รอบ) ---
FARM_STEPS = [
    {
        "label": "Station",
        "files": ['station1.png', 'station2.png','station3.png', 'station4.png', 'station5.png', 'station6.png'],
        "thresh": 0.30, 
        "post_delay": 2.5  # ปรับเพิ่มจาก 2.48s ตามสถิติ 55 รอบ (avg: 2.25s, optimized: 2.48s) เพื่อให้หน้าจอเมนูหลักนิ่งสนิท
    },
    {
        "label": "Hero Battle",
        "files": ['HeroBattle.png'],
        "thresh": 0.80,    # คงความเข้มงวดไว้สูงเพื่อกัน "ตาฝาด" ในช่วงรอยต่อหน้าจอ
        "post_delay": 4.0  # ปรับตามค่าเฉลี่ยจริง 3.64s และ optimized delay 4.0s เพื่อจังหวะที่แม่นยำที่สุด
    },
    {
        "label": "Start Match",
        "files": ['StartMatch.png', 'StartMatch2.png', 'StartMatch3.png'],
        "thresh": 0.20,    # ใช้ Thresh ต่ำเพราะปุ่มนี้มักมีแสงเงารบกวนจากพื้นหลังสนาม
        "post_delay": 2.9  # คงค่าเดิมตามสถิติ (avg: 2.64s, optimized: 2.9s) เพื่อรอให้ปุ่มปรากฏชัดเจนก่อนคลิก
    },
    {
        "label": "Yes",
        "files": ['Yes.png'],
        "thresh": 0.25, 
        "post_delay": 1.6  # ปรับเพิ่มเล็กน้อยจาก 1.58s ตามสถิติ (avg: 1.44s, optimized: 1.58s) เพื่อความเสถียร
    },
    {
        "label": "Press",
        "files": ['Press.png'],
        "thresh": 0.25, 
        "post_delay": 8.7  # ปรับตามค่าเฉลี่ย 7.92s และ optimized delay 8.71s เพื่อรองรับจังหวะโหลดเข้าสู่โหมดเตรียมทีม
    },
    {
        "label": "Formation",
        "files": ['set1.png', 'set2.png'],
        "thresh": 0.25, 
        "post_delay": 9.0,  # ปรับตามค่าเฉลี่ย 8.22s และ optimized delay 9.04s เพื่อให้มั่นใจว่าหน้าจัดแผนโหลดเสร็จก่อนกด ALT
        "post_key": 'ALT'
    },
    {
        "label": "Next 1",
        "files": ['next.png', 'next2.png', 'next3.png', 'next4.png', 'next5.png', 'next6.png'],
        "thresh": 0.25, 
        "post_delay": 9.2  # คงค่าเดิมตาม optimized delay 9.04s เป็นจุดที่ใช้เวลาโหลดนานที่สุดจุดหนึ่ง
    },
    {
        "label": "Next 2",
        "files": ['next.png', 'next2.png', 'next3.png', 'next4.png', 'next5.png', 'next6.png'],
        "thresh": 0.25, 
        "post_delay": 4.2  # ปรับตามค่าเฉลี่ย 4.13s และ optimized delay 4.15s เพื่อแก้ปัญหา Kickoff วืด
    },
    {
        "label": "Kickoff",
        "files": ['kickoff.png'],
        "thresh": 0.20,    # 🎯 ลด Thresh ลงเพื่อแก้ปัญหา Step Back 20 ครั้ง ให้บอทหาปุ่มเจอแม้แสงในสนามจะเปลี่ยน
        "post_delay": 3.7, # คงค่าเดิมตาม optimized delay 3.7s (avg: 3.36s) 🎯 Step Back ลดเหลือ 21 ครั้งจากเดิม 
        "post_key": 'U'
    },
    {
        "label": "Formation (จบครึ่งแรก)",
        "files": ['set1.png', 'set2.png'],
        "thresh": 0.25, 
        "post_delay": 2.0, 
        "is_match_phase": True # คงระบบวนลูปสแกนจนกว่าจะจบครึ่งแรก
    },
    {
        "label": "Next (จบครึ่งหลัง)",
        "files": ['next.png', 'next2.png', 'next3.png', 'next4.png', 'next5.png', 'next6.png'],
        "thresh": 0.55,    # ตั้งค่าสูงเป็นพิเศษเพื่อกันบอทเผลอไปกดปุ่มอื่นในระหว่างที่บอลยังไม่หยุดนิ่ง
        "post_delay": 2.5, 
        "is_match_phase": True
    },
    {
        "label": "Final Result",
        "files": ['next.png', 'next2.png', 'next3.png', 'next4.png', 'next5.png', 'next6.png'],
        "thresh": 0.20, 
        "post_delay": 1.9  # ปรับลดจาก 2.3s ตามสถิติ (avg: 1.71s, optimized: 1.88s) เป็นขั้นตอนที่เสถียรที่สุด (Step Back แค่ 1 ครั้ง)
    },
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
NORMAL_WAIT_LIMIT = 5        # 5 ครั้ง × 3 วินาที = 15 วินาท ท total wait time
STATION_STUCK_LIMIT = 10
CONSECUTIVE_BACK_LIMIT = 3   # จำนวนครั้งที่ยอมให้ถอยซ้ำที่เดิมก่อน Hard Reset
NEXT_CLICK_INTERVAL = 5      # ทุกๆ กี่รอบที่หาไม่เจอ ถึงจะทำการคลิกย้ำ
CHECK_INTERVAL = 3.0         # เช็ครูปทุก 3 วินาที
MAX_WAIT_TIME = 15.0         # เวลาสูงสุดต่อ step คือ 15 วินาที
MATCH_PHASE_WAIT_COUNT = 50  # จำนวนครั้งที่รอก่อนเช็ครูปในช่วงแข่ง

# --- Timings ---
POST_MATCH_REST = 10.0       # เวลาพักหลังจบรอบ
DEFAULT_POST_DELAY = 0.1
KEY_PRESS_DURATION = 0.1     # ระยะเวลาการกดปุ่มค้าง (วินาที)