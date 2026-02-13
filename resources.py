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
        self.music_path = ""
        self.font = None

    def create_placeholder_surface(self, color, size=(90, 90)):
        """防黑屏备用色块"""
        surf = pygame.Surface(size)
        surf.fill(color)
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, size[0], size[1]), 4)
        return surf

    def load_assets(self):
        # --- 1. 图片加载 ---
        # 你的图片应该都在这里了，就不动了
        img_map = {
            'blue': ((50, 100, 200), "blue_block.png"),
            'green': ((50, 200, 50), "green_block.png"),
            'purple': ((150, 50, 200), "purple_block.png"),
            'yellow': ((200, 200, 50), "yellow_block.png"),
            'stone': ((100, 100, 100), "stone.png"),
            'background': ((30, 30, 30), "background_b.png")
        }

        for key, (fallback_color, filename) in img_map.items():
            path = os.path.join(IMAGE_DIR, filename)
            try:
                if os.path.exists(path):
                    self.images[key] = pygame.image.load(path)
                else:
                    if key == 'background':
                        self.images[key] = None
                    else:
                        self.images[key] = self.create_placeholder_surface(fallback_color)
            except:
                self.images[key] = self.create_placeholder_surface(fallback_color)

        # --- 2. 【关键修复】中文字体加载 ---
        # 我们不依赖 SysFont，而是直接找字体文件
        # Windows 系统的字体通常在这里：C:\Windows\Fonts\

        # 方案A: 微软雅黑 (最推荐，清晰好看)
        font_path_msyh = "C:\\Windows\\Fonts\\msyh.ttc"
        # 方案B: 黑体 (备用)
        font_path_simhei = "C:\\Windows\\Fonts\\simhei.ttf"

        try:
            if os.path.exists(font_path_msyh):
                print(f"✅ 已加载系统字体: 微软雅黑")
                self.font = pygame.font.Font(font_path_msyh, 36)
            elif os.path.exists(font_path_simhei):
                print(f"✅ 已加载系统字体: 黑体")
                self.font = pygame.font.Font(font_path_simhei, 36)
            else:
                # 如果是 Mac 或 Linux，或者找不到上述文件，回退到默认
                # 但大概率会乱码
                print("⚠️ 未找到常用中文字体，尝试使用系统默认...")
                self.font = pygame.font.SysFont("microsoftyahei", 36)
        except Exception as e:
            print(f"字体加载出错: {e}，将使用默认字体(可能乱码)")
            self.font = pygame.font.Font(None, 36)

        # --- 3. 音乐 ---
        self.music_path = os.path.join(SOUND_DIR, "z8g15-g2l2u.wav")

    def get_block_image(self, color):
        return self.images.get(color)

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
