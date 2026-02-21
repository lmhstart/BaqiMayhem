# baqi/main.py
import pygame
import sys
import ctypes
from settings import *
from resources import R
from ui import Button, Slider, draw_panel
from game_logic import Game
from renderer import GameRenderer

# --- 解决高分屏模糊问题 ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 初始化
pygame.init()
pygame.display.set_caption("八奇乱斗 (Full Characters Update)")

# 资源加载
R.load_assets()
R.play_music()

# 屏幕初始化
screen = pygame.display.set_mode(global_state['screen_size'], pygame.RESIZABLE)
clock = pygame.time.Clock()

# 状态常量
STATE_MENU = 0
STATE_GAME = 1
STATE_SETTINGS_VOL = 2
STATE_SETTINGS_SCREEN = 3
STATE_CHAR_SELECT = 4
current_state = STATE_MENU

# --- 核心实例 ---
game = Game()
renderer = GameRenderer()


# --- UI 布局管理 ---
def get_center():
    return global_state['screen_size'][0] // 2, global_state['screen_size'][1] // 2


# === 菜单按钮 ===
def create_menu_buttons():
    cx, cy = get_center()
    style_bg = (60, 40, 30)
    return [
        Button(cx - 120, cy - 60, 240, 50, "开始对局", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 10, 240, 50, "角色选择", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 80, 240, 50, "音量设置", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 150, 240, 50, "调整分辨率", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 220, 240, 50, "退出游戏", R.font, bg_color=style_bg)
    ]


menu_buttons = create_menu_buttons()

# === 角色选择 UI ===
char_buttons = []
# 这里的 Button 必须在 import ui 之后
btn_back_char = Button(0, 0, 200, 50, "返回", R.font)


def create_char_buttons():
    cx, cy = get_center()
    # 定义角色列表：(显示名, 内部ID, 描述)
    chars = [
        ("无角色", CHAR_NONE, "无特殊技能"),
        ("刻晴", CHAR_KEQING, "雷楔：标记方块，消除触发菱形爆炸"),
        ("甘雨", CHAR_GANYU, "霜华矢：接下来5组方块全部同色"),
        ("钟离", CHAR_ZHONGLI, "天星：召唤陨石摧毁顶部3层方块"),
        ("兹白", CHAR_ZIBAI, "灵驹：每3秒抛入结晶马，落地3秒后爆炸")
    ]
    btns = []
    # 动态计算起始高度，让按钮居中
    total_h = len(chars) * 90
    start_y = cy - total_h // 2

    for i, (label, val, desc) in enumerate(chars):
        # 如果是当前选择的角色，改变背景色高亮
        bg = (100, 80, 150) if global_state['current_character'] == val else BUTTON_COLOR
        btn = Button(cx - 250, start_y + i * 90, 500, 60, label, R.font, bg_color=bg)
        # 将元数据绑定到按钮对象上，方便绘制和点击逻辑
        btn.desc = desc
        btn.char_val = val
        btns.append(btn)
    return btns


# === 其他 UI ===
slider_vol = Slider(0, 0, 300, 20, 0, 10, global_state['volume'])
btn_back_vol = Button(0, 0, 200, 50, "返回", R.font)

resolutions = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]
screen_buttons = []
btn_back_screen = Button(0, 0, 200, 50, "返回", R.font)

btn_pause = Button(20, 20, 80, 40, "暂停", R.font, bg_color=(60, 40, 30))
btn_resume = Button(0, 0, 200, 50, "继续", R.font)
btn_to_menu = Button(0, 0, 200, 50, "退出", R.font)

# 技能按钮 Rect (在 draw_game_hud 动态计算)
skill_btn_rect = pygame.Rect(0, 0, 0, 0)


def update_ui_layout():
    cx, cy = get_center()
    global menu_buttons, screen_buttons, char_buttons
    menu_buttons = create_menu_buttons()

    # 角色选择
    char_buttons = create_char_buttons()
    btn_back_char.rect.center = (cx, cy + 280)  # 调整返回按钮位置

    # 音量
    slider_vol.rect.center = (cx, cy)
    slider_vol.update_handle_pos()
    btn_back_vol.rect.center = (cx, cy + 100)

    # 分辨率
    screen_buttons = []
    start_y = cy - (len(resolutions) * 60) // 2
    for i, res in enumerate(resolutions):
        bg = (80, 100, 80) if res == global_state['screen_size'] else BUTTON_COLOR
        btn = Button(cx - 150, start_y + i * 60, 300, 50, f"{res[0]}x{res[1]}", R.font, bg_color=bg)
        screen_buttons.append((btn, res))
    btn_back_screen.rect.center = (cx, start_y + len(resolutions) * 60 + 40)

    # 暂停
    btn_resume.rect.center = (cx, cy - 30)
    btn_to_menu.rect.center = (cx, cy + 40)


update_ui_layout()


def handle_screen_change(res):
    global screen
    global_state['screen_size'] = res
    screen = pygame.display.set_mode(res, pygame.RESIZABLE)
    update_ui_layout()


def draw_background():
    if 'background' in R.images and R.images['background']:
        bg = pygame.transform.scale(R.images['background'], global_state['screen_size'])
        screen.blit(bg, (0, 0))
    else:
        screen.fill((40, 30, 25))


def draw_menu():
    draw_background()
    cx, cy = get_center()
    title = R.font.render("八奇乱斗", True, (255, 215, 0))
    screen.blit(title, title.get_rect(center=(cx - 2, cy - 152)))
    screen.blit(title, title.get_rect(center=(cx, cy - 150)))
    for btn in menu_buttons:
        btn.draw(screen)


def draw_char_select():
    draw_background()
    cx, cy = get_center()
    t = R.font.render("选择出战角色", True, WHITE)
    screen.blit(t, t.get_rect(center=(cx, cy - 250)))

    for btn in char_buttons:
        btn.draw(screen)
        # 绘制技能描述
        if btn.desc:
            desc_font = pygame.font.Font(None, 24)
            if R.font:
                desc_surf = R.font.render(btn.desc, True, (180, 180, 180))
                # 稍微缩小字体
                desc_surf = pygame.transform.scale(desc_surf, (
                    int(desc_surf.get_width() * 0.7), int(desc_surf.get_height() * 0.7)))
            else:
                desc_surf = desc_font.render(btn.desc, True, (180, 180, 180))
            screen.blit(desc_surf, desc_surf.get_rect(center=(cx, btn.rect.bottom + 15)))

    btn_back_char.draw(screen)


def draw_game_hud(screen, board_rect):
    global skill_btn_rect

    # 1. 左侧：NEXT
    cell_size = board_rect.width // GRID_WIDTH
    lantern_w = cell_size * 2.5
    lantern_h = cell_size * 4
    lantern_x = board_rect.left - lantern_w - 20
    lantern_y = board_rect.top + 50

    pygame.draw.line(screen, (139, 69, 19), (lantern_x + lantern_w // 2, board_rect.top),
                     (lantern_x + lantern_w // 2, lantern_y), 4)
    lantern_rect = pygame.Rect(lantern_x, lantern_y, lantern_w, lantern_h)
    pygame.draw.rect(screen, (240, 230, 210), lantern_rect, border_radius=10)
    pygame.draw.rect(screen, (160, 82, 45), lantern_rect, 4, border_radius=10)

    text_surf = R.font.render("NEXT", True, (100, 50, 20))
    text_surf = pygame.transform.scale(text_surf, (int(lantern_w * 0.6), int(lantern_w * 0.25)))
    screen.blit(text_surf, (lantern_x + (lantern_w - text_surf.get_width()) // 2, lantern_y + 15))

    if game.next_blocks_data:
        c1, c2 = game.next_blocks_data
        preview_size = int(cell_size * 0.9)
        p_x = lantern_x + (lantern_w - preview_size) // 2
        p_y_start = lantern_y + (lantern_h - preview_size * 2) // 2 + 10
        if R.get_block_image(c1): screen.blit(
            pygame.transform.scale(R.get_block_image(c1), (preview_size, preview_size)), (p_x, p_y_start))
        if R.get_block_image(c2): screen.blit(
            pygame.transform.scale(R.get_block_image(c2), (preview_size, preview_size)),
            (p_x, p_y_start + preview_size))

    # 2. 右侧：分数
    score_center_x = board_rect.right + 80
    score_center_y = board_rect.top + 80
    radius = 60
    pygame.draw.circle(screen, (50, 40, 40), (score_center_x, score_center_y), radius)
    pygame.draw.circle(screen, (255, 215, 0), (score_center_x, score_center_y), radius, 3)
    score_label = R.font.render("得分", True, (200, 200, 200))
    score_val = R.font.render(str(game.score), True, (255, 255, 255))
    screen.blit(score_label, score_label.get_rect(center=(score_center_x, score_center_y - 20)))
    screen.blit(score_val, score_val.get_rect(center=(score_center_x, score_center_y + 20)))

    # 3. 右侧下部：当前角色与技能按钮
    char_y_start = score_center_y + 120

    # 显示当前角色名
    char_name_map = {
        CHAR_NONE: "无角色",
        CHAR_KEQING: "刻晴",
        CHAR_GANYU: "甘雨",
        CHAR_ZHONGLI: "钟离",
        CHAR_ZIBAI: "兹白"
    }
    curr_name = char_name_map.get(global_state['current_character'], "Unknown")
    char_text = R.font.render(f"当前: {curr_name}", True, (200, 180, 255))
    char_text = pygame.transform.scale(char_text, (int(char_text.get_width() * 0.8), int(char_text.get_height() * 0.8)))
    screen.blit(char_text, char_text.get_rect(center=(score_center_x, char_y_start)))

    # 技能按钮 (如果是无角色就不画或者画灰色)
    if global_state['current_character'] != CHAR_NONE:
        btn_radius = 50
        btn_center_x = score_center_x
        btn_center_y = char_y_start + 100

        # 更新 rect 用于点击检测
        skill_btn_rect = pygame.Rect(btn_center_x - btn_radius, btn_center_y - btn_radius, btn_radius * 2,
                                     btn_radius * 2)

        # 绘制圆形按钮
        pygame.draw.circle(screen, (240, 240, 240), (btn_center_x, btn_center_y), btn_radius)
        pygame.draw.circle(screen, (100, 100, 100), (btn_center_x, btn_center_y), btn_radius, 4)

        # 绘制 "E"
        e_text = R.font.render("E", True, (50, 50, 50))
        screen.blit(e_text, e_text.get_rect(center=(btn_center_x, btn_center_y)))

        # 冷却遮罩
        progress = game.skill_manager.get_cooldown_progress(pygame.time.get_ticks())
        if progress < 1.0:
            overlay_h = int(btn_radius * 2 * (1.0 - progress))
            overlay_surf = pygame.Surface((btn_radius * 2, btn_radius * 2), pygame.SRCALPHA)
            pygame.draw.rect(overlay_surf, (0, 0, 0, 150), (0, 0, btn_radius * 2, overlay_h))

            mask_surf = pygame.Surface((btn_radius * 2, btn_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(mask_surf, (255, 255, 255, 255), (btn_radius, btn_radius), btn_radius)
            overlay_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            screen.blit(overlay_surf, (btn_center_x - btn_radius, btn_center_y - btn_radius))

            # 显示剩余时间
            rem_sec = game.skill_manager.get_remaining_seconds(pygame.time.get_ticks())
            cd_text = R.font.render(f"{rem_sec}s", True, (255, 50, 50))
            screen.blit(cd_text, cd_text.get_rect(center=(btn_center_x, btn_center_y + 20)))
    else:
        skill_btn_rect = pygame.Rect(0, 0, 0, 0)


def draw_game():
    draw_background()
    sw, sh = global_state['screen_size']
    margin_v = 40
    board_h = sh - margin_v * 2
    cell_size = board_h // GRID_HEIGHT
    board_h = cell_size * GRID_HEIGHT
    board_w = cell_size * GRID_WIDTH
    center_x = (sw - board_w) // 2
    center_y = (sh - board_h) // 2

    board_rect = renderer.draw_game_board(screen, game, center_x, center_y, board_w, board_h)
    draw_game_hud(screen, board_rect)
    btn_pause.draw(screen)

    if game.game_over_flag:
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        screen.blit(overlay, (0, 0))
        go_text = R.font.render("胜负已分", True, (220, 80, 80))
        screen.blit(go_text, go_text.get_rect(center=(sw // 2, sh // 2 - 60)))
        score_text = R.font.render(f"最终得分: {game.score}", True, WHITE)
        screen.blit(score_text, score_text.get_rect(center=(sw // 2, sh // 2 + 40)))
        hint = R.font.render("点击任意处返回菜单", True, GRAY)
        screen.blit(hint, hint.get_rect(center=(sw // 2, sh // 2 + 100)))

    elif game.paused:
        s = pygame.Surface(global_state['screen_size'], pygame.SRCALPHA)
        s.fill((0, 0, 0, 180))
        screen.blit(s, (0, 0))
        cx, cy = get_center()
        panel_rect = pygame.Rect(0, 0, 300, 250)
        panel_rect.center = (cx, cy)
        draw_panel(screen, panel_rect)
        pause_title = R.font.render("暂 停", True, (255, 255, 255))
        screen.blit(pause_title, pause_title.get_rect(center=(cx, cy - 80)))
        btn_resume.draw(screen)
        btn_to_menu.draw(screen)


# --- 主循环 ---
while True:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.VIDEORESIZE:
            handle_screen_change(event.size)

        if current_state == STATE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_buttons[0].rect.collidepoint(event.pos):
                    game.start_new_game()
                    current_state = STATE_GAME
                elif menu_buttons[1].rect.collidepoint(event.pos):
                    # 重新生成按钮以确保状态正确
                    char_buttons = create_char_buttons()
                    current_state = STATE_CHAR_SELECT
                elif menu_buttons[2].rect.collidepoint(event.pos):
                    current_state = STATE_SETTINGS_VOL
                elif menu_buttons[3].rect.collidepoint(event.pos):
                    update_ui_layout()
                    current_state = STATE_SETTINGS_SCREEN
                elif menu_buttons[4].rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
            mx, my = pygame.mouse.get_pos()
            for btn in menu_buttons: btn.hovered = btn.rect.collidepoint((mx, my))

        # 【新增】角色选择逻辑
        elif current_state == STATE_CHAR_SELECT:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn in char_buttons:
                    if btn.rect.collidepoint(event.pos):
                        global_state['current_character'] = btn.char_val
                        # 重新生成按钮以更新高亮
                        char_buttons = create_char_buttons()
                if btn_back_char.rect.collidepoint(event.pos):
                    current_state = STATE_MENU

            mx, my = pygame.mouse.get_pos()
            for btn in char_buttons: btn.hovered = btn.rect.collidepoint((mx, my))
            btn_back_char.hovered = btn_back_char.rect.collidepoint((mx, my))

        elif current_state == STATE_GAME:
            if game.game_over_flag:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    game.running = False
                    current_state = STATE_MENU
            elif not game.paused:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        new_pos = [{"color": b["color"], "x": b["x"] - 1, "y": b["y"]} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_RIGHT:
                        new_pos = [{"color": b["color"], "x": b["x"] + 1, "y": b["y"]} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_DOWN:
                        new_pos = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                        game.rotate_blocks()
                    # 【新增】E键释放技能
                    elif event.key == pygame.K_e:
                        game.skill_manager.try_trigger(game)

                # 【新增】点击技能按钮
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if skill_btn_rect.collidepoint(event.pos):
                        game.skill_manager.try_trigger(game)

            if event.type == pygame.MOUSEBUTTONDOWN and not game.game_over_flag:
                if not game.paused and btn_pause.rect.collidepoint(event.pos):
                    game.paused = True
                elif game.paused:
                    if btn_resume.rect.collidepoint(event.pos):
                        game.paused = False
                    elif btn_to_menu.rect.collidepoint(event.pos):
                        game.running = False
                        current_state = STATE_MENU

            mx, my = pygame.mouse.get_pos()
            btn_pause.hovered = btn_pause.rect.collidepoint((mx, my))
            if game.paused:
                btn_resume.hovered = btn_resume.rect.collidepoint((mx, my))
                btn_to_menu.hovered = btn_to_menu.rect.collidepoint((mx, my))

        # ... (音量和分辨率逻辑) ...
        elif current_state == STATE_SETTINGS_VOL:
            if slider_vol.handle_event(event):
                global_state['volume'] = slider_vol.val
                R.update_volume()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back_vol.rect.collidepoint(event.pos):
                    current_state = STATE_MENU
            mx, my = pygame.mouse.get_pos()
            btn_back_vol.hovered = btn_back_vol.rect.collidepoint((mx, my))

        elif current_state == STATE_SETTINGS_SCREEN:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for btn, res in screen_buttons:
                    if btn.rect.collidepoint(event.pos):
                        handle_screen_change(res)
                if btn_back_screen.rect.collidepoint(event.pos):
                    current_state = STATE_MENU
            mx, my = pygame.mouse.get_pos()
            for btn, _ in screen_buttons: btn.hovered = btn.rect.collidepoint((mx, my))
            btn_back_screen.hovered = btn_back_screen.rect.collidepoint((mx, my))

    # === 绘制 ===
    if current_state == STATE_GAME: game.update()

    if current_state == STATE_MENU:
        draw_menu()
    elif current_state == STATE_CHAR_SELECT:
        draw_char_select()
    elif current_state == STATE_GAME:
        draw_game()
    elif current_state == STATE_SETTINGS_VOL:
        draw_background()
        cx, cy = get_center()
        panel_rect = pygame.Rect(0, 0, 400, 300)
        panel_rect.center = (cx, cy)
        draw_panel(screen, panel_rect)
        t = R.font.render("音量调节", True, WHITE)
        screen.blit(t, t.get_rect(center=(cx, cy - 100)))
        slider_vol.draw(screen, R.font)
        btn_back_vol.draw(screen)
    elif current_state == STATE_SETTINGS_SCREEN:
        draw_background()
        cx, cy = get_center()
        t = R.font.render("分辨率设置", True, WHITE)
        screen.blit(t, t.get_rect(center=(cx, cy - 180)))
        for btn, _ in screen_buttons: btn.draw(screen)
        btn_back_screen.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
