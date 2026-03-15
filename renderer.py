# baqi/renderer.py
import pygame
from settings import *
from resources import R
from cards import ALL_CARDS

CARD_TIER_COLOR = {
    "01": (80,  130, 220),
    "02": (80,  180, 100),
    "03": (200, 80,  80),
}

class GameRenderer:
    def __init__(self):
        self._ghost_surfs = {}

    def _get_ghost_surf(self, color, cell_size):
        key = (color, cell_size)
        if key not in self._ghost_surfs:
            img = R.get_scaled_block(color, cell_size)
            if img:
                surf = img.copy()
                surf.set_alpha(GHOST_ALPHA)
            else:
                surf = pygame.Surface((cell_size, cell_size), pygame.SRCALPHA)
                surf.fill((200, 200, 200, GHOST_ALPHA))
            self._ghost_surfs[key] = surf
        return self._ghost_surfs[key]

    def clear_caches(self):
        self._ghost_surfs.clear()

    # ─── 棋盘及元素绘制 (保持原有) ───
    def draw_game_board(self, screen, game, x, y, width, height):
        cell_size  = height // GRID_HEIGHT
        board_px_w = cell_size * GRID_WIDTH
        board_px_h = cell_size * GRID_HEIGHT
        offset_x   = x + (width - board_px_w) // 2
        offset_y   = y
        board_rect = pygame.Rect(offset_x, offset_y, board_px_w, board_px_h)

        pygame.draw.rect(screen, (40, 30, 25), board_rect)
        for i in range(1, GRID_WIDTH):
            lx = offset_x + i * cell_size
            pygame.draw.line(screen, (60, 50, 45), (lx, offset_y), (lx, offset_y + board_px_h), 1)
        for i in range(1, GRID_HEIGHT):
            ly = offset_y + i * cell_size
            pygame.draw.line(screen, (60, 50, 45), (offset_x, ly), (offset_x + board_px_w, ly), 1)

        original_clip = screen.get_clip()
        screen.set_clip(board_rect)

        current_positions = {(b['x'], b['y']) for b in game.current_blocks}
        for gb in game.get_ghost_blocks():
            if gb['y'] >= 0 and (gb['x'], gb['y']) not in current_positions:
                gs = self._get_ghost_surf(gb['color'], cell_size)
                if gs:
                    screen.blit(gs, (offset_x + gb['x'] * cell_size,
                                     offset_y + gb['y'] * cell_size))

        animating_targets = {(a.end_y, a.x) for a in game.effects_manager.falling_anims}

        for gy in range(GRID_HEIGHT):
            for gx in range(GRID_WIDTH):
                block = game.grid[gy][gx]
                if not block or (gy, gx) in animating_targets:
                    continue
                self._draw_cell(
                    screen, gx, gy, block, offset_x, offset_y, cell_size,
                    highlight =(game.internal_state == STATE_PRE_CLEAR and
                                (gy, gx) in game.elimination_list),
                    has_mark  = game.marks[gy][gx],
                    has_smoke = game.smoke_mask[gy][gx] > 0,
                    has_mint  = game.mint_mask[gy][gx])

        for anim in game.effects_manager.falling_anims:
            anim.draw(screen, offset_x, offset_y, cell_size)
        for exp in game.effects_manager.explosions:
            exp.draw(screen, offset_x, offset_y, cell_size)
        for sword in game.effects_manager.swords:
            sword.draw(screen, offset_x, offset_y, cell_size)

        for b in game.current_blocks:
            if b['y'] >= 0:
                img = R.get_scaled_block(b['color'], cell_size)
                if img:
                    screen.blit(img, (offset_x + b['x'] * cell_size,
                                      offset_y + b['y'] * cell_size))

        # ── 注意：陨石移出 clip 区域之外绘制，见下方 ──

        screen.set_clip(original_clip)

        # 【修复 Bug1】陨石在 set_clip(original_clip) 之后绘制：
        #   陨石使用绝对屏幕坐标 self.y，从 y<0（屏顶以上）出发向下运动。
        #   若在 board_rect clip 内绘制，陨石在进入棋盘前完全不可见，
        #   对于目标行靠近顶部的情况，几乎看不到任何视觉效果。
        #   移到 clip 重置之后，陨石可从屏幕顶部开始显示，"从天而降"效果正常。
        if game.effects_manager.meteor:
            game.effects_manager.meteor.draw(screen, offset_x, board_px_w, cell_size)

        for ft in game.effects_manager.floating_texts:
            ft.draw(screen, R.font)

        pygame.draw.rect(screen, (160, 120, 80), board_rect.inflate(10, 10),
                         width=6, border_radius=8)
        return board_rect

    def _draw_cell(self, screen, gx, gy, color, ox, oy, cs,
                   highlight=False, has_mark=False, has_smoke=False, has_mint=False):
        dest_x = ox + gx * cs
        dest_y = oy + gy * cs

        if has_smoke:
            img = R.get_scaled_block('smoke', cs)
            if img:
                screen.blit(img, (dest_x, dest_y))
            return

        img = R.get_scaled_block(color, cs)
        if not img:
            return
        screen.blit(img, (dest_x, dest_y))

        if has_mark:
            mark = R.get_scaled_block('mark_cover', cs)
            if mark:
                screen.blit(mark, (dest_x, dest_y))
        if has_mint:
            mint = R.get_scaled_block('mint', cs)
            if mint:
                screen.blit(mint, (dest_x, dest_y))
        if highlight:
            s = pygame.Surface((cs, cs), pygame.SRCALPHA)
            alpha = 80 + int(60 * abs((pygame.time.get_ticks() % 400) / 200 - 1))
            s.fill((255, 255, 255, alpha))
            screen.blit(s, (dest_x, dest_y))

    def _draw_left_panel(self, screen, game):
        PX = 14     
        py = 16     
        if game.owned_cards:
            lbl = R.font_sm.render("已持有卡牌", True, (160, 140, 100))
            screen.blit(lbl, (PX, py));  py += 26
            for cid in game.owned_cards[-8:]:   
                if cid not in ALL_CARDS:
                    continue
                tier = cid[:2]
                col  = CARD_TIER_COLOR.get(tier, (160, 160, 160))
                t    = R.font_sm.render(f"· {ALL_CARDS[cid]['name']}", True, col)
                screen.blit(t, (PX + 4, py));  py += 22
            py += 10  
            
        def txt(s, c=(200, 200, 200)):
            nonlocal py
            surf = R.font_sm.render(s, True, c)
            screen.blit(surf, (PX, py));  py += 24

        if game.zibai_pause_timer   > 0: txt(f"兹白之力: {int(game.zibai_pause_timer/1000)}s",   (100, 255, 200))
        if game.shield_active_timer > 0: txt(f"玉璋护盾: {int(game.shield_active_timer/1000)}s", (255, 200,  50))

        for cid, data in game.active_buffs.items():
            if cid in ALL_CARDS:
                name = ALL_CARDS[cid]['name']
                if "timer" in data: txt(f"{name}: {60 - int(data['timer']/1000)}s")
                else: txt(name)

    def draw_hud(self, screen, game, board_rect):
        cell_size      = board_rect.width // GRID_WIDTH
        skill_btn_rect = pygame.Rect(0, 0, 0, 0)
        self._draw_left_panel(screen, game)

        lw = int(cell_size * 2.5)
        lh = int(cell_size * 4.0)
        lx = board_rect.left - lw - 24
        ly = board_rect.top  + 50
        pygame.draw.line(screen, (139, 69, 19),
                         (lx + lw // 2, board_rect.top), (lx + lw // 2, ly), 4)
        pygame.draw.rect(screen, (240, 230, 210), (lx, ly, lw, lh), border_radius=10)
        pygame.draw.rect(screen, (160,  82,  45), (lx, ly, lw, lh), 4, border_radius=10)
        next_t = R.font_sm.render("NEXT", True, (100, 50, 20))
        screen.blit(next_t, (lx + (lw - next_t.get_width()) // 2, ly + 12))

        if game.next_blocks_data:
            c1, c2 = game.next_blocks_data
            ps = int(cell_size * 0.85)
            px = lx + (lw - ps) // 2
            py = ly + 55
            for color in (c1, c2):
                img = R.get_scaled_block(color, ps)
                if img: screen.blit(img, (px, py))
                py += ps + 4

        sc_x = board_rect.right + 80
        sc_y = board_rect.top   + 80
        pygame.draw.circle(screen, (50, 40, 40), (sc_x, sc_y), 62)
        pygame.draw.circle(screen, (255, 215, 0), (sc_x, sc_y), 62, 3)
        sl = R.font_sm.render("得分", True, (200, 200, 200))
        sv = R.font.render(str(game.score), True, WHITE)
        screen.blit(sl, sl.get_rect(center=(sc_x, sc_y - 18)))
        screen.blit(sv, sv.get_rect(center=(sc_x, sc_y + 18)))

        # 【核心修改】：进度条算法适配非线性字典
        if game.card_draw_index < len(CARD_DRAW_THRESHOLDS):
            target_score = CARD_DRAW_THRESHOLDS[game.card_draw_index]
            prev_score   = 0 if game.card_draw_index == 0 else CARD_DRAW_THRESHOLDS[game.card_draw_index - 1]
            current      = game.score - prev_score
            total_req    = target_score - prev_score
            prog         = min(1.0, max(0.0, current / total_req))
        else:
            prog = 1.0  # 已经满级

        bar_w   = 120
        bar_rect= pygame.Rect(sc_x - bar_w // 2, sc_y + 72, bar_w, 8)
        pygame.draw.rect(screen, (60, 60, 60), bar_rect, border_radius=4)
        fill = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_w * prog), 8)
        pygame.draw.rect(screen, (255, 215, 0), fill, border_radius=4)
        
        # 提示文字
        avail = [k for k in ALL_CARDS if k not in game.owned_cards]
        text_status = "下一张卡" if len(avail) > 0 else "卡池已空"
        ct_s = R.font_sm.render(text_status, True, (160, 160, 160))
        screen.blit(ct_s, ct_s.get_rect(center=(sc_x, sc_y + 90)))

        cy_start = sc_y + 110
        char_names = {CHAR_NONE:"无", CHAR_KEQING:"刻晴",
                      CHAR_GANYU:"甘雨", CHAR_ZHONGLI:"钟离", CHAR_ZIBAI:"兹白"}
        name = char_names.get(global_state['current_character'], "?")
        ct = R.font_sm.render(f"角色: {name}", True, (200, 180, 255))
        screen.blit(ct, ct.get_rect(center=(sc_x, cy_start)))

        if global_state['current_character'] != CHAR_NONE:
            btn_r  = 38
            btn_cx = sc_x
            btn_cy = cy_start + 68
            skill_btn_rect = pygame.Rect(btn_cx - btn_r, btn_cy - btn_r, btn_r*2, btn_r*2)

            prog_e = game.skill_manager.get_cooldown_progress(pygame.time.get_ticks())
            ready  = prog_e >= 1.0
            base_col = (80, 180, 80) if ready else (60, 60, 60)
            pygame.draw.circle(screen, base_col, (btn_cx, btn_cy), btn_r)
            pygame.draw.circle(screen, (200,200,200) if ready else (120,120,120),
                               (btn_cx, btn_cy), btn_r, 3)

            if not ready:
                mask   = pygame.Surface((btn_r*2, btn_r*2), pygame.SRCALPHA)
                filled = int(btn_r*2 * prog_e)
                pygame.draw.circle(mask, (0,0,0,160), (btn_r, btn_r), btn_r)
                pygame.draw.rect(mask, (0,0,0,0), (0, btn_r*2 - filled, btn_r*2, filled))
                screen.blit(mask, (btn_cx - btn_r, btn_cy - btn_r))

            et = R.font.render("E", True, WHITE if ready else GRAY)
            screen.blit(et, et.get_rect(center=(btn_cx, btn_cy)))

            if not ready:
                rem = game.skill_manager.get_remaining_seconds(pygame.time.get_ticks())
                rt  = R.font_sm.render(str(rem), True, (255, 200, 80))
                screen.blit(rt, rt.get_rect(center=(btn_cx, btn_cy + btn_r + 14)))

        if game.q_skill_id:
            btn_r  = 28
            btn_cx = sc_x
            btn_cy = cy_start + 158
            now        = pygame.time.get_ticks()
            q_elapsed  = now - game.q_skill_last_used
            q_ready    = q_elapsed >= 60000
            if q_ready:
                game.q_skill_ready = True
            base_col = (100, 200, 255) if q_ready else (40, 80, 100)
            pygame.draw.circle(screen, base_col, (btn_cx, btn_cy), btn_r)
            pygame.draw.circle(screen, (150,230,255) if q_ready else (80,130,160),
                               (btn_cx, btn_cy), btn_r, 2)
            qt = R.font.render("Q", True, WHITE)
            screen.blit(qt, qt.get_rect(center=(btn_cx, btn_cy)))
            if not q_ready:
                rem_q = int((60000 - q_elapsed) / 1000)
                rq = R.font_sm.render(str(rem_q), True, (200, 180, 80))
                screen.blit(rq, rq.get_rect(center=(btn_cx, btn_cy + btn_r + 12)))

        return skill_btn_rect

    def draw_card_selection(self, screen, game):
        sw, sh = global_state['screen_size']
        cx, cy = sw // 2, sh // 2

        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))

        now         = pygame.time.get_ticks()
        title_alpha = 180 + int(75 * abs((now % 1200) / 600 - 1))
        title_surf  = R.font_lg.render("获得新卡牌", True, (255, 215, 0))
        title_surf.set_alpha(title_alpha)
        screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 280)))

        card_w, card_h = 280, 420
        gap     = 40
        start_x = cx - (card_w * 3 + gap * 2) // 2
        game.card_rects = []
        mx, my  = pygame.mouse.get_pos()

        for i, card_id in enumerate(game.current_card_choices):
            if card_id not in ALL_CARDS:
                continue

            x    = start_x + i * (card_w + gap)
            y    = cy - card_h // 2
            rect = pygame.Rect(x, y, card_w, card_h)
            game.card_rects.append((rect, card_id))

            hovered   = rect.collidepoint((mx, my))
            draw_rect = rect.inflate(16, 16) if hovered else rect

            tier     = card_id[:2]
            tier_col = CARD_TIER_COLOR.get(tier, (80, 80, 120))
            bg_col   = tuple(min(255, c + 30) for c in tier_col) if hovered else (25, 25, 38)
            pygame.draw.rect(screen, bg_col, draw_rect, border_radius=16)

            border_col = (255, 230, 50) if hovered else tier_col
            pygame.draw.rect(screen, border_col, draw_rect,
                             4 if hovered else 2, border_radius=16)

            img = R.get_card_image(card_id)
            if img:
                scaled = R.get_scaled(f"card_{card_id}", card_w, card_h)
                if scaled: screen.blit(scaled, rect)
            else:
                name  = ALL_CARDS[card_id]['name']
                nsurf = R.font.render(name, True, (255, 215, 0))
                screen.blit(nsurf, nsurf.get_rect(center=(rect.centerx, rect.centery)))

        # 【核心修改】：添加跳过/关闭按钮
        skip_surf = R.font.render("× 跳过选卡", True, (200, 200, 200))
        skip_rect = skip_surf.get_rect(center=(cx, cy + card_h // 2 + 58)) 
        bg_skip   = skip_rect.inflate(30, 16)
        
        # 如果有刷新按钮，让它俩并排显示
        if "0304" in game.owned_cards and game.card_manager.reroll_counts > 0:
            skip_rect.centerx -= 120
            bg_skip.centerx -= 120
            
            rr_surf = R.font.render(f"刷新 ({game.card_manager.reroll_counts}次)", True, WHITE)
            rr_rect = rr_surf.get_rect(center=(cx + 120, cy + card_h // 2 + 58))
            bg_rr   = rr_rect.inflate(24, 14)
            pygame.draw.rect(screen, (80, 40, 40),  bg_rr, border_radius=8)
            pygame.draw.rect(screen, (160, 80, 80), bg_rr, 2, border_radius=8)
            screen.blit(rr_surf, rr_rect)
            game.reroll_rect = rr_rect
        else:
            game.reroll_rect = None

        # 绘制跳过按钮
        hover_skip = skip_rect.collidepoint((mx, my))
        pygame.draw.rect(screen, (70, 70, 70) if hover_skip else (50, 50, 50), bg_skip, border_radius=8)
        pygame.draw.rect(screen, (120, 120, 120), bg_skip, 2, border_radius=8)
        screen.blit(skip_surf, skip_rect)
        game.skip_rect = skip_rect

    def draw_game_over(self, screen, game):
        sw, sh  = global_state['screen_size']
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        screen.blit(overlay, (0, 0))
        cx, cy = sw // 2, sh // 2

        panel = pygame.Rect(0, 0, 420, 280)
        panel.center = (cx, cy)
        pygame.draw.rect(screen, (30, 20, 20), panel, border_radius=18)
        pygame.draw.rect(screen, (200, 80, 80), panel, 3, border_radius=18)

        t1   = R.font_lg.render("胜负已分", True, RED)
        sc_s = R.font.render(f"最终得分：{game.score}", True, WHITE)
        hint = R.font_sm.render("点击任意处返回主菜单", True, GRAY)
        screen.blit(t1,   t1.get_rect(center=(cx, cy - 70)))
        screen.blit(sc_s, sc_s.get_rect(center=(cx, cy)))
        screen.blit(hint, hint.get_rect(center=(cx, cy + 70)))

    def draw_pause(self, screen, btn_resume, btn_to_menu):
        from ui import draw_panel
        sw, sh  = global_state['screen_size']
        cx, cy  = sw // 2, sh // 2
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(0, 0, 320, 260)
        panel_rect.center = (cx, cy)
        draw_panel(screen, panel_rect)
        pt = R.font_lg.render("暂  停", True, WHITE)
        screen.blit(pt, pt.get_rect(center=(cx, cy - 80)))
        btn_resume.draw(screen)
        btn_to_menu.draw(screen)