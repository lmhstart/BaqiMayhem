# baqi/game_logic.py
import pygame
import random
from settings import *
from effects import Explosion, FallingAnim, MeteoriteAnim, SwordAnim, FloatingText
from skill import SkillManager
from cards import CardManager, ALL_CARDS

# ── 状态机延迟 (ms) ────────────────────────────────────────────
DELAY_PRE_CLEAR  = 50   # ← [可调] 消除前高亮停顿时间
DELAY_POST_FALL  = 50   # ← [可调] 下落完成后等待时间


class EffectsManager:
    def __init__(self):
        self.falling_anims  = []
        self.explosions     = []
        self.meteor         = None
        self.swords         = []
        self.floating_texts = []

    def clear(self):
        self.falling_anims  = []
        self.explosions     = []
        self.meteor         = None
        self.swords         = []
        self.floating_texts = []

    def update(self, current_time):
        for e  in self.explosions:      e.update(current_time)
        for a  in self.falling_anims:   a.update()
        for s  in self.swords:          s.update()
        for ft in self.floating_texts:  ft.update(current_time)

        self.explosions     = [e  for e  in self.explosions     if not e.finished]
        self.falling_anims  = [a  for a  in self.falling_anims  if not a.finished]
        self.swords         = [s  for s  in self.swords         if not s.finished]
        self.floating_texts = [ft for ft in self.floating_texts if not ft.finished]

        return len(self.falling_anims) == 0


class Game:
    def __init__(self):
        self._init_grids()
        self.score             = 0
        self.card_draw_index   = 0   # 【新增】记录当前非线性抽卡进行到了第几个阶段
        self.current_blocks    = []
        self.next_blocks_data  = []
        self.running           = False
        self.paused            = False
        self.pause_start_time  = 0
        self.card_select_start_time = 0
        self.game_over_flag    = False
        self.internal_state    = STATE_PLAYING
        self._pre_card_state   = STATE_PLAYING
        self.state_timer       = 0
        self.elimination_list  = []
        self.effects_manager   = EffectsManager()
        self.skill_manager     = SkillManager()
        self.card_manager      = CardManager()
        self.normal_drop_interval = NORMAL_DROP_INTERVAL  
        self.last_drop_time    = 0
        self.next_stone_time   = 0
        self.last_update_time  = 0
        self.ganyu_buff_charges= 0
        self.zibai_summon_queue= []
        self.owned_cards       = []
        self.active_buffs      = {}
        self.current_card_choices = []
        self.card_rects        = []
        self.reroll_rect       = None
        self.skip_rect         = None  
        self._reset_modifiers()
        self.combo_count       = 0
        self.last_score_added  = 0

    def _init_grids(self):
        self.grid         = [[None  for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.marks        = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.bloom_timers = [[0     for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.smoke_mask   = [[0     for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.mint_mask    = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    def _reset_modifiers(self):
        self.score_multiplier         = 1.0
        self.stone_interval_multiplier= 1.0
        self.color_reduce_charges     = 0
        self.same_color_prob_boost    = False
        self.grid_height_limit        = GRID_HEIGHT
        self.ignore_top_limit         = False
        self.disable_down_key         = False
        self.q_skill_id               = None
        self.q_skill_cooldown         = 0
        # 【修复】：初始化为极小值，避免开局刚抽到技能就被误判还在冷却
        self.q_skill_last_used        = -999999  
        self.q_skill_ready            = False
        self.shield_active_timer      = 0
        self.zibai_pause_timer        = 0

    def start_new_game(self):
        self._init_grids()
        self.score            = 0
        self.card_draw_index  = 0   # 重置抽卡阶段
        self.paused           = False
        self.game_over_flag   = False
        self.running          = True
        self.internal_state   = STATE_PLAYING
        self._pre_card_state  = STATE_PLAYING
        self.card_select_start_time = 0
        self.effects_manager.clear()
        self.elimination_list = []
        self.ganyu_buff_charges= 0
        self.zibai_summon_queue= []
        self.owned_cards      = []
        self.active_buffs     = {}
        self.combo_count      = 0
        self.last_score_added = 0
        self._reset_modifiers()
        self.skill_manager.set_character(global_state['current_character'])
        self.skill_manager.reset()
        self.next_blocks_data = self.generate_random_pair()
        self.current_blocks   = self.spawn_new_blocks_from_next()
        now = pygame.time.get_ticks()
        self.last_drop_time   = now
        self.next_stone_time  = now + STONE_INITIAL_DELAY  
        self.last_update_time = now

    def toggle_pause(self):
        if self.paused:
            self._apply_time_correction(pygame.time.get_ticks() - self.pause_start_time)
            self.paused = False
        else:
            self.paused = True
            self.pause_start_time = pygame.time.get_ticks()

    def resume_from_card_select(self):
        duration = pygame.time.get_ticks() - self.card_select_start_time
        if duration > 0:
            self._apply_time_correction(duration)
        prev = self._pre_card_state
        if prev == STATE_SELECT_CARD:
            prev = STATE_PLAYING
        self.internal_state = prev
        if self.internal_state == STATE_PLAYING and not self.current_blocks and not self.game_over_flag:
            self.current_blocks = self.spawn_new_blocks_from_next()

    def _apply_time_correction(self, duration):
        self.last_drop_time    += duration
        self.next_stone_time   += duration
        self.last_update_time  += duration
        self.q_skill_last_used += duration
        self.skill_manager.adjust_time(duration)
        for i in range(len(self.zibai_summon_queue)):
            self.zibai_summon_queue[i] += duration

    # ─── 方块生成 ────────────────────────────────────────────────────────

    def generate_random_pair(self):
        colors = ["blue", "green", "purple", "yellow", "red"]
        if self.color_reduce_charges > 0:
            colors = [c for c in colors if c != "red"]
            self.color_reduce_charges -= 1
        if self.ganyu_buff_charges > 0:
            self.ganyu_buff_charges -= 1
            c = random.choice(colors)
            return [c, c]
        c1 = random.choice(colors)
        c2 = c1 if (self.same_color_prob_boost and random.random() < 0.5) else random.choice(colors)
        return [c1, c2]

    def spawn_new_blocks_from_next(self):
        if not self.next_blocks_data:
            self.next_blocks_data = self.generate_random_pair()
        c1, c2 = self.next_blocks_data
        self.next_blocks_data = self.generate_random_pair()
        x = GRID_WIDTH // 2 - 1
        if self.grid[0][x] or self.grid[1][x]:
            if not self.ignore_top_limit:
                self.game_over_flag = True
            return []
        limit_y = GRID_HEIGHT - self.grid_height_limit
        if 0 < limit_y < GRID_HEIGHT:
            for cx in range(GRID_WIDTH):
                if self.grid[limit_y][cx]:
                    self.game_over_flag = True
                    break
        return [{"color": c1, "x": x, "y": 0}, {"color": c2, "x": x, "y": 1}]

    def spawn_stones(self):
        if self.zibai_pause_timer > 0 or self.shield_active_timer > 0:
            return
        occupied = {b["x"] for b in self.current_blocks}
        available = [x for x in range(GRID_WIDTH) if x not in occupied]
        if len(available) < 2:
            available = list(range(GRID_WIDTH))
        cols = random.sample(available, min(2, len(available)))
        spawned = False
        for x in cols:
            if self.grid[0][x] is None:
                self.grid[0][x] = "stone"
                self.marks[0][x] = False
                spawned = True
        if spawned and self.internal_state == STATE_PLAYING:
            self.resolve_grid_stability()

    def spawn_meteor(self, target_y):
        board_h = (global_state['screen_size'][1] - 80) // GRID_HEIGHT * GRID_HEIGHT
        self.effects_manager.meteor = MeteoriteAnim(target_y, board_h)

    def get_rain_cutter_targets(self):
        board_h = (global_state['screen_size'][1] - 80) // GRID_HEIGHT * GRID_HEIGHT
        self.effects_manager.swords.append(SwordAnim(0, board_h))
        self.effects_manager.swords.append(SwordAnim(GRID_WIDTH - 1, board_h))
        targets = set()
        for x in [0, GRID_WIDTH - 1]:
            for y in range(GRID_HEIGHT):
                if self.grid[y][x]:
                    targets.add((y, x))
        return targets

    # ─── 玩家操作 ─────────────────────────────────────────────────────────

    def check_collision(self, blocks):
        for b in blocks:
            if b["x"] < 0 or b["x"] >= GRID_WIDTH or b["y"] >= GRID_HEIGHT:
                return True
            if b["y"] >= 0 and self.grid[b["y"]][b["x"]]:
                return True
        return False

    def rotate_blocks(self):
        if not self.current_blocks:
            return
        pivot = self.current_blocks[0]
        new_blocks = [{"color": b["color"],
                       "x": pivot["x"] - (b["y"] - pivot["y"]),
                       "y": pivot["y"] + (b["x"] - pivot["x"])}
                      for b in self.current_blocks]
        if not self.check_collision(new_blocks):
            self.current_blocks = new_blocks

    def hard_drop(self):
        if not self.current_blocks:
            return
        blocks = self.current_blocks
        while True:
            below = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in blocks]
            if self.check_collision(below):
                break
            blocks = below
        self.current_blocks = blocks
        self.place_blocks()

    def get_ghost_blocks(self):
        if not self.current_blocks:
            return []
        ghost = list(self.current_blocks)
        while True:
            below = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in ghost]
            if self.check_collision(below):
                break
            ghost = below
        return ghost

    def place_blocks(self):
        if any(b["y"] < 0 for b in self.current_blocks) and not self.ignore_top_limit:
            self.game_over_flag = True
            self.current_blocks = []
            return
        for b in self.current_blocks:
            if b["y"] >= 0 and self.grid[b["y"]][b["x"]] is None:
                self.grid[b["y"]][b["x"]] = b["color"]
                self.marks[b["y"]][b["x"]] = False
                self.bloom_timers[b["y"]][b["x"]] = 0
                if "0303" in self.owned_cards and random.random() < 0.2:
                    self.mint_mask[b["y"]][b["x"]] = True
        self.current_blocks = []
        self.resolve_grid_stability()

    # ─── 消除逻辑 ─────────────────────────────────────────────────────────

    def check_elimination_conditions(self):
        visited      = [[False] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        to_eliminate = set()

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell = self.grid[y][x]
                if not cell or cell in ("stone", "bloom") or visited[y][x]:
                    continue
                stack, group = [(y, x)], set()
                while stack:
                    cy, cx = stack.pop()
                    if (cy, cx) in group:
                        continue
                    group.add((cy, cx))
                    visited[cy][cx] = True
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx] == cell:
                            stack.append((ny, nx))

                if len(group) < 4:      
                    continue

                to_eliminate.update(group)
                self.combo_count = len(group) // 4  

                if "0110" in self.owned_cards:
                    if self.combo_count >= 3:
                        self.skill_manager.last_used_time = -999999
                        self.q_skill_last_used = -999999
                    elif self.combo_count >= 2:
                        e_cd = self.skill_manager.get_effective_cooldown()
                        self.skill_manager.last_used_time -= e_cd * 0.2   
                        self.q_skill_last_used -= 60000 * 0.2

                if "0113" in self.owned_cards:
                    max_h = max((GRID_HEIGHT - y for y in range(GRID_HEIGHT)
                                 for x in range(GRID_WIDTH) if self.grid[y][x]), default=0)
                    if random.random() < max_h * 0.03:  
                        to_eliminate.update(self.get_rain_cutter_targets())

                if "0202" in self.owned_cards:
                    for (gy, gx) in group:
                        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                            ny, nx = gy + dy, gx + dx
                            if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx]:
                                to_eliminate.add((ny, nx))

                if "0301" in self.owned_cards:
                    for (gy, gx) in group:
                        for dy in range(-1, 2):
                            for dx in range(-1, 2):
                                ny, nx = gy + dy, gx + dx
                                if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx]:
                                    to_eliminate.add((ny, nx))

                for (gy, gx) in group:
                    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        ny, nx = gy + dy, gx + dx
                        if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx] == "stone":
                            to_eliminate.add((ny, nx))
                    if self.marks[gy][gx]:
                        for ody, odx in SkillManager.get_keqing_explosion_offsets():
                            ny, nx = gy + ody, gx + odx
                            if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx]:
                                to_eliminate.add((ny, nx))
                        self.marks[gy][gx] = False

        if to_eliminate:
            existing = set(self.elimination_list)
            existing.update(to_eliminate)
            self.elimination_list = list(existing)
            return True
        return False

    def execute_elimination_and_explode(self):
        stone_count = normal_count = 0
        mint_triggered = False
        sum_x = sum_y = 0

        if "0101" in self.owned_cards and "0101_cd" not in self.active_buffs:
            self.active_buffs["0101_cd"] = {"timer": 0}
            e_cd = self.skill_manager.get_effective_cooldown()
            self.skill_manager.last_used_time -= e_cd * 0.2    

        for (y, x) in self.elimination_list:
            color = self.grid[y][x]
            if not color:
                continue
            if color == "stone":    stone_count += 1
            elif color != "bloom":  normal_count += 1
            if self.mint_mask[y][x]:
                mint_triggered = True
                self.mint_mask[y][x] = False
            self.effects_manager.explosions.append(Explosion(x, y, color))
            self.grid[y][x]         = None
            self.marks[y][x]        = False
            self.bloom_timers[y][x] = 0
            self.smoke_mask[y][x]   = 0
            sum_x += x
            sum_y += y

        n      = len(self.elimination_list)
        cx_avg = sum_x / n if n else GRID_WIDTH  // 2
        cy_avg = sum_y / n if n else GRID_HEIGHT // 2

        points = (normal_count * SCORE_PER_BLOCK +  
                  stone_count  * STONE_BONUS)        
        if mint_triggered:
            points += 500                            
            self.skill_manager.last_used_time -= self.skill_manager.get_effective_cooldown() * 0.3

        points = int(points * self.score_multiplier)
        self.score           += points
        self.last_score_added = points

        if points > 0:
            self._spawn_float_text_grid(
                f"+{points}", cx_avg, cy_avg,
                color=(255, 215, 0) if points < 200 else (255, 100, 50),
                scale=1.0 if points < 200 else 1.4)
        if self.combo_count >= 2:
            self._spawn_float_text_grid(
                f"{self.combo_count}连消！", cx_avg, cy_avg - 1.5,
                color=(100, 220, 255), scale=1.1)

        self.elimination_list = []
        self.internal_state   = STATE_EXPLODING

        if "0112_trigger" in self.active_buffs:
            for r in range(GRID_HEIGHT - 3, GRID_HEIGHT):   
                for c in range(GRID_WIDTH):
                    if not self.grid[r][c]:
                        self.grid[r][c] = "stone"
            del self.active_buffs["0112_trigger"]

    def _spawn_float_text_grid(self, text, grid_cx, grid_cy, color, scale=1.0):
        sw, sh       = global_state['screen_size']
        board_h_px   = (sh - 80) // GRID_HEIGHT * GRID_HEIGHT
        cell_size    = board_h_px // GRID_HEIGHT
        board_w_px   = cell_size * GRID_WIDTH
        offset_x     = (sw - board_w_px) // 2
        offset_y     = (sh - board_h_px) // 2
        px = offset_x + grid_cx * cell_size + cell_size // 2
        py = offset_y + grid_cy * cell_size
        self.effects_manager.floating_texts.append(
            FloatingText(text, px, py, color, scale))

    # ─── 物理 & 状态机 ────────────────────────────────────────────────────

    def setup_falling_animations(self):
        new_grid   = [[None  for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_marks  = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_timers = [[0     for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_smoke  = [[0     for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_mint   = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.effects_manager.falling_anims = []
        has_falling = False

        for x in range(GRID_WIDTH):
            write_y = GRID_HEIGHT - 1
            for read_y in range(GRID_HEIGHT - 1, -1, -1):
                color = self.grid[read_y][x]
                if not color:
                    continue
                new_grid[write_y][x]   = color
                new_marks[write_y][x]  = self.marks[read_y][x]
                new_smoke[write_y][x]  = self.smoke_mask[read_y][x]
                new_mint[write_y][x]   = self.mint_mask[read_y][x]
                new_timers[write_y][x] = (self.bloom_timers[read_y][x]
                                          if read_y == write_y else 0)
                if read_y != write_y:
                    has_falling = True
                    self.effects_manager.falling_anims.append(
                        FallingAnim(x, read_y, write_y, color))
                write_y -= 1

        self.grid         = new_grid
        self.marks        = new_marks
        self.bloom_timers = new_timers
        self.smoke_mask   = new_smoke
        self.mint_mask    = new_mint
        return has_falling

    def resolve_grid_stability(self):
        if self.setup_falling_animations():
            self.internal_state = STATE_ANIMATING
            if self.check_collision(self.current_blocks):
                test = [{"color": b["color"], "x": b["x"], "y": b["y"] - 1}
                        for b in self.current_blocks]
                if not self.check_collision(test):
                    self.current_blocks = test
            return
        if self.check_elimination_conditions():
            self.internal_state = STATE_PRE_CLEAR
            self.state_timer    = pygame.time.get_ticks()
            return
        self.internal_state = STATE_PLAYING
        if not self.current_blocks and not self.game_over_flag:
            self.current_blocks = self.spawn_new_blocks_from_next()

    # ─── Q 技能 ──────────────────────────────────────────────────────────

    def try_use_q_skill(self):
        if not self.q_skill_id or not self.q_skill_ready:
            return
        current_time = pygame.time.get_ticks()
        if current_time - self.q_skill_last_used < 60000:   
            return
            
        used = False
        if self.q_skill_id == "0111":
            self.zibai_pause_timer = 20000  
            used = True
        elif self.q_skill_id == "0112":
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if self.grid[y][x]:
                        self.elimination_list.append((y, x))
            self.active_buffs["0112_trigger"] = {"count": 3}
            used = True
            self.current_blocks = []
        elif self.q_skill_id == "0114":
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if self.grid[y][x] == "stone":
                        self.elimination_list.append((y, x))
            self.shield_active_timer = 20000    
            used = True
            self.current_blocks = []
            
        if used:
            self.q_skill_last_used = current_time
            if self.elimination_list:
                self.internal_state = STATE_PRE_CLEAR
                self.state_timer    = current_time
            else:
                self.resolve_grid_stability()

    # ─── 兹白/结晶马 ─────────────────────────────────────────────────────

    def process_zibai_queue(self, current_time):
        remaining = []
        for t in self.zibai_summon_queue:
            if current_time >= t:
                self.spawn_bloom_block()
            else:
                remaining.append(t)
        self.zibai_summon_queue = remaining

    def spawn_bloom_block(self):
        occupied = {b["x"] for b in self.current_blocks}
        available = [x for x in range(GRID_WIDTH) if x not in occupied]
        if not available:
            available = list(range(GRID_WIDTH))
        random.shuffle(available)
        for x in available:
            if self.grid[0][x] is None:
                self.grid[0][x] = "bloom"
                self.marks[0][x] = False
                if self.internal_state == STATE_PLAYING:
                    self.resolve_grid_stability()
                return

    # ─── Buff 计时器 ─────────────────────────────────────────────────────

    def update_buffs_and_timers(self, dt, current_time):
        if self.internal_state == STATE_PLAYING:
            to_explode = set()
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if self.grid[y][x] == "bloom":
                        if y == GRID_HEIGHT - 1 or self.grid[y + 1][x] is not None:
                            self.bloom_timers[y][x] += dt
                            if self.bloom_timers[y][x] >= 3000:     
                                to_explode.add((y, x))
                                for dy, dx in ((0,1),(0,-1),(1,0),(-1,0)):
                                    ny, nx = y+dy, x+dx
                                    if 0<=ny<GRID_HEIGHT and 0<=nx<GRID_WIDTH and self.grid[ny][nx]:
                                        to_explode.add((ny, nx))
            if to_explode:
                existing = set(self.elimination_list)
                existing.update(to_explode)
                self.elimination_list = list(existing)
                self.internal_state   = STATE_PRE_CLEAR
                self.state_timer      = current_time - DELAY_PRE_CLEAR + 10

        if self.zibai_pause_timer   > 0: self.zibai_pause_timer   -= dt
        if self.shield_active_timer > 0: self.shield_active_timer -= dt

        if "0101_cd" in self.active_buffs:
            self.active_buffs["0101_cd"]["timer"] += dt
            if self.active_buffs["0101_cd"]["timer"] >= 10000:  
                del self.active_buffs["0101_cd"]

        colors_map = {
            "0105": "red",
            "0106": "blue",
            "0107": "purple",
            "0108": "green",
            "0109": "yellow",
        }
        for cid, target_color in colors_map.items():
            if cid not in self.owned_cards:
                continue
            if cid not in self.active_buffs:
                self.active_buffs[cid] = {"timer": 0}
            self.active_buffs[cid]["timer"] += dt
            if self.active_buffs[cid]["timer"] >= 60000:    
                self.active_buffs[cid]["timer"] = 0
                for y in range(GRID_HEIGHT):
                    for x in range(GRID_WIDTH):
                        if self.grid[y][x] == target_color:
                            self.elimination_list.append((y, x))
                if self.elimination_list:
                    self.internal_state = STATE_PRE_CLEAR
                    self.state_timer    = current_time

        if "0203" in self.owned_cards:
            if "0203" not in self.active_buffs:
                self.active_buffs["0203"] = {"timer": 0}
            self.active_buffs["0203"]["timer"] += dt
            if self.active_buffs["0203"]["timer"] >= 30000:     
                self.active_buffs["0203"]["timer"] = 0
                targets = [(y, x) for y in range(GRID_HEIGHT)
                           for x in range(GRID_WIDTH) if self.grid[y][x]]
                for (y, x) in random.sample(targets, min(len(targets), 5)):
                    self.smoke_mask[y][x] = 40000               
            for y in range(GRID_HEIGHT):
                for x in range(GRID_WIDTH):
                    if self.smoke_mask[y][x] > 0:
                        self.smoke_mask[y][x] -= dt

        if "0304" in self.owned_cards:
            if "0304" not in self.active_buffs:
                self.active_buffs["0304"] = {"timer": 0}
            self.active_buffs["0304"]["timer"] += dt
            if self.active_buffs["0304"]["timer"] >= 1000:      
                self.active_buffs["0304"]["timer"] = 0
                self.score = max(0, self.score - 6)             

    # ─── 主更新 ───────────────────────────────────────────────────────────

    def update(self):
        if not self.running or self.paused or self.game_over_flag:
            return

        # 非线性抽卡与空卡池跳过检测
        if self.card_draw_index < len(CARD_DRAW_THRESHOLDS):
            if self.score >= CARD_DRAW_THRESHOLDS[self.card_draw_index]:
                self.card_draw_index += 1
                available = [k for k in ALL_CARDS if k not in self.owned_cards]
                
                # 如果有卡可抽，才进入选卡界面；否则静默跳过（只加索引）
                if len(available) > 0:
                    self._pre_card_state   = self.internal_state   
                    self.internal_state    = STATE_SELECT_CARD
                    self.card_select_start_time = pygame.time.get_ticks()
                    self.current_card_choices   = self.card_manager.draw_three_cards(self.owned_cards)
                    return

        if self.internal_state == STATE_SELECT_CARD:
            return

        current_time = pygame.time.get_ticks()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        self.skill_manager.update(current_time)
        self.process_zibai_queue(current_time)
        self.update_buffs_and_timers(dt, current_time)

        if self.effects_manager.meteor:
            board_h   = (global_state['screen_size'][1] - 80) // GRID_HEIGHT * GRID_HEIGHT
            cell_size = board_h // GRID_HEIGHT
            center_y  = (global_state['screen_size'][1] - board_h) // 2
            if self.effects_manager.meteor.update(center_y, cell_size):
                sr = self.effects_manager.meteor.target_row
                for y in range(sr, min(sr + 3, GRID_HEIGHT)):   
                    for x in range(GRID_WIDTH):
                        if self.grid[y][x]:
                            self.elimination_list.append((y, x))
                self.effects_manager.meteor = None
                if self.elimination_list:
                    self.internal_state = STATE_PRE_CLEAR
                    self.state_timer    = current_time

        self.effects_manager.update(current_time)

        if self.internal_state == STATE_PRE_CLEAR:
            if current_time - self.state_timer > DELAY_PRE_CLEAR:
                self.execute_elimination_and_explode()
        elif self.internal_state == STATE_EXPLODING:
            if not self.effects_manager.explosions:
                self.resolve_grid_stability()
        elif self.internal_state == STATE_ANIMATING:
            if not self.effects_manager.falling_anims:
                self.internal_state = STATE_POST_FALL_DELAY
                self.state_timer    = current_time
                if self.check_collision(self.current_blocks):
                    test = [{"color": b["color"], "x": b["x"], "y": b["y"] - 1}
                            for b in self.current_blocks]
                    if not self.check_collision(test):
                        self.current_blocks = test
        elif self.internal_state == STATE_POST_FALL_DELAY:
            if current_time - self.state_timer > DELAY_POST_FALL:
                self.resolve_grid_stability()

        if (not self.game_over_flag and
                self.internal_state not in (STATE_PRE_CLEAR, STATE_EXPLODING,
                                            STATE_ANIMATING, STATE_POST_FALL_DELAY,
                                            STATE_SELECT_CARD)):
            if current_time >= self.next_stone_time:
                self.spawn_stones()
                self.next_stone_time = current_time + int(
                    STONE_INTERVAL * self.stone_interval_multiplier)  
        
        # 终极防卡死处理
        if self.internal_state == STATE_PLAYING:
            if not self.current_blocks and not self.game_over_flag:
                self.current_blocks = self.spawn_new_blocks_from_next()
            elif self.current_blocks:
                if current_time - self.last_drop_time > self.normal_drop_interval:
                    self.last_drop_time = current_time
                    new_pos = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1}
                               for b in self.current_blocks]
                    if self.check_collision(new_pos):
                        self.place_blocks()
                    else:
                        self.current_blocks = new_pos

        # 【安全兜底】若动画链状态持续超过 8 秒未能自动退出（理论上不应发生），
        # 强制清理并跳回 STATE_PLAYING，防止游戏彻底卡死。
        _ANIM_STATES = (STATE_PRE_CLEAR, STATE_EXPLODING,
                        STATE_ANIMATING, STATE_POST_FALL_DELAY)
        if self.internal_state in _ANIM_STATES:
            if not hasattr(self, '_stuck_check_timer'):
                self._stuck_check_timer = current_time
            elif current_time - self._stuck_check_timer > 8000:
                self.effects_manager.explosions    = []
                self.effects_manager.falling_anims = []
                self.elimination_list = []
                self.resolve_grid_stability()
                self._stuck_check_timer = current_time
        else:
            self._stuck_check_timer = current_time