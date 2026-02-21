# baqi/renderer.py
import pygame
from settings import *
from resources import R
from game_logic import STATE_PRE_CLEAR


class GameRenderer:
    def __init__(self):
        pass

    def draw_game_board(self, screen, game, x, y, width, height):
        cell_size = height // GRID_HEIGHT
        board_pixel_w = cell_size * GRID_WIDTH
        board_pixel_h = cell_size * GRID_HEIGHT

        offset_x = x + (width - board_pixel_w) // 2
        offset_y = y
        board_rect = pygame.Rect(offset_x, offset_y, board_pixel_w, board_pixel_h)

        # 背景
        pygame.draw.rect(screen, (40, 30, 25), board_rect)
        for i in range(1, GRID_WIDTH):
            lx = offset_x + i * cell_size
            pygame.draw.line(screen, (60, 50, 45), (lx, offset_y), (lx, offset_y + board_pixel_h), 2)
        for i in range(1, GRID_HEIGHT):
            ly = offset_y + i * cell_size
            pygame.draw.line(screen, (60, 50, 45), (offset_x, ly), (offset_x + board_pixel_w, ly), 2)

        original_clip = screen.get_clip()
        screen.set_clip(board_rect)

        def draw_cell(cx, cy, color, highlight=False, has_mark=False):
            img = R.get_block_image(color)
            if not img: return
            dest_x = offset_x + cx * cell_size
            dest_y = offset_y + cy * cell_size
            scaled = pygame.transform.scale(img, (cell_size, cell_size))
            screen.blit(scaled, (dest_x, dest_y))

            # 绘制雷楔标记
            if has_mark:
                mark_img = R.get_block_image('mark_cover')
                if mark_img:
                    scaled_mark = pygame.transform.scale(mark_img, (cell_size, cell_size))
                    screen.blit(scaled_mark, (dest_x, dest_y))

            if highlight:
                s = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                alpha = 100 + int(50 * (pygame.time.get_ticks() % 200) / 200)
                s.fill((255, 255, 255, alpha))
                screen.blit(s, (dest_x, dest_y))

        # 1. 计算正在下落的格子 (不画静态图)
        animating_targets = set()
        for anim in game.effects_manager.falling_anims:
            animating_targets.add((anim.target_y, anim.x))

        # 2. 画静态网格
        for gy in range(GRID_HEIGHT):
            for gx in range(GRID_WIDTH):
                block = game.grid[gy][gx]
                if block:
                    if (gy, gx) in animating_targets: continue
                    is_elim_target = (game.internal_state == STATE_PRE_CLEAR and (gy, gx) in game.elimination_list)
                    has_mark = game.marks[gy][gx]
                    draw_cell(gx, gy, block, highlight=is_elim_target, has_mark=has_mark)

        # 3. 画下落动画
        for anim in game.effects_manager.falling_anims:
            anim.draw(screen, offset_x, offset_y, cell_size)

        # 4. 画爆炸
        for exp in game.effects_manager.explosions:
            exp.draw(screen, offset_x, offset_y, cell_size)

        # 5. 画玩家方块
        for b in game.current_blocks:
            if b['y'] >= 0:
                draw_cell(b['x'], b['y'], b['color'])

        # 6. 【新增】画钟离天星
        if game.effects_manager.meteor:
            game.effects_manager.meteor.draw(screen, offset_x, board_pixel_w)

        screen.set_clip(original_clip)
        pygame.draw.rect(screen, (160, 120, 80), board_rect.inflate(10, 10), width=6, border_radius=8)

        return board_rect
