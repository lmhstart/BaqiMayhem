# baqi/game_logic.py
import pygame
import random
from settings import *
from effects import Explosion, FallingAnim, MeteoriteAnim
from skill import SkillManager

# 状态常量
STATE_PLAYING = 0
STATE_PRE_CLEAR = 1
STATE_EXPLODING = 2
STATE_ANIMATING = 3
STATE_POST_FALL_DELAY = 4

DELAY_PRE_CLEAR = 100
DELAY_POST_FALL = 100


class EffectsManager:
    def __init__(self):
        self.falling_anims = []
        self.explosions = []
        self.meteor = None  # 钟离的天星对象

    def clear(self):
        self.falling_anims = []
        self.explosions = []
        self.meteor = None

    def update(self, current_time, board_origin_y=0, cell_size=60):
        # 爆炸动画
        for exp in self.explosions:
            exp.update(current_time)
        self.explosions = [e for e in self.explosions if not e.finished]

        # 下落动画
        all_falling_finished = True
        for anim in self.falling_anims:
            anim.update()
            if not anim.finished:
                all_falling_finished = False

        # 陨石动画逻辑需在外部 Game.update 处理碰撞，这里只负责返回状态
        return all_falling_finished


class Game:
    def __init__(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.marks = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        # 【兹白】结晶马的计时器网格，记录落地后的时间。0表示未落地或不是Bloom
        self.bloom_timers = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.last_update_time = pygame.time.get_ticks()

        self.score = 0
        self.current_blocks = []
        self.next_blocks_data = []

        self.running = False
        self.paused = False
        self.game_over_flag = False

        self.internal_state = STATE_PLAYING
        self.state_timer = 0
        self.elimination_list = []

        self.effects_manager = EffectsManager()
        self.skill_manager = SkillManager()

        self.normal_drop_interval = NORMAL_DROP_INTERVAL
        self.last_drop_time = 0
        self.next_stone_time = 0

        # --- 新角色逻辑变量 ---
        self.ganyu_buff_charges = 0  # 甘雨剩余同色次数
        self.zibai_summon_queue = []  # 兹白待召唤时间队列

    def start_new_game(self):
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.marks = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.bloom_timers = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

        self.score = 0
        self.paused = False
        self.game_over_flag = False
        self.running = True
        self.internal_state = STATE_PLAYING
        self.effects_manager.clear()
        self.elimination_list = []

        self.ganyu_buff_charges = 0
        self.zibai_summon_queue = []

        # 设置角色并重置技能CD
        self.skill_manager.set_character(global_state['current_character'])
        self.skill_manager.reset()

        self.next_blocks_data = self.generate_random_pair()
        self.current_blocks = self.spawn_new_blocks_from_next()

        now = pygame.time.get_ticks()
        self.last_drop_time = now
        self.next_stone_time = now + STONE_INITIAL_DELAY
        self.last_update_time = now

    def generate_random_pair(self):
        colors = ["blue", "green", "purple", "yellow", "red"]

        # 【甘雨技能逻辑】
        if self.ganyu_buff_charges > 0:
            self.ganyu_buff_charges -= 1
            c = random.choice(colors)
            return [c, c]  # 返回同色

        return [random.choice(colors), random.choice(colors)]

    def spawn_new_blocks_from_next(self):
        if not self.next_blocks_data: self.next_blocks_data = self.generate_random_pair()
        c1, c2 = self.next_blocks_data
        self.next_blocks_data = self.generate_random_pair()
        x = GRID_WIDTH // 2 - 1
        y = 0
        if self.grid[y][x] or self.grid[y + 1][x]:
            self.game_over_flag = True
            return []
        return [{"color": c1, "x": x, "y": y}, {"color": c2, "x": x, "y": y + 1}]

    def spawn_stones(self):
        cols = random.sample(range(GRID_WIDTH), 2)
        spawned = False
        for x in cols:
            if self.grid[0][x] is None:
                self.grid[0][x] = "stone"
                self.marks[0][x] = False
                self.bloom_timers[0][x] = 0
                spawned = True
        if spawned: self.resolve_grid_stability()

    def spawn_meteor(self, target_y):
        # 钟离技能：初始化陨石动画
        # 计算棋盘像素高度
        board_h = (global_state['screen_size'][1] - 80) // GRID_HEIGHT * GRID_HEIGHT
        self.effects_manager.meteor = MeteoriteAnim(target_y, board_h)

    def process_zibai_queue(self, current_time):
        # 兹白技能：处理召唤队列
        if not self.zibai_summon_queue: return

        # 取出所有时间已到的召唤请求
        remaining = []
        for t in self.zibai_summon_queue:
            if current_time >= t:
                self.spawn_bloom_block()
            else:
                remaining.append(t)
        self.zibai_summon_queue = remaining

    def spawn_bloom_block(self):
        # 随机找一列抛入 Bloom
        # 尝试多次找一个空位
        cols = list(range(GRID_WIDTH))
        random.shuffle(cols)
        for x in cols:
            if self.grid[0][x] is None:
                self.grid[0][x] = "bloom"
                self.marks[0][x] = False
                self.bloom_timers[0][x] = 0  # 初始计时为0
                self.resolve_grid_stability()
                return

    def check_collision(self, blocks):
        for block in blocks:
            if block["x"] < 0 or block["x"] >= GRID_WIDTH or block["y"] >= GRID_HEIGHT: return True
            if block["y"] >= 0 and self.grid[block["y"]][block["x"]]: return True
        return False

    def rotate_blocks(self):
        if not self.current_blocks: return
        pivot = self.current_blocks[0]
        new_blocks = []
        for block in self.current_blocks:
            dx, dy = block["x"] - pivot["x"], block["y"] - pivot["y"]
            new_blocks.append({"color": block["color"], "x": pivot["x"] - dy, "y": pivot["y"] + dx})
        if not self.check_collision(new_blocks): self.current_blocks = new_blocks

    def place_blocks(self):
        for block in self.current_blocks:
            if block["y"] >= 0 and self.grid[block["y"]][block["x"]] is None:
                self.grid[block["y"]][block["x"]] = block["color"]
                self.marks[block["y"]][block["x"]] = False
                self.bloom_timers[block["y"]][block["x"]] = 0
        self.current_blocks = []
        self.resolve_grid_stability()

    def check_elimination_conditions(self):
        visited = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        to_eliminate = set()

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell = self.grid[y][x]
                # bloom 和 stone 不参与普通颜色消除
                if cell and cell not in ["stone", "bloom"] and not visited[y][x]:
                    stack = [(y, x)]
                    group = set()
                    while stack:
                        cy, cx = stack.pop()
                        if (cy, cx) in group: continue
                        group.add((cy, cx))
                        visited[cy][cx] = True
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx] == cell:
                                stack.append((ny, nx))

                    if len(group) >= 4:
                        to_eliminate.update(group)
                        # 刻晴技能与石头连锁逻辑
                        for (gy, gx) in group:
                            # 炸石头
                            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                ny, nx = gy + dy, gx + dx
                                if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx] == "stone":
                                    to_eliminate.add((ny, nx))

                            # 刻晴标记
                            if self.marks[gy][gx]:
                                offsets = SkillManager.get_keqing_explosion_offsets()
                                for ody, odx in offsets:
                                    ny, nx = gy + ody, gx + odx
                                    if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH and self.grid[ny][nx] is not None:
                                        to_eliminate.add((ny, nx))
                                self.marks[gy][gx] = False

        if to_eliminate:
            self.elimination_list = list(to_eliminate)
            return True
        return False

    def execute_elimination_and_explode(self):
        stone_count = 0
        normal_count = 0
        for (y, x) in self.elimination_list:
            color = self.grid[y][x]
            if color:
                if color == "stone":
                    stone_count += 1
                elif color == "bloom":
                    normal_count += 0  # Bloom 被动消除不加分? 或者当做普通
                else:
                    normal_count += 1

                self.effects_manager.explosions.append(Explosion(x, y, color))
                self.grid[y][x] = None
                self.marks[y][x] = False
                self.bloom_timers[y][x] = 0

        points = normal_count * SCORE_PER_BLOCK + stone_count * STONE_BONUS
        self.score += points
        self.elimination_list = []
        self.internal_state = STATE_EXPLODING

    def setup_falling_animations(self):
        has_falling = False
        new_grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_marks = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        new_timers = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]  # 同步 bloom timer

        self.effects_manager.falling_anims = []

        for x in range(GRID_WIDTH):
            write_y = GRID_HEIGHT - 1
            for read_y in range(GRID_HEIGHT - 1, -1, -1):
                block_color = self.grid[read_y][x]
                if block_color:
                    target_y = write_y
                    new_grid[target_y][x] = block_color
                    new_marks[target_y][x] = self.marks[read_y][x]
                    # 下落时重置计时器？或者保持？
                    # 规则：landing后三秒。如果正在下落，则不是landing状态。
                    # 所以如果发生下落，计时器应该归零（重新开始计时）或者暂停。这里简单点：归零。
                    # 如果 read_y == target_y (没动)，则保留原计时
                    if read_y == target_y:
                        new_timers[target_y][x] = self.bloom_timers[read_y][x]
                    else:
                        new_timers[target_y][x] = 0

                    if read_y != target_y:
                        has_falling = True
                        self.effects_manager.falling_anims.append(
                            FallingAnim(x, read_y, target_y, block_color)
                        )
                    write_y -= 1

        self.grid = new_grid
        self.marks = new_marks
        self.bloom_timers = new_timers
        return has_falling

    def resolve_grid_stability(self):
        if self.setup_falling_animations():
            self.internal_state = STATE_ANIMATING
            if self.check_collision(self.current_blocks):
                test = [{"x": b["x"], "y": b["y"] - 1, "color": b["color"]} for b in self.current_blocks]
                if not self.check_collision(test): self.current_blocks = test
            return
        if self.check_elimination_conditions():
            self.internal_state = STATE_PRE_CLEAR
            self.state_timer = pygame.time.get_ticks()
            return
        self.internal_state = STATE_PLAYING
        if not self.current_blocks and not self.game_over_flag:
            self.current_blocks = self.spawn_new_blocks_from_next()

    def update_bloom_timers(self, dt):
        """兹白：更新所有静态Bloom的计时器"""
        if self.internal_state != STATE_PLAYING: return

        has_explosion = False
        to_explode = set()

        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x] == "bloom":
                    # 确保下方是底部或者有方块（即处于稳定着陆状态）
                    if y == GRID_HEIGHT - 1 or self.grid[y + 1][x] is not None:
                        self.bloom_timers[y][x] += dt
                        if self.bloom_timers[y][x] >= 3000:  # 3秒
                            # 触发小范围爆炸
                            # 本身
                            to_explode.add((y, x))
                            # 上下左右
                            for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                ny, nx = y + dy, x + dx
                                if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH:
                                    if self.grid[ny][nx] is not None:
                                        to_explode.add((ny, nx))

        if to_explode:
            self.elimination_list = list(to_explode)
            # 立即触发清除（绕过PRE_CLEAR延迟，或者设为PRE_CLEAR）
            # 为了统一流程，设为PRE_CLEAR
            self.internal_state = STATE_PRE_CLEAR
            self.state_timer = pygame.time.get_ticks() - DELAY_PRE_CLEAR + 10  # 几乎立即触发

    def update(self):
        if not self.running or self.paused or self.game_over_flag: return
        current_time = pygame.time.get_ticks()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        self.skill_manager.update(current_time)
        self.process_zibai_queue(current_time)
        self.update_bloom_timers(dt)

        # 钟离陨石逻辑
        if self.effects_manager.meteor:
            # 获取 board_origin_y 用于碰撞检测
            board_h = (global_state['screen_size'][1] - 80) // GRID_HEIGHT * GRID_HEIGHT
            cell_size = board_h // GRID_HEIGHT
            center_y = (global_state['screen_size'][1] - board_h) // 2

            hit = self.effects_manager.meteor.update(center_y, cell_size)
            if hit:
                # 摧毁 target_row 开始的3行
                start_row = self.effects_manager.meteor.target_row
                for y in range(start_row, min(start_row + 3, GRID_HEIGHT)):
                    for x in range(GRID_WIDTH):
                        if self.grid[y][x]:
                            self.elimination_list.append((y, x))

                self.effects_manager.meteor = None  # 移除陨石对象
                if self.elimination_list:
                    self.internal_state = STATE_PRE_CLEAR
                    self.state_timer = current_time

        if self.internal_state == STATE_PRE_CLEAR:
            if current_time - self.state_timer > DELAY_PRE_CLEAR:
                self.execute_elimination_and_explode()

        elif self.internal_state == STATE_EXPLODING:
            self.effects_manager.update(current_time)
            if not self.effects_manager.explosions:
                self.resolve_grid_stability()

        elif self.internal_state == STATE_ANIMATING:
            all_finished = self.effects_manager.update(current_time)
            if all_finished:
                self.effects_manager.falling_anims = []
                self.internal_state = STATE_POST_FALL_DELAY
                self.state_timer = current_time
                if self.check_collision(self.current_blocks):
                    test = [{"x": b["x"], "y": b["y"] - 1, "color": b["color"]} for b in self.current_blocks]
                    if not self.check_collision(test): self.current_blocks = test

        elif self.internal_state == STATE_POST_FALL_DELAY:
            if current_time - self.state_timer > DELAY_POST_FALL:
                self.resolve_grid_stability()

        if not self.game_over_flag and self.internal_state not in [STATE_PRE_CLEAR, STATE_EXPLODING]:
            if current_time >= self.next_stone_time:
                self.spawn_stones()
                self.next_stone_time = current_time + STONE_INTERVAL

        if self.internal_state == STATE_PLAYING:
            if current_time - self.last_drop_time > self.normal_drop_interval:
                self.last_drop_time = current_time
                new_pos = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in self.current_blocks]
                if self.check_collision(new_pos):
                    self.place_blocks()
                else:
                    self.current_blocks = new_pos
