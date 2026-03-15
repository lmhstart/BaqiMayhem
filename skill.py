# baqi/skill.py
import pygame
import random
from settings import *


class SkillManager:
    def __init__(self):
        self.character_name = CHAR_NONE
        self.cooldown_max = 0
        self.last_used_time = -999999  # 【修复】：初始化为一个极小值，确保开局立即可用
        self.is_ready = True
        self.cooldown_reduction = 0.0 # 0.0 - 1.0 (来自卡牌加成)

    def set_character(self, name):
        self.character_name = name
        self.last_used_time = -999999
        self.cooldown_reduction = 0.0

        if name == CHAR_KEQING: self.cooldown_max = SKILL_COOLDOWN_KEQING
        elif name == CHAR_GANYU: self.cooldown_max = SKILL_COOLDOWN_GANYU
        elif name == CHAR_ZHONGLI: self.cooldown_max = SKILL_COOLDOWN_ZHONGLI
        elif name == CHAR_ZIBAI: self.cooldown_max = SKILL_COOLDOWN_ZIBAI
        else: self.cooldown_max = 0

    def reset(self):
        self.last_used_time = -999999
        self.cooldown_reduction = 0.0

    def adjust_time(self, delta_ms):
        """修复暂停BUG：将上次使用时间向后推移，保持剩余CD不变"""
        self.last_used_time += delta_ms

    def get_effective_cooldown(self):
        return self.cooldown_max * (1.0 - self.cooldown_reduction)

    def update(self, current_time):
        if self.character_name == CHAR_NONE:
            self.is_ready = False
            return
        elapsed = current_time - self.last_used_time
        self.is_ready = (elapsed >= self.get_effective_cooldown())

    def get_cooldown_progress(self, current_time):
        if self.character_name == CHAR_NONE: return 0.0
        elapsed = current_time - self.last_used_time
        cd = self.get_effective_cooldown()
        if elapsed >= cd: return 1.0
        return elapsed / cd

    def get_remaining_seconds(self, current_time):
        elapsed = current_time - self.last_used_time
        cd = self.get_effective_cooldown()
        remain = cd - elapsed
        if remain < 0: return 0
        return int(remain / 1000)

    def try_trigger(self, game_instance):
        current_time = pygame.time.get_ticks()
        
        # 【修复】：如果技能还没冷却好，直接拒绝，不再执行错误判定
        if not self.is_ready:
            return False
        
        # 荒星破顶判定 (0305): 超过顶部使用技能判负
        if "0305" in game_instance.owned_cards:
            for x in range(GRID_WIDTH):
                if game_instance.grid[0][x]:
                    game_instance.game_over_flag = True
                    return False

        success = False
        trigger_char = self.character_name
        
        # 【修复】：处理 "0302" 随机效果，正确读取 owned_cards
        if "0302" in game_instance.owned_cards:
             pool = [CHAR_KEQING, CHAR_GANYU, CHAR_ZHONGLI, CHAR_ZIBAI] 
             trigger_char = random.choice(pool)

        if trigger_char == CHAR_KEQING:
            success = self._trigger_keqing(game_instance)
        elif trigger_char == CHAR_GANYU:
            success = self._trigger_ganyu(game_instance)
        elif trigger_char == CHAR_ZHONGLI:
            success = self._trigger_zhongli(game_instance)
        elif trigger_char == CHAR_ZIBAI:
            success = self._trigger_zibai(game_instance)

        if success:
            self.last_used_time = current_time
            self.is_ready = False
            return True
        return False

    # --- 技能具体实现 ---
    def _trigger_keqing(self, game):
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
        game.ganyu_buff_charges = 5
        game.next_blocks_data = game.generate_random_pair()
        return True

    def _trigger_zhongli(self, game):
        top_y = GRID_HEIGHT
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if game.grid[y][x] is not None:
                    top_y = y
                    break
            if top_y != GRID_HEIGHT: break
        if top_y == GRID_HEIGHT: top_y = GRID_HEIGHT - 1
        game.spawn_meteor(top_y)
        return True

    def _trigger_zibai(self, game):
        current_now = pygame.time.get_ticks()
        game.zibai_summon_queue.append(current_now + 0)
        game.zibai_summon_queue.append(current_now + 3000)
        game.zibai_summon_queue.append(current_now + 6000)
        return True

    @staticmethod
    def get_keqing_explosion_offsets():
        return [(0, -2), (-1, -1), (0, -1), (1, -1), (-2, 0), (-1, 0), (1, 0), (2, 0), (-1, 1), (0, 1), (1, 1), (0, 2)]
