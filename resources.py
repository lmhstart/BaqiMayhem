# baqi/resources.py
import pygame
import os
import sys
from settings import *

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, 'images')
SOUND_DIR = os.path.join(BASE_DIR, 'sounds')


class ResourceManager:
    def __init__(self):
        self.images = {}
        self.explosion_anims = {}
        self.music_path = ""
        self.font = None

    def create_placeholder_surface(self, color, size=(90, 90)):
        surf = pygame.Surface(size)
        surf.fill(color)
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, size[0], size[1]), 4)
        return surf

    def create_mark_placeholder(self, size=(90, 90)):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, (150, 0, 200, 100), (0, 0, size[0], size[1]), 5)
        pygame.draw.lines(surf, (200, 200, 50), False,
                          [(size[0] * 0.6, size[1] * 0.1), (size[0] * 0.4, size[1] * 0.5),
                           (size[0] * 0.7, size[1] * 0.5), (size[0] * 0.3, size[1] * 0.9)], 3)
        return surf

    def create_meteor_placeholder(self, size=(540, 540)):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 100, 0), (size[0] // 2, size[1] // 2), size[0] // 2)
        pygame.draw.circle(surf, (100, 50, 0), (size[0] // 2, size[1] // 2), size[0] // 2 - 20, 10)
        return surf

    def load_assets(self):
        # --- 1. 图片加载 ---
        img_map = {
            'blue': ((50, 100, 200), "blue_block.png"),
            'green': ((50, 200, 50), "green_block.png"),
            'purple': ((150, 50, 200), "purple_block.png"),
            'yellow': ((200, 200, 50), "yellow_block.png"),
            'red': ((200, 50, 50), "red_block.png"),
            'stone': ((100, 100, 100), "stone.png"),
            'background': ((30, 30, 30), "background_b.png"),
            'mark_cover': (None, "mark_cover.png"),
            # 新增图片
            'meteorite': (None, "meteorite.png"),  # 钟离天星
            'bloom': ((100, 255, 200), "bloom.png")  # 兹白结晶马
        }

        for key, (fallback_color, filename) in img_map.items():
            path = os.path.join(IMAGE_DIR, filename)
            try:
                if os.path.exists(path):
                    self.images[key] = pygame.image.load(path)
                else:
                    if key == 'background':
                        self.images[key] = None
                    elif key == 'mark_cover':
                        self.images[key] = self.create_mark_placeholder()
                    elif key == 'meteorite':
                        self.images[key] = self.create_meteor_placeholder()
                    elif key == 'bloom':
                        self.images[key] = self.create_placeholder_surface(fallback_color)
                    else:
                        self.images[key] = self.create_placeholder_surface(fallback_color)
            except:
                if key == 'meteorite':
                    self.images[key] = self.create_meteor_placeholder()
                elif key == 'bloom':
                    self.images[key] = self.create_placeholder_surface(fallback_color)
                else:
                    self.images[key] = self.create_placeholder_surface(fallback_color)

        # --- 2. 加载爆炸动画 ---
        # 增加 'bloom' 到加载列表
        colors_to_load = ['blue', 'green', 'purple', 'yellow', 'red', 'stone', 'bloom']

        for color in colors_to_load:
            frames = []
            folder_name = f"explosion_{color}"
            folder_path = os.path.join(IMAGE_DIR, folder_name)

            if os.path.exists(folder_path):
                # 兹白的动画有25帧，其他假设20帧
                max_frame = 25 if color == 'bloom' else 20
                for i in range(1, max_frame + 1):
                    file_name = f"{color}_explosion_{i:04d}.png"
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.exists(file_path):
                        try:
                            frames.append(pygame.image.load(file_path))
                        except:
                            pass
                    else:
                        break

            if frames:
                self.explosion_anims[color] = frames
            else:
                self.explosion_anims[color] = []

        # --- 3. 字体与音乐 ---
        font_path_msyh = "C:\\Windows\\Fonts\\msyh.ttc"
        try:
            if os.path.exists(font_path_msyh):
                self.font = pygame.font.Font(font_path_msyh, 36)
            else:
                self.font = pygame.font.SysFont("microsoftyahei", 36)
        except:
            self.font = pygame.font.Font(None, 36)
        self.music_path = os.path.join(SOUND_DIR, "z8g15-g2l2u.wav")

    def get_block_image(self, color):
        return self.images.get(color)

    def get_explosion_frames(self, color):
        return self.explosion_anims.get(color, [])

    def play_music(self):
        if not os.path.exists(self.music_path): return
        try:
            pygame.mixer.music.load(self.music_path)
            self.update_volume()
            pygame.mixer.music.play(-1)
        except:
            pass

    def update_volume(self):
        if pygame.mixer.get_init():
            vol = global_state['volume'] / 10.0
            pygame.mixer.music.set_volume(vol)


R = ResourceManager()
