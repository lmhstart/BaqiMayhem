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
HIGHLIGHT = (255, 215, 0)      # 金色高亮
BUTTON_COLOR = (60, 64, 72)
BUTTON_HOVER = (80, 84, 92)
RED = (220, 80, 80)

# ==========================================
# ======= 【重点】 游戏手感/难度可调参数 =======
# ==========================================

# 1. 玩家控制方块的自然下落速度 (毫秒)
# 数值越大越慢。例如 1000 代表每 1 秒掉一格，500 代表 0.5 秒掉一格。
NORMAL_DROP_INTERVAL = 800  # <--- [调整这里] 改小变快，改大变慢

# 2. 消除后悬空方块掉落的动画速度 (像素/帧)
# 数值越大掉得越快。20 是比较平滑的速度。
ANIMATION_DROP_SPEED = 15   # <--- [调整这里] 建议范围 10-50

# 3. "大石头" 生成机制
STONE_INITIAL_DELAY = 10000 # 游戏开始后多少毫秒(ms)生成第一波石头 (10000 = 10秒)
STONE_INTERVAL = 15000      # 之后每隔多少毫秒生成一次石头 (15000 = 15秒)

# 4. 分数规则
SCORE_PER_BLOCK = 10        # 普通方块消除得分 (基数)
STONE_BONUS = 100           # 消除石头的额外奖励分

# ==========================================

# 逻辑网格 (不要动)
GRID_WIDTH = 6
GRID_HEIGHT = 12

global_state = {
    "volume": 5,
    "screen_size": (SCREEN_WIDTH, SCREEN_HEIGHT),
    "fullscreen": False
}
