# baqi/effects.py
import pygame
from settings import *
from resources import R


class Explosion:
    def __init__(self, x, y, color):
        self.grid_x = x
        self.grid_y = y
        self.color = color
        self.frames = R.get_explosion_frames(color)
        self.frame_index = 0
        self.last_update = pygame.time.get_ticks()
        self.finished = False

    def update(self, current_time):
        if self.finished: return
        if current_time - self.last_update > EXPLOSION_FRAME_DURATION:
            self.last_update = current_time
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.finished = True

    def draw(self, screen, board_origin_x, board_origin_y, cell_size):
        if self.finished or not self.frames: return

        center_x = board_origin_x + self.grid_x * cell_size + cell_size // 2
        center_y = board_origin_y + self.grid_y * cell_size + cell_size // 2

        frame_img = self.frames[self.frame_index]
        explode_size = int(cell_size * EXPLOSION_SCALE)
        scaled_img = pygame.transform.scale(frame_img, (explode_size, explode_size))

        offset = explode_size // 2
        screen.blit(scaled_img, (center_x - offset, center_y - offset))


class FallingAnim:
    def __init__(self, x, start_grid_y, target_grid_y, color):
        self.x = x
        self.start_y = start_grid_y
        self.target_y = target_grid_y
        self.current_y = float(start_grid_y)
        self.color = color
        self.finished = False

    def update(self):
        if self.finished: return
        # 加快一点消除后的下落动画，使其更流畅
        speed_per_frame = 0.4

        if self.current_y < self.target_y:
            self.current_y += speed_per_frame
            if self.current_y >= self.target_y:
                self.current_y = float(self.target_y)
                self.finished = True

    def draw(self, screen, board_origin_x, board_origin_y, cell_size):
        draw_x = board_origin_x + self.x * cell_size
        draw_y = board_origin_y + int(self.current_y * cell_size)

        img = R.get_block_image(self.color)
        if img:
            scaled = pygame.transform.scale(img, (cell_size, cell_size))
            screen.blit(scaled, (draw_x, draw_y))


# 新增：陨石动画
class MeteoriteAnim:
    def __init__(self, target_grid_y_start, board_pixel_h):
        # 目标是撞击 grid_y 所在的像素位置
        self.target_row = target_grid_y_start
        self.y = -600  # 从屏幕上方很高的地方开始
        self.speed = 15  # 陨石下落速度
        self.finished = False
        self.impacted = False  # 是否已经撞击
        self.board_h = board_pixel_h

    def update(self, board_origin_y, cell_size):
        target_pixel_y = board_origin_y + self.target_row * cell_size

        # 让陨石底部接触到目标行顶部
        # 假设陨石图片被缩放为棋盘宽度 (cell_size * 6)
        meteor_height = cell_size * GRID_WIDTH

        if self.y + meteor_height < target_pixel_y:
            self.y += self.speed
        else:
            self.y = target_pixel_y - meteor_height
            if not self.impacted:
                self.impacted = True
                return True  # 返回 True 表示刚撞击，触发消除逻辑
        return False

    def draw(self, screen, board_origin_x, board_width):
        img = R.get_block_image('meteorite')
        if not img: return
        # 缩放到棋盘宽度
        scaled = pygame.transform.scale(img, (board_width, board_width))
        screen.blit(scaled, (board_origin_x, int(self.y)))
