# baqi/resources.py
import pygame
import os
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
        self.font_sm = None       # 小字体
        self.font_lg = None       # 大字体
        self._scale_cache = {}    # 【性能优化】缩放图片缓存，避免每帧重复缩放

    # --- 占位图生成 ---
    def _placeholder(self, color, size=(90, 90)):
        surf = pygame.Surface(size)
        surf.fill(color)
        pygame.draw.rect(surf, (255, 255, 255), (0, 0, size[0], size[1]), 4)
        return surf

    def _placeholder_alpha(self, color, size=(90, 90)):
        surf = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surf, color, (0, 0, size[0], size[1]), 5)
        return surf

    # --- 缩放缓存 API ---
    def get_scaled_block(self, color, size):
        """获取已缓存的方块图片（避免每帧 transform.scale）"""
        key = (color, size)
        if key not in self._scale_cache:
            img = self.get_block_image(color)
            self._scale_cache[key] = pygame.transform.scale(img, (size, size)) if img else None
        return self._scale_cache[key]

    def get_scaled(self, img_key, w, h):
        """通用缩放缓存"""
        key = (img_key, w, h)
        if key not in self._scale_cache:
            img = self.images.get(img_key)
            self._scale_cache[key] = pygame.transform.scale(img, (w, h)) if img else None
        return self._scale_cache[key]

    def clear_scale_cache(self):
        """窗口大小改变时调用，清除缓存"""
        self._scale_cache = {}

    def load_assets(self):
        img_map = {
            'blue':       ((50, 100, 200),  "blue_block.png"),
            'green':      ((50, 200, 50),   "green_block.png"),
            'purple':     ((150, 50, 200),  "purple_block.png"),
            'yellow':     ((200, 200, 50),  "yellow_block.png"),
            'red':        ((200, 50, 50),   "red_block.png"),
            'stone':      ((100, 100, 100), "stone.png"),
            'background': ((30, 30, 30),    "background_b.png"),
            'mark_cover': (None,            "mark_cover.png"),
            'meteorite':  (None,            "meteorite.png"),
            'bloom':      ((100, 255, 200), "bloom.png"),
            'sword':      ((100, 200, 255), "sword.png"),
            'smoke':      ((100, 100, 100), "smoke.png"),
            'mint':       ((0, 255, 0),     "mint_cover.png"),
        }
        for key, (fallback, filename) in img_map.items():
            path = os.path.join(IMAGE_DIR, filename)
            try:
                if os.path.exists(path):
                    self.images[key] = pygame.image.load(path)
                elif key == 'meteorite':
                    surf = pygame.Surface((540, 540), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (255, 100, 0), (270, 270), 270)
                    self.images[key] = surf
                elif key == 'mark_cover':
                    self.images[key] = self._placeholder_alpha((150, 0, 200, 100))
                elif fallback:
                    self.images[key] = self._placeholder(fallback)
            except Exception:
                if fallback:
                    self.images[key] = self._placeholder(fallback)

        # 卡牌图片
        cards_dir = os.path.join(IMAGE_DIR, 'cards')
        card_ids = [f"{a:02d}{b:02d}" for a in range(1, 4) for b in range(1, 16)]
        for cid in card_ids:
            fp = os.path.join(cards_dir, f"{cid}.png")
            if os.path.exists(fp):
                try:
                    self.images[f"card_{cid}"] = pygame.image.load(fp)
                except Exception:
                    pass

        # 爆炸动画
        for color in ['blue', 'green', 'purple', 'yellow', 'red', 'stone', 'bloom']:
            frames = []
            folder = os.path.join(IMAGE_DIR, f"explosion_{color}")
            if os.path.exists(folder):
                max_f = 25 if color == 'bloom' else 20
                for i in range(1, max_f + 1):
                    fp = os.path.join(folder, f"{color}_explosion_{i:04d}.png")
                    if os.path.exists(fp):
                        try: frames.append(pygame.image.load(fp))
                        except: break
                    else: break
            self.explosion_anims[color] = frames

        # 字体（三个大小）
        font_path = "C:\\Windows\\Fonts\\msyh.ttc"
        def make_font(size):
            try:
                if os.path.exists(font_path): return pygame.font.Font(font_path, size)
                return pygame.font.SysFont("microsoftyahei", size)
            except: return pygame.font.Font(None, size)

        self.font    = make_font(36)
        self.font_sm = make_font(24)
        self.font_lg = make_font(52)

        self.music_path = os.path.join(SOUND_DIR, "z8g15-g2l2u.wav")

    def get_block_image(self, color): return self.images.get(color)
    def get_card_image(self, cid):    return self.images.get(f'card_{cid}')
    def get_explosion_frames(self, color): return self.explosion_anims.get(color, [])

    def play_music(self):
        if not os.path.exists(self.music_path): return
        try:
            pygame.mixer.music.load(self.music_path)
            self.update_volume()
            pygame.mixer.music.play(-1)
        except: pass

    def update_volume(self):
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(global_state['volume'] / 10.0)

R = ResourceManager()