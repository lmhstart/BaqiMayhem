# baqi/main.py
import pygame
import sys
import ctypes
from settings import *
from resources import R
from ui import Button, Slider, draw_panel
from game_logic import Game

# --- 解决高分屏模糊问题 ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 初始化
pygame.init()
pygame.display.set_caption("八奇乱斗")

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
current_state = STATE_MENU

# 游戏实例
game = Game()


# --- UI 布局管理 ---
def get_center():
    return global_state['screen_size'][0] // 2, global_state['screen_size'][1] // 2


def create_menu_buttons():
    cx, cy = get_center()
    style_bg = (60, 40, 30)
    return [
        Button(cx - 120, cy - 60, 240, 50, "开始对局", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 10, 240, 50, "音量设置", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 80, 240, 50, "调整分辨率", R.font, bg_color=style_bg),
        Button(cx - 120, cy + 150, 240, 50, "退出游戏", R.font, bg_color=style_bg)
    ]


menu_buttons = create_menu_buttons()

# 音量设置 UI
slider_vol = Slider(0, 0, 300, 20, 0, 10, global_state['volume'])
btn_back_vol = Button(0, 0, 200, 50, "返回", R.font)

# 分辨率设置 UI
resolutions = [(1280, 720), (1600, 900), (1920, 1080), (2560, 1440)]
screen_buttons = []
btn_back_screen = Button(0, 0, 200, 50, "返回", R.font)

# 游戏内暂停 UI
btn_pause = Button(20, 20, 80, 40, "暂停", R.font, bg_color=(60, 40, 30))
btn_resume = Button(0, 0, 200, 50, "继续", R.font)
btn_to_menu = Button(0, 0, 200, 50, "认输", R.font)


def update_ui_layout():
    """响应窗口大小变化，重置所有UI位置"""
    cx, cy = get_center()

    # 主菜单
    global menu_buttons
    menu_buttons = create_menu_buttons()

    # 音量界面
    slider_vol.rect.center = (cx, cy)
    # 滑块轨道更新后，需要重新计算手柄位置
    slider_vol.update_handle_pos()
    btn_back_vol.rect.center = (cx, cy + 100)

    # 分辨率界面
    global screen_buttons
    screen_buttons = []
    start_y = cy - (len(resolutions) * 60) // 2
    for i, res in enumerate(resolutions):
        # 高亮显示当前分辨率
        bg = (80, 100, 80) if res == global_state['screen_size'] else BUTTON_COLOR
        btn = Button(cx - 150, start_y + i * 60, 300, 50, f"{res[0]}x{res[1]}", R.font, bg_color=bg)
        screen_buttons.append((btn, res))
    btn_back_screen.rect.center = (cx, start_y + len(resolutions) * 60 + 40)

    # 暂停界面
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

    # 标题
    title_text = "八奇乱斗"
    title = R.font.render(title_text, True, (255, 215, 0))
    screen.blit(title, title.get_rect(center=(cx - 2, cy - 152)))  # 阴影
    screen.blit(title, title.get_rect(center=(cx, cy - 150)))  # 本体

    for btn in menu_buttons:
        btn.draw(screen)


def draw_game():
    if 'background' in R.images and R.images['background']:
        bg = pygame.transform.scale(R.images['background'], global_state['screen_size'])
        screen.blit(bg, (0, 0))
    else:
        screen.fill((30, 30, 35))

    game.draw(screen)
    btn_pause.draw(screen)

    if game.paused:
        # 遮罩
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

        # === 状态机逻辑 ===

        # 1. 主菜单逻辑
        if current_state == STATE_MENU:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if menu_buttons[0].rect.collidepoint(event.pos):
                    game.start_new_game()
                    current_state = STATE_GAME
                elif menu_buttons[1].rect.collidepoint(event.pos):
                    current_state = STATE_SETTINGS_VOL
                elif menu_buttons[2].rect.collidepoint(event.pos):
                    # 进入前刷新一下按钮状态(高亮当前分辨率)
                    update_ui_layout()
                    current_state = STATE_SETTINGS_SCREEN
                elif menu_buttons[3].rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

            mx, my = pygame.mouse.get_pos()
            for btn in menu_buttons:
                btn.hovered = btn.rect.collidepoint((mx, my))

        # 2. 游戏内逻辑
        elif current_state == STATE_GAME:
            if not game.paused and not game.game_over_flag:
                if event.type == pygame.KEYDOWN:
                    # 移动与旋转
                    if event.key == pygame.K_LEFT:
                        new_pos = [{"color": b["color"], "x": b["x"] - 1, "y": b["y"]} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_RIGHT:
                        new_pos = [{"color": b["color"], "x": b["x"] + 1, "y": b["y"]} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_DOWN:
                        new_pos = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in game.current_blocks]
                        if not game.check_collision(new_pos): game.current_blocks = new_pos
                    elif event.key == pygame.K_SPACE:  # 空格旋转
                        game.rotate_blocks()  # 调用旋转函数
                    elif event.key == pygame.K_UP:  # 上键也旋转
                        game.rotate_blocks()

            # 鼠标点击暂停等
            if event.type == pygame.MOUSEBUTTONDOWN:
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

        # 3. 音量设置逻辑 (之前缺失的部分)
        elif current_state == STATE_SETTINGS_VOL:
            # 处理滑块拖动
            if slider_vol.handle_event(event):
                global_state['volume'] = slider_vol.val
                R.update_volume()  # 实时调整音量

            # 处理返回按钮
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_back_vol.rect.collidepoint(event.pos):
                    current_state = STATE_MENU

            mx, my = pygame.mouse.get_pos()
            btn_back_vol.hovered = btn_back_vol.rect.collidepoint((mx, my))

        # 4. 分辨率设置逻辑
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

    # === 更新与绘制 ===

    if current_state == STATE_GAME:
        game.update()

    # 绘制阶段
    if current_state == STATE_MENU:
        draw_menu()

    elif current_state == STATE_GAME:
        draw_game()

    elif current_state == STATE_SETTINGS_VOL:
        draw_background()
        # 绘制半透明面板
        cx, cy = get_center()
        panel_rect = pygame.Rect(0, 0, 400, 300)
        panel_rect.center = (cx, cy)
        draw_panel(screen, panel_rect)

        # 标题
        t = R.font.render("音量调节", True, WHITE)
        screen.blit(t, t.get_rect(center=(cx, cy - 100)))

        slider_vol.draw(screen, R.font)
        btn_back_vol.draw(screen)

    elif current_state == STATE_SETTINGS_SCREEN:
        draw_background()
        cx, cy = get_center()
        # 标题
        t = R.font.render("分辨率设置", True, WHITE)
        screen.blit(t, t.get_rect(center=(cx, cy - 180)))

        for btn, _ in screen_buttons: btn.draw(screen)
        btn_back_screen.draw(screen)

    pygame.display.flip()
    clock.tick(FPS)
