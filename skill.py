# baqi/skill.py
import pygame
import random
from settings import *


class SkillManager:
    def __init__(self):
        self.character_name = CHAR_NONE
        self.cooldown_max = 0
        self.last_used_time = 0
        self.is_ready = True

    def set_character(self, name):
        self.character_name = name
        self.last_used_time = -999999  # 确保开局可用

        if name == CHAR_KEQING:
            self.cooldown_max = SKILL_COOLDOWN_KEQING
        elif name == CHAR_GANYU:
            self.cooldown_max = SKILL_COOLDOWN_GANYU
        elif name == CHAR_ZHONGLI:
            self.cooldown_max = SKILL_COOLDOWN_ZHONGLI
        elif name == CHAR_ZIBAI:
            self.cooldown_max = SKILL_COOLDOWN_ZIBAI
        else:
            self.cooldown_max = 0

    def reset(self):
        self.last_used_time = -self.cooldown_max

    def update(self, current_time):
        if self.character_name == CHAR_NONE:
            self.is_ready = False
            return
        elapsed = current_time - self.last_used_time
        self.is_ready = (elapsed >= self.cooldown_max)

    def get_cooldown_progress(self, current_time):
        if self.character_name == CHAR_NONE: return 0.0
        elapsed = current_time - self.last_used_time
        if elapsed >= self.cooldown_max: return 1.0
        return elapsed / self.cooldown_max

    def get_remaining_seconds(self, current_time):
        elapsed = current_time - self.last_used_time
        remain = self.cooldown_max - elapsed
        if remain < 0: return 0
        return int(remain / 1000)

    def try_trigger(self, game_instance):
        current_time = pygame.time.get_ticks()
        if not self.is_ready:
            return False

        success = False
        if self.character_name == CHAR_KEQING:
            success = self._trigger_keqing(game_instance)
        elif self.character_name == CHAR_GANYU:
            success = self._trigger_ganyu(game_instance)
        elif self.character_name == CHAR_ZHONGLI:
            success = self._trigger_zhongli(game_instance)
        elif self.character_name == CHAR_ZIBAI:
            success = self._trigger_zibai(game_instance)

        if success:
            self.last_used_time = current_time
            self.is_ready = False
            return True
        return False

    # --- 技能具体实现 ---

    def _trigger_keqing(self, game):
        """刻晴：标记两个方块"""
        candidates = []
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                block = game.grid[y][x]
                if block and block != "stone" and block != "bloom" and not game.marks[y][x]:
                    candidates.append((y, x))

        if not candidates: return False
        count = min(len(candidates), 2)
        targets = random.sample(candidates, count)
        for (y, x) in targets: game.marks[y][x] = True
        return True

    def _trigger_ganyu(self, game):
        """甘雨：接下来5组方块为同色"""
        # 激活Buff
        game.ganyu_buff_charges = 5
        # 立即刷新当前的 NEXT 预览（可选，为了视觉反馈更好，重新生成next）
        game.next_blocks_data = game.generate_random_pair()
        return True

    def _trigger_zhongli(self, game):
        """钟离：召唤天星"""
        # 找到最高的方块行
        top_y = GRID_HEIGHT
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if game.grid[y][x] is not None:
                    top_y = y
                    break
            if top_y != GRID_HEIGHT: break

        # 即使棋盘是空的，也可以砸最下面
        if top_y == GRID_HEIGHT: top_y = GRID_HEIGHT - 1

        # 在游戏中生成陨石对象
        game.spawn_meteor(top_y)
        return True

    def _trigger_zibai(self, game):
        """兹白：每3秒抛入一只结晶马，共抛3次"""
        current_now = pygame.time.get_ticks()
        # 将3个生成事件加入队列：现在，+3秒，+6秒
        game.zibai_summon_queue.append(current_now + 0)
        game.zibai_summon_queue.append(current_now + 3000)
        game.zibai_summon_queue.append(current_now + 6000)
        return True

    @staticmethod
    def get_keqing_explosion_offsets():
        return [(0, -2), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)]
