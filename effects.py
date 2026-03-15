# baqi/effects.py
import pygame
from settings import *


class FloatingText:
    """消除后浮动的得分/提示文字"""
    def __init__(self, text, x, y, color=(255, 215, 0), scale=1.0):
        self.text  = text
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.scale = scale
        self.alpha = 255
        self.finished = False
        self.born = pygame.time.get_ticks()

    def update(self, current_time):
        elapsed = current_time - self.born
        if elapsed >= FLOAT_TEXT_LIFE:      # ← [可调] FLOAT_TEXT_LIFE 在 settings.py
            self.finished = True
            return
        t = elapsed / FLOAT_TEXT_LIFE
        self.y    -= 1.4                    # ← [可调] 上飘速度 (px/帧)
        self.alpha = max(0, int(255 * (1.0 - t ** 0.6)))   # ← [可调] 渐出曲线指数

    def draw(self, screen, font):
        if self.alpha <= 0:
            return
        surf = font.render(self.text, True, self.color)
        if self.scale != 1.0:
            w = max(1, int(surf.get_width()  * self.scale))
            h = max(1, int(surf.get_height() * self.scale))
            surf = pygame.transform.scale(surf, (w, h))
        surf.set_alpha(self.alpha)
        screen.blit(surf, (int(self.x) - surf.get_width() // 2, int(self.y)))


class Explosion:
    def __init__(self, grid_x, grid_y, color):
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.color  = color
        self.frame_index = 0
        self.finished    = False
        self.last_update = pygame.time.get_ticks()
        self.frame_rate  = EXPLOSION_FRAME_DURATION  # ← [可调] 在 settings.py

    def update(self, current_time):
        if current_time - self.last_update > self.frame_rate:
            self.last_update = current_time
            self.frame_index += 1
            if self.frame_index >= 20:
                self.finished = True

    def draw(self, screen, offset_x, offset_y, cell_size):
        from resources import R
        frames = R.get_explosion_frames(self.color)
        if frames and self.frame_index < len(frames):
            scale_size = int(cell_size * 1.3)   # ← [可调] 爆炸视觉缩放倍数（相对格子）
            scaled = pygame.transform.scale(frames[self.frame_index], (scale_size, scale_size))
            cx = offset_x + self.grid_x * cell_size + cell_size // 2
            cy = offset_y + self.grid_y * cell_size + cell_size // 2
            screen.blit(scaled, scaled.get_rect(center=(cx, cy)))


class FallingAnim:
    def __init__(self, x, start_y, end_y, color):
        self.x         = x
        self.start_y   = start_y
        self.end_y     = end_y
        self.current_y = float(start_y)
        self.color     = color
        self.finished  = False
        self.speed     = 0.2    # ← [可调] 初始下落速度（格子/帧）
        self.gravity   = 0.05   # ← [可调] 加速度（格子/帧²）

    def update(self):
        self.speed    += self.gravity
        self.current_y += self.speed
        if self.current_y >= self.end_y:
            self.current_y = self.end_y
            self.finished  = True

    def draw(self, screen, offset_x, offset_y, cell_size):
        from resources import R
        img = R.get_scaled_block(self.color, cell_size)
        if img:
            screen.blit(img, (offset_x + self.x * cell_size,
                              offset_y + int(self.current_y) * cell_size))


class MeteoriteAnim:
    """
    【修复 1】陨石大小改为按格子数缩放，避免原始 540×540 贴图占满屏幕。
    显示大小由 settings.METEOR_DISPLAY_SIZE 控制（单位：格子数）。
    """
    def __init__(self, target_row_y, board_height_px):
        self.target_row    = target_row_y
        self.board_height_px = board_height_px
        self.y             = -300   # 屏幕上方出发
        self.speed         = 10     # ← [可调] 陨石下落速度 (px/帧)
        self.finished      = False

    def update(self, board_top_y, cell_size):
        self.y += self.speed
        impact_y = board_top_y + self.target_row * cell_size
        if self.y >= impact_y:
            self.finished = True
            return True
        return False

    def draw(self, screen, board_offset_x, board_width, cell_size):
        """cell_size 由 renderer 传入，用于计算合适的显示尺寸"""
        from resources import R
        img = R.get_block_image('meteorite')
        if img:
            cx   = board_offset_x + board_width // 2
            size = cell_size * METEOR_DISPLAY_SIZE  # ← [可调] METEOR_DISPLAY_SIZE 在 settings.py
            scaled = pygame.transform.scale(img, (size, size))
            screen.blit(scaled, scaled.get_rect(center=(cx, int(self.y))))


class SwordAnim:
    """
    【修复 2】雨帘剑从上往下运动（原为从下往上）。
    self.y 使用绝对屏幕坐标（与 MeteoriteAnim 保持一致）。
    """
    def __init__(self, col_idx, board_height_px):
        self.col             = col_idx
        self.board_height_px = board_height_px
        self.y               = -200     # 从屏幕顶部上方出发
        self.speed           = 30       # ← [可调] 雨帘剑下落速度 (px/帧)
        self.finished        = False

    def update(self):
        self.y += self.speed            # 向下移动
        if self.y > self.board_height_px + 200:
            self.finished = True

    def draw(self, screen, offset_x, offset_y, cell_size):
        from resources import R
        img = R.get_block_image('sword')
        if img:
            w = cell_size
            h = cell_size * 3           # ← [可调] 剑气高度（格子数×格子高）
            scaled = pygame.transform.scale(img, (w, h))
            # self.y 是绝对 y；offset_x 是棋盘左边缘
            screen.blit(scaled, (offset_x + self.col * cell_size, int(self.y)))