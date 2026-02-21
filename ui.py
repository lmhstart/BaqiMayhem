# baqi/ui.py
import pygame
from settings import *


def draw_panel(screen, rect, color=PANEL_BG, border_radius=15):
    """绘制半透明圆角面板"""
    # 创建一个支持Alpha通道的Surface
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, color, s.get_rect(), border_radius=border_radius)
    # 绘制边框
    pygame.draw.rect(s, (255, 255, 255, 30), s.get_rect(), 2, border_radius=border_radius)
    screen.blit(s, (rect.x, rect.y))


class Button:
    def __init__(self, x, y, w, h, text, font, action=None, bg_color=BUTTON_COLOR):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.action = action
        self.hovered = False
        self.bg_color = bg_color

    def draw(self, screen):
        # 悬停变色效果
        current_color = BUTTON_HOVER if self.hovered else self.bg_color

        # 绘制圆角按钮
        pygame.draw.rect(screen, current_color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2, border_radius=10)  # 边框

        # 绘制文字（居中）
        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.hovered and self.action:
                self.action()


class Slider:
    def __init__(self, x, y, w, h, min_val, max_val, current_val):
        self.rect = pygame.Rect(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.val = current_val
        self.dragging = False
        self.handle_rect = pygame.Rect(0, y - 5, 20, h + 10)
        self.update_handle_pos()

    def update_handle_pos(self):
        ratio = (self.val - self.min_val) / (self.max_val - self.min_val)
        self.handle_rect.centerx = self.rect.x + self.rect.width * ratio

    def draw(self, screen, font):
        # 轨道
        pygame.draw.rect(screen, (100, 100, 100), self.rect, border_radius=5)
        # 已选区域高亮
        fill_rect = pygame.Rect(self.rect.x, self.rect.y, self.handle_rect.centerx - self.rect.x, self.rect.height)
        pygame.draw.rect(screen, HIGHLIGHT, fill_rect, border_radius=5)

        # 滑块
        pygame.draw.rect(screen, WHITE, self.handle_rect, border_radius=5)

        # 文字显示数值
        text = font.render(f"音量: {int(self.val)}", True, WHITE)
        screen.blit(text, (self.rect.x, self.rect.y - 35))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val_from_pos(event.pos[0])
                return True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val_from_pos(event.pos[0])
                return True
        return False

    def update_val_from_pos(self, x):
        x = max(self.rect.x, min(x, self.rect.right))
        ratio = (x - self.rect.x) / self.rect.width
        self.val = round(self.min_val + ratio * (self.max_val - self.min_val))
        self.update_handle_pos()
