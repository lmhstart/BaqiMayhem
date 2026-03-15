# baqi/settings.py
import pygame

# --- 屏幕基础配置 ---
SCREEN_WIDTH  = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- 视觉颜色定义 ---
WHITE       = (240, 240, 240)
BLACK       = (20,  20,  20)
GRAY        = (180, 180, 180)
DARK_GRAY   = (40,  44,  52)
PANEL_BG    = (30,  33,  40,  200)
HIGHLIGHT   = (255, 215, 0)
BUTTON_COLOR= (60,  64,  72)
BUTTON_HOVER= (80,  84,  92)
RED         = (220, 80,  80)

# ── 下落速度 ──────────────────────────────────────────────────
NORMAL_DROP_INTERVAL  = 400     
ANIMATION_DROP_SPEED  = 15      

# ── 石头生成 ──────────────────────────────────────────────────
STONE_INITIAL_DELAY   = 10000   
STONE_INTERVAL        = 15000   

# ── 分数与抽卡 (非线性配置) ───────────────────────────────────
SCORE_PER_BLOCK       = 10      
STONE_BONUS           = 50

# 【新增可调】：非线性的选卡分数阈值列表（你可以随意增加、修改这里的数值）
CARD_DRAW_THRESHOLDS = [
    1000, 2000, 4000, 6000, 8000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 50000
]

# ── 技能冷却 (ms) ──────────────────────────────────────────────
SKILL_COOLDOWN_KEQING  = 45000  
SKILL_COOLDOWN_GANYU   = 30000  
SKILL_COOLDOWN_ZHONGLI = 60000  
SKILL_COOLDOWN_ZIBAI   = 40000  

# ── 动效参数 ──────────────────────────────────────────────────
EXPLOSION_FRAME_DURATION = 30   
EXPLOSION_SCALE          = 2.0  
METEOR_DISPLAY_SIZE      = 4    
GHOST_ALPHA              = 70   
FLOAT_TEXT_LIFE          = 1200 

CARD_TIER_WEIGHTS = {
    "01": 5,    
    "02": 3,    
    "03": 1,    
}

# 角色 ID 常量
CHAR_NONE    = "None"
CHAR_KEQING  = "Keqing"
CHAR_GANYU   = "Ganyu"
CHAR_ZHONGLI = "Zhongli"
CHAR_ZIBAI   = "Zibai"

# 逻辑网格
GRID_WIDTH  = 6
GRID_HEIGHT = 12

# --- 游戏/App 状态常量 ---
STATE_MENU           = "menu"
STATE_GAME           = "game"
STATE_CHAR_SELECT    = "char_select"
STATE_SETTINGS_VOL   = "settings_vol"
STATE_SETTINGS_SCREEN= "settings_screen"

STATE_PLAYING        = 10
STATE_PRE_CLEAR      = 11
STATE_EXPLODING      = 12
STATE_ANIMATING      = 13
STATE_POST_FALL_DELAY= 14
STATE_SELECT_CARD    = "select_card"

global_state = {
    "volume"           : 5,
    "screen_size"      : (SCREEN_WIDTH, SCREEN_HEIGHT),
    "fullscreen"       : False,
    "current_character": CHAR_NONE,
}
