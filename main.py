# baqi/main.py
import pygame
import sys
import os
import ctypes
from settings import *
from resources import R
from ui import Button, Slider, draw_panel
from game_logic import Game
from renderer import GameRenderer

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

pygame.init()
pygame.display.set_caption("八奇乱斗")

# ─── 加载游戏图标（优先尝试 PNG，再尝试 ICO） ───
try:
    icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'images')
    icon_png = os.path.join(icon_dir, 'hutaoicon.png')
    icon_ico = os.path.join(icon_dir, 'hutaoicon.ico')
    
    # 强烈建议把图标存为 PNG！Pygame加载Windows ICO很容易报错
    if os.path.exists(icon_png):
        pygame.display.set_icon(pygame.image.load(icon_png))
    elif os.path.exists(icon_ico):
        pygame.display.set_icon(pygame.image.load(icon_ico))
except Exception as e:
    pass

R.load_assets()
R.play_music()

screen = pygame.display.set_mode(global_state['screen_size'], pygame.RESIZABLE)
clock  = pygame.time.Clock()

current_state = STATE_MENU
game     = Game()
renderer = GameRenderer()

def _cx(): return global_state['screen_size'][0] // 2
def _cy(): return global_state['screen_size'][1] // 2

def make_menu_buttons():
    cx, cy, s = _cx(), _cy(), (60, 40, 30)
    labels = ["开始对局", "角色选择", "音量设置", "调整分辨率", "退出游戏"]
    return [Button(cx - 120, cy - 60 + i * 70, 240, 50, lbl, R.font, bg_color=s)
            for i, lbl in enumerate(labels)]

def make_char_buttons():
    cx, cy = _cx(), _cy()
    chars = [
        ("无角色",   CHAR_NONE,    "无特殊技能"),
        ("刻晴",     CHAR_KEQING,  "雷楔：标记方块，消除触发菱形爆炸"),
        ("甘雨",     CHAR_GANYU,   "霜华矢：接下来5组方块全部同色"),
        ("钟离",     CHAR_ZHONGLI, "天星：召唤陨石摧毁顶部3层方块"),
        ("兹白",     CHAR_ZIBAI,   "灵驹：每3秒抛入结晶马，落地3秒后爆炸"),
    ]
    btns = []
    total_h = len(chars) * 90
    sy = cy - total_h // 2
    for i, (label, val, desc) in enumerate(chars):
        bg = (100, 80, 150) if global_state['current_character'] == val else BUTTON_COLOR
        btn = Button(cx - 250, sy + i * 90, 500, 60, label, R.font, bg_color=bg)
        btn.desc     = desc
        btn.char_val = val
        btns.append(btn)
    return btns

resolutions = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]

menu_buttons  = make_menu_buttons()
char_buttons  = make_char_buttons()
btn_back_char = Button(0, 0, 200, 50, "返回", R.font)
slider_vol    = Slider(0, 0, 300, 20, 0, 10, global_state['volume'])
btn_back_vol  = Button(0, 0, 200, 50, "返回", R.font)
btn_back_scr  = Button(0, 0, 200, 50, "返回", R.font)
btn_pause     = Button(20, 20, 80, 40, "暂停", R.font, bg_color=(60, 40, 30))
btn_resume    = Button(0, 0, 200, 50, "继续", R.font)
btn_to_menu   = Button(0, 0, 200, 50, "退出", R.font)
screen_buttons = []
skill_btn_rect = pygame.Rect(0, 0, 0, 0)

def update_layout():
    global menu_buttons, char_buttons, screen_buttons
    cx, cy = _cx(), _cy()
    menu_buttons = make_menu_buttons()
    char_buttons = make_char_buttons()
    btn_back_char.rect.center = (cx, cy + 300)
    slider_vol.rect.center    = (cx, cy)
    slider_vol.update_handle_pos()
    btn_back_vol.rect.center  = (cx, cy + 100)
    screen_buttons = []
    sy = cy - (len(resolutions) * 60) // 2
    for i, res in enumerate(resolutions):
        bg = (80, 100, 80) if res == global_state['screen_size'] else BUTTON_COLOR
        btn = Button(cx - 150, sy + i * 60, 300, 50, f"{res[0]}x{res[1]}", R.font, bg_color=bg)
        screen_buttons.append((btn, res))
    btn_back_scr.rect.center  = (cx, sy + len(resolutions) * 60 + 40)
    btn_resume.rect.center    = (cx, cy - 30)
    btn_to_menu.rect.center   = (cx, cy + 40)

update_layout()

def handle_resize(size):
    global screen
    global_state['screen_size'] = size
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    R.clear_scale_cache()
    renderer.clear_caches()
    update_layout()

def draw_background():
    bg = R.get_scaled('background', *global_state['screen_size'])
    if bg: screen.blit(bg, (0, 0))
    else: screen.fill((40, 30, 25))

def draw_menu():
    draw_background()
    cx, cy = _cx(), _cy()
    now = pygame.time.get_ticks()
    glow = 180 + int(75 * abs((now % 2000) / 1000 - 1))
    title = R.font_lg.render("八奇乱斗", True, (255, 215, 0))
    title.set_alpha(glow)
    screen.blit(title, title.get_rect(center=(cx, cy - 200)))
    sub = R.font_sm.render("Roguelike Edition", True, (180, 160, 100))
    screen.blit(sub, sub.get_rect(center=(cx, cy - 155)))
    for btn in menu_buttons: btn.draw(screen)

def draw_char_select():
    draw_background()
    cx, cy = _cx(), _cy()
    t = R.font_lg.render("选择出战角色", True, WHITE)
    screen.blit(t, t.get_rect(center=(cx, cy - 290)))
    for btn in char_buttons:
        btn.draw(screen)
        if btn.desc:
            ds = R.font_sm.render(btn.desc, True, (180, 180, 180))
            screen.blit(ds, ds.get_rect(center=(cx, btn.rect.bottom + 14)))
    btn_back_char.draw(screen)

def draw_game():
    global skill_btn_rect
    draw_background()
    sw, sh = global_state['screen_size']
    board_h   = (sh - 80) // GRID_HEIGHT * GRID_HEIGHT
    cell_size = board_h // GRID_HEIGHT
    board_w   = cell_size * GRID_WIDTH
    bx = (sw - board_w) // 2
    by = (sh - board_h) // 2

    board_rect = renderer.draw_game_board(screen, game, bx, by, board_w, board_h)
    skill_btn_rect = renderer.draw_hud(screen, game, board_rect)
    btn_pause.draw(screen)

    if game.internal_state == STATE_SELECT_CARD:
        renderer.draw_card_selection(screen, game)
    elif game.game_over_flag:
        renderer.draw_game_over(screen, game)
    elif game.paused:
        renderer.draw_pause(screen, btn_resume, btn_to_menu)

def draw_vol_settings():
    draw_background()
    cx, cy = _cx(), _cy()
    draw_panel(screen, pygame.Rect(cx - 210, cy - 170, 420, 320))
    title = R.font.render("音量设置", True, WHITE)
    screen.blit(title, title.get_rect(center=(cx, cy - 120)))
    slider_vol.draw(screen, R.font_sm)
    btn_back_vol.draw(screen)

def draw_screen_settings():
    draw_background()
    cx, cy = _cx(), _cy()
    t = R.font.render("分辨率设置", True, WHITE)
    screen.blit(t, t.get_rect(center=(cx, _cy() - (len(resolutions) * 60) // 2 - 40)))
    for b, _ in screen_buttons: b.draw(screen)
    btn_back_scr.draw(screen)

while True:
    events = pygame.event.get()
    mx, my = pygame.mouse.get_pos()

    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            handle_resize(event.size)

        if current_state == STATE_MENU:
            for btn in menu_buttons: btn.hovered = btn.rect.collidepoint((mx, my))
            if event.type == pygame.MOUSEBUTTONDOWN:
                if   menu_buttons[0].rect.collidepoint(event.pos): game.start_new_game(); current_state = STATE_GAME
                elif menu_buttons[1].rect.collidepoint(event.pos): char_buttons = make_char_buttons(); current_state = STATE_CHAR_SELECT
                elif menu_buttons[2].rect.collidepoint(event.pos): current_state = STATE_SETTINGS_VOL
                elif menu_buttons[3].rect.collidepoint(event.pos): current_state = STATE_SETTINGS_SCREEN
                elif menu_buttons[4].rect.collidepoint(event.pos): pygame.quit(); sys.exit()

        elif current_state == STATE_CHAR_SELECT:
            for btn in char_buttons: btn.hovered = btn.rect.collidepoint((mx, my))
            btn_back_char.hovered = btn_back_char.rect.collidepoint((mx, my))
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in char_buttons:
                    if btn.rect.collidepoint(event.pos):
                        global_state['current_character'] = btn.char_val
                        char_buttons = make_char_buttons()
                if btn_back_char.rect.collidepoint(event.pos):
                    current_state = STATE_MENU

        elif current_state == STATE_GAME:
            btn_pause.hovered = btn_pause.rect.collidepoint((mx, my))

            if game.game_over_flag:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game.running = False
                    current_state = STATE_MENU

            elif game.internal_state == STATE_SELECT_CARD:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # 【核心修改】：处理跳过选卡按钮的点击
                    if hasattr(game, 'skip_rect') and game.skip_rect and game.skip_rect.collidepoint(event.pos):
                        game.resume_from_card_select()
                        continue
                        
                    if hasattr(game, 'card_rects'):
                        for rect, cid in game.card_rects:
                            if rect.collidepoint(event.pos):
                                game.card_manager.apply_card_effect(game, cid)
                                game.resume_from_card_select()
                                break
                    if game.reroll_rect and game.reroll_rect.collidepoint(event.pos):
                        game.card_manager.reroll_counts -= 1
                        game.current_card_choices = game.card_manager.draw_three_cards(game.owned_cards)

            elif game.paused:
                btn_resume.hovered  = btn_resume.rect.collidepoint((mx, my))
                btn_to_menu.hovered = btn_to_menu.rect.collidepoint((mx, my))
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_resume.rect.collidepoint(event.pos): game.toggle_pause()
                    elif btn_to_menu.rect.collidepoint(event.pos): game.running = False; current_state = STATE_MENU

            else:
                if event.type == pygame.KEYDOWN:
                    # 【修复 Bug2】左右移动允许在所有非特殊状态下使用。
                    #   原先限制在 STATE_PLAYING(10) 才能移动，导致钟离E触发后
                    #   整条动画链（PRE_CLEAR→EXPLODING→ANIMATING→POST_FALL）期间
                    #   无法操作，体感像"卡死"。
                    #   这四个状态里 self.grid 已是最终态（消除/落定后），
                    #   碰撞检测完全正确，允许移动安全。
                    #   下键加速和旋转仍只在 STATE_PLAYING 生效（避免在动画中乱入）。
                    _MOVABLE_STATES = (STATE_PLAYING, STATE_PRE_CLEAR,
                                       STATE_EXPLODING, STATE_ANIMATING,
                                       STATE_POST_FALL_DELAY)
                    if game.internal_state in _MOVABLE_STATES:
                        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                            np = [{"color": b["color"], "x": b["x"] - 1, "y": b["y"]} for b in game.current_blocks]
                            if not game.check_collision(np): game.current_blocks = np
                        elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                            np = [{"color": b["color"], "x": b["x"] + 1, "y": b["y"]} for b in game.current_blocks]
                            if not game.check_collision(np): game.current_blocks = np
                    if game.internal_state == STATE_PLAYING:
                        if event.key == pygame.K_DOWN or event.key == pygame.K_s:
                            if not game.disable_down_key:
                                np = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in game.current_blocks]
                                if not game.check_collision(np): game.current_blocks = np
                        elif event.key == pygame.K_SPACE or event.key == pygame.K_w:  
                            game.rotate_blocks()
                        elif event.key == pygame.K_UP:
                            pass 

                    if event.key in (pygame.K_e, pygame.K_KP1): game.skill_manager.try_trigger(game)
                    elif event.key in (pygame.K_q, pygame.K_KP2): game.try_use_q_skill()
                    elif event.key == pygame.K_ESCAPE: game.toggle_pause()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if skill_btn_rect.collidepoint(event.pos):
                        game.skill_manager.try_trigger(game)

            if (event.type == pygame.MOUSEBUTTONDOWN and not game.game_over_flag
                    and game.internal_state != STATE_SELECT_CARD and not game.paused):
                if btn_pause.rect.collidepoint(event.pos): game.toggle_pause()

        elif current_state == STATE_SETTINGS_VOL:
            if slider_vol.handle_event(event):
                global_state['volume'] = slider_vol.val; R.update_volume()
            if event.type == pygame.MOUSEBUTTONDOWN and btn_back_vol.rect.collidepoint(event.pos): current_state = STATE_MENU

        elif current_state == STATE_SETTINGS_SCREEN:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for b, res in screen_buttons:
                    if b.rect.collidepoint(event.pos): handle_resize(res)
                if btn_back_scr.rect.collidepoint(event.pos): current_state = STATE_MENU

    if current_state == STATE_GAME: game.update()

    if   current_state == STATE_MENU:            draw_menu()
    elif current_state == STATE_CHAR_SELECT:     draw_char_select()
    elif current_state == STATE_GAME:            draw_game()
    elif current_state == STATE_SETTINGS_VOL:    draw_vol_settings()
    elif current_state == STATE_SETTINGS_SCREEN: draw_screen_settings()

    pygame.display.flip()
    clock.tick(FPS)