# baqi/settings.py
import pygame

# --- 屏幕基础配置 ---
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# --- 视觉颜色定义 ---
WHITE = (240, 240, 240)
BLACK = (20, 20, 20)
GRAY = (180, 180, 180)
DARK_GRAY = (40, 44, 52)
PANEL_BG = (30, 33, 40, 200)
HIGHLIGHT = (255, 215, 0)
BUTTON_COLOR = (60, 64, 72)
BUTTON_HOVER = (80, 84, 92)
RED = (220, 80, 80)

# ==========================================
# ======= 【重点】 游戏手感/难度可调参数 =======
# ==========================================

# 1. 玩家控制方块的自然下落速度 (毫秒)
# 原来是800，现在改为400，速度更快更自然
NORMAL_DROP_INTERVAL = 400

# 2. 消除后悬空方块掉落的动画速度
ANIMATION_DROP_SPEED = 15

# 3. "大石头" 生成机制
STONE_INITIAL_DELAY = 10000
STONE_INTERVAL = 15000

# 4. 分数规则
SCORE_PER_BLOCK = 10
STONE_BONUS = 100

# 5. 爆炸动画参数
EXPLOSION_FRAME_DURATION = 30
EXPLOSION_SCALE = 2.0

# 6. 技能冷却与配置
SKILL_COOLDOWN_KEQING = 45000   # 45秒
SKILL_COOLDOWN_GANYU = 30000    # 30秒
SKILL_COOLDOWN_ZHONGLI = 45000  # 45秒
SKILL_COOLDOWN_ZIBAI = 40000    # 40秒

# 角色ID常量
CHAR_NONE = "None"
CHAR_KEQING = "Keqing"
CHAR_GANYU = "Ganyu"
CHAR_ZHONGLI = "Zhongli"
CHAR_ZIBAI = "Zibai"

# ==========================================

# 逻辑网格
GRID_WIDTH = 6
GRID_HEIGHT = 12

global_state = {
    "volume": 5,
    "screen_size": (SCREEN_WIDTH, SCREEN_HEIGHT),
    "fullscreen": False,
    "current_character": CHAR_NONE
}
