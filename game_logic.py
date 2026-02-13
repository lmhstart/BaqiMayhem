# baqi/game_logic.py
import pygame
import random
from settings import *
from resources import R

# 内部状态常量
STATE_PLAYING = 0
STATE_ANIMATING = 1


class Game:
    def __init__(self):
        # 初始化网格
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.current_blocks = []
        self.next_blocks_data = []  # 下一个方块数据

        # 游戏流程控制
        self.running = False
        self.paused = False
        self.game_over_flag = False
        self.internal_state = STATE_PLAYING

        # 动画列表
        self.falling_animations = []

        # --- 从 settings.py 读取参数 ---
        self.normal_drop_interval = NORMAL_DROP_INTERVAL  # 自然下落间隔
        self.last_drop_time = 0

        # 石头生成计时器
        self.game_start_time = 0
        self.next_stone_time = 0

    def start_new_game(self):
        """开始新游戏，重置所有状态"""
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.score = 0
        self.paused = False
        self.game_over_flag = False
        self.running = True
        self.internal_state = STATE_PLAYING
        self.falling_animations = []

        # 初始化方块
        self.next_blocks_data = self.generate_random_pair()
        self.current_blocks = self.spawn_new_blocks_from_next()

        # 重置计时器
        now = pygame.time.get_ticks()
        self.game_start_time = now
        self.last_drop_time = now
        # 第一波石头生成的时刻
        self.next_stone_time = now + STONE_INITIAL_DELAY

    def generate_random_pair(self):
        """生成一对随机颜色的方块数据"""
        colors = ["blue", "green", "purple", "yellow"]
        return [random.choice(colors), random.choice(colors)]

    def spawn_new_blocks_from_next(self):
        """将'下一个'方块移动到'当前'，并生成新的'下一个'"""
        if not self.next_blocks_data:
            self.next_blocks_data = self.generate_random_pair()

        c1 = self.next_blocks_data[0]
        c2 = self.next_blocks_data[1]

        # 刷新下一个预览
        self.next_blocks_data = self.generate_random_pair()

        # 初始位置：顶部中间
        x = GRID_WIDTH // 2 - 1
        y = 0

        # 如果出生点被堵住，游戏结束
        if self.grid[y][x] or self.grid[y + 1][x]:
            self.game_over_flag = True
            return []

        return [{"color": c1, "x": x, "y": y}, {"color": c2, "x": x, "y": y + 1}]

    def spawn_stones(self):
        """生成干扰石头"""
        # 随机选两列
        cols = random.sample(range(GRID_WIDTH), 2)
        spawned = False
        for x in cols:
            # 只有顶格为空才生成
            if self.grid[0][x] is None:
                # 确保不会生成在玩家当前的方块身体里
                player_here = False
                for b in self.current_blocks:
                    if b['x'] == x and b['y'] == 0:
                        player_here = True
                        break
                if not player_here:
                    self.grid[0][x] = "stone"
                    spawned = True

        # 如果生成了石头，可能导致悬空，需要处理重力
        if spawned:
            self.resolve_grid_stability()

    def check_collision(self, blocks):
        """碰撞检测"""
        for block in blocks:
            # 边界检查
            if block["x"] < 0 or block["x"] >= GRID_WIDTH or block["y"] >= GRID_HEIGHT:
                return True
            # 占用检查 (只检查y>=0的部分，虽然逻辑上y都>=0)
            if block["y"] >= 0 and self.grid[block["y"]][block["x"]]:
                return True
        return False

    def rotate_blocks(self):
        """旋转方块 (以第一个块为轴心)"""
        if self.internal_state != STATE_PLAYING: return

        pivot = self.current_blocks[0]
        new_blocks = []
        for block in self.current_blocks:
            # 相对坐标
            dx = block["x"] - pivot["x"]
            dy = block["y"] - pivot["y"]
            # 旋转90度公式: (x, y) -> (-y, x)
            new_x = pivot["x"] - dy
            new_y = pivot["y"] + dx
            new_blocks.append({"color": block["color"], "x": new_x, "y": new_y})

        if not self.check_collision(new_blocks):
            self.current_blocks = new_blocks

    def place_blocks(self):
        """将当前方块固定到网格中"""
        for block in self.current_blocks:
            if block["y"] >= 0:
                self.grid[block["y"]][block["x"]] = block["color"]
        self.current_blocks = []
        # 固定后，检查是否需要消除或掉落
        self.resolve_grid_stability()

    def resolve_grid_stability(self):
        """处理网格稳定性：掉落 -> 消除 -> 掉落 循环"""
        # 1. 检查是否有悬空方块需要掉落
        if self.setup_falling_animations():
            self.internal_state = STATE_ANIMATING
            return

        # 2. 如果稳定，检查是否有消除
        if self.check_elimination():
            # 如果发生了消除，再次递归检查稳定性（可能消除后又有方块悬空）
            self.resolve_grid_stability()
            return

        # 3. 如果既没掉落也没消除，回合结束，生成新方块
        self.internal_state = STATE_PLAYING
        if not self.current_blocks and not self.game_over_flag:
            self.current_blocks = self.spawn_new_blocks_from_next()

    def check_elimination(self):
        """检查并执行消除逻辑"""
        eliminated = set()
        visited = [[False for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        current_round_eliminated = set()

        # 遍历全图寻找同色连通区域
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell = self.grid[y][x]
                if cell and cell != "stone" and not visited[y][x]:
                    color = cell
                    # DFS 搜索
                    dfs_stack = [(y, x)]
                    connected_coords = set()

                    while dfs_stack:
                        cy, cx = dfs_stack.pop()
                        if (cy, cx) in connected_coords: continue

                        connected_coords.add((cy, cx))
                        visited[cy][cx] = True

                        # 检查上下左右
                        for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            ny, nx = cy + dy, cx + dx
                            if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH:
                                if self.grid[ny][nx] == color:
                                    dfs_stack.append((ny, nx))

                    # 规则：4个及以上消除
                    if len(connected_coords) >= 4:
                        current_round_eliminated.update(connected_coords)
                        # 检查周围是否有石头（石头被消除波及）
                        for (cy, cx) in connected_coords:
                            for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                                ny, nx = cy + dy, cx + dx
                                if 0 <= ny < GRID_HEIGHT and 0 <= nx < GRID_WIDTH:
                                    if self.grid[ny][nx] == "stone":
                                        current_round_eliminated.add((ny, nx))

        if current_round_eliminated:
            stone_count = 0
            normal_count = 0
            for (y, x) in current_round_eliminated:
                if self.grid[y][x] == "stone":
                    stone_count += 1
                else:
                    normal_count += 1
                self.grid[y][x] = None  # 执行消除

            # 计算分数 (从 settings 读取)
            points = normal_count * SCORE_PER_BLOCK
            points += stone_count * STONE_BONUS
            self.score += points
            return True  # 发生了消除

        return False  # 无事发生

    def setup_falling_animations(self):
        """检测悬空方块并建立下落动画"""
        self.falling_animations = []
        has_falling = False
        V_SIZE = 100  # 虚拟高度单位，用于平滑动画

        for x in range(GRID_WIDTH):
            column_blocks = []
            # 从下往上扫描，收集非空方块
            for y in range(GRID_HEIGHT - 1, -1, -1):
                if self.grid[y][x]:
                    column_blocks.append({'color': self.grid[y][x], 'old_y': y})
                    self.grid[y][x] = None  # 先从网格移除，交给动画接管

            # 重新计算它们落地后的位置（堆叠在底部）
            target_y = GRID_HEIGHT - 1
            for block in column_blocks:
                color = block['color']
                old_y = block['old_y']

                if old_y != target_y:
                    # 需要下落
                    self.falling_animations.append({
                        'x': x,
                        'start_y_pixel': old_y * V_SIZE,
                        'current_y_pixel': old_y * V_SIZE,
                        'target_y_pixel': target_y * V_SIZE,
                        'target_grid_y': target_y,
                        'color': color,
                        'v_size': V_SIZE
                    })
                    has_falling = True
                else:
                    # 已经在正确位置，直接放回网格
                    self.grid[target_y][x] = color
                target_y -= 1

        return has_falling

    def update(self):
        """游戏主循环逻辑"""
        if not self.running or self.paused or self.game_over_flag:
            return

        current_time = pygame.time.get_ticks()

        # --- 状态A: 动画进行中 ---
        if self.internal_state == STATE_ANIMATING:
            all_finished = True
            for anim in self.falling_animations:
                # 动画速度从 settings 读取
                drop_speed = ANIMATION_DROP_SPEED * (anim['v_size'] / 20.0)

                if anim['current_y_pixel'] < anim['target_y_pixel']:
                    anim['current_y_pixel'] += drop_speed
                    all_finished = False
                    # 防止过冲
                    if anim['current_y_pixel'] > anim['target_y_pixel']:
                        anim['current_y_pixel'] = anim['target_y_pixel']

            if all_finished:
                # 动画结束，将方块写回网格
                for anim in self.falling_animations:
                    self.grid[anim['target_grid_y']][anim['x']] = anim['color']
                self.falling_animations = []
                # 动画结束后，再次检查是否构成了新的消除
                self.resolve_grid_stability()

        # --- 状态B: 玩家操作中 ---
        elif self.internal_state == STATE_PLAYING:
            # 1. 检查生成石头 (时间从 settings 读取)
            if current_time >= self.next_stone_time:
                self.spawn_stones()
                self.next_stone_time = current_time + STONE_INTERVAL
                # 如果生成石头导致了下落动画，直接返回，暂停玩家控制
                if self.internal_state == STATE_ANIMATING: return

                # 2. 自然下落 (速度从 settings 读取)
            if current_time - self.last_drop_time > self.normal_drop_interval:
                self.last_drop_time = current_time
                new_pos = [{"color": b["color"], "x": b["x"], "y": b["y"] + 1} for b in self.current_blocks]

                if self.check_collision(new_pos):
                    self.place_blocks()
                else:
                    self.current_blocks = new_pos

    def draw(self, screen):
        """绘制游戏界面"""
        # === 1. 动态布局计算 ===
        sw, sh = global_state['screen_size']

        # 棋盘高度，上下留边距 (仿七圣召唤卡牌长宽比)
        margin_v = 40
        board_pixel_h = sh - margin_v * 2
        # 方块大小动态计算
        dyn_block_size = board_pixel_h // GRID_HEIGHT

        # 棋盘总宽度
        board_pixel_w = dyn_block_size * GRID_WIDTH

        # 棋盘居中稍微偏右一点，左边留给“悬挂卷轴”
        center_x = (sw - board_pixel_w) // 2 + 60
        center_y = (sh - board_pixel_h) // 2

        # 内部函数：绘制单个方块
        def draw_block_at(color, grid_x, grid_y, pixel_y_offset=None):
            img = R.get_block_image(color)
            if not img: return
            scaled = pygame.transform.scale(img, (dyn_block_size, dyn_block_size))
            dest_x = center_x + grid_x * dyn_block_size
            if pixel_y_offset is not None:
                dest_y = center_y + pixel_y_offset
            else:
                dest_y = center_y + grid_y * dyn_block_size
            screen.blit(scaled, (dest_x, dest_y))

        # === 2. 绘制棋盘背景（仿木质边框） ===
        board_rect = pygame.Rect(center_x, center_y, board_pixel_w, board_pixel_h)
        # 外框 (金色/浅棕色)
        padding = 8
        frame_rect = board_rect.inflate(padding * 2, padding * 2)
        pygame.draw.rect(screen, (160, 120, 80), frame_rect, border_radius=8)
        # 内底 (深褐色)
        pygame.draw.rect(screen, (40, 30, 25), board_rect, border_radius=4)

        # 画淡色网格线
        for i in range(1, GRID_WIDTH):
            line_x = center_x + i * dyn_block_size
            pygame.draw.line(screen, (60, 50, 45), (line_x, center_y), (line_x, center_y + board_pixel_h), 2)
        for i in range(1, GRID_HEIGHT):
            line_y = center_y + i * dyn_block_size
            pygame.draw.line(screen, (60, 50, 45), (center_x, line_y), (center_x + board_pixel_w, line_y), 2)

        # === 3. 绘制左侧“灯笼/卷轴”悬挂预览 (The Lantern) ===
        # 挂在棋盘左侧边框上
        lantern_w = dyn_block_size * 1.5
        lantern_h = dyn_block_size * 2.8
        lantern_x = center_x - lantern_w - 15
        lantern_y = center_y + 50

        # 灯笼挂绳
        pygame.draw.line(screen, (139, 69, 19), (lantern_x + lantern_w // 2, center_y),
                         (lantern_x + lantern_w // 2, lantern_y), 4)

        # 灯笼本体背景
        lantern_rect = pygame.Rect(lantern_x, lantern_y, lantern_w, lantern_h)
        pygame.draw.rect(screen, (240, 230, 210), lantern_rect, border_radius=10)  # 米白色纸质感
        pygame.draw.rect(screen, (160, 82, 45), lantern_rect, 4, border_radius=10)  # 边框

        # 灯笼上下装饰
        pygame.draw.rect(screen, (139, 69, 19), (lantern_x, lantern_y, lantern_w, 15), border_top_left_radius=10,
                         border_top_right_radius=10)
        pygame.draw.rect(screen, (139, 69, 19), (lantern_x, lantern_y + lantern_h - 15, lantern_w, 15),
                         border_bottom_left_radius=10, border_bottom_right_radius=10)

        # 绘制“下一个”文字 (使用 R.font)
        # 调整字体大小以适应灯笼
        font_small = pygame.font.Font(None, 24)
        if R.font:  # 如果有中文字体，尝试创建一个小号的
            try:
                # 这种方式可能不通用，简单起见用 R.font 缩放
                text_surf = R.font.render("下一个", True, (100, 50, 20))
                text_surf = pygame.transform.scale(text_surf, (int(lantern_w * 0.8), int(lantern_w * 0.4)))
            except:
                text_surf = font_small.render("NEXT", True, (100, 50, 20))
        else:
            text_surf = font_small.render("NEXT", True, (100, 50, 20))

        screen.blit(text_surf, (lantern_x + (lantern_w - text_surf.get_width()) // 2, lantern_y + 20))

        # 绘制预览方块
        if self.next_blocks_data:
            c1, c2 = self.next_blocks_data

            # 计算预览方块位置（在灯笼中间）
            preview_size = int(dyn_block_size * 0.9)
            p_x = lantern_x + (lantern_w - preview_size) // 2
            p_y_start = lantern_y + (lantern_h - preview_size * 2) // 2 + 10

            img1 = R.get_block_image(c1)
            img2 = R.get_block_image(c2)

            if img1:
                s1 = pygame.transform.scale(img1, (preview_size, preview_size))
                screen.blit(s1, (p_x, p_y_start))
            if img2:
                s2 = pygame.transform.scale(img2, (preview_size, preview_size))
                screen.blit(s2, (p_x, p_y_start + preview_size))

        # === 4. 右侧绘制分数面板 ===
        score_x = center_x + board_pixel_w + 30
        score_y = center_y + 50

        # 分数背景圆盘
        pygame.draw.circle(screen, (50, 40, 40), (score_x + 50, score_y + 50), 60)
        pygame.draw.circle(screen, (255, 215, 0), (score_x + 50, score_y + 50), 60, 3)  # 金边

        score_label = R.font.render("得分", True, (200, 200, 200))
        score_val = R.font.render(str(self.score), True, (255, 255, 255))

        # 居中显示
        screen.blit(score_label, score_label.get_rect(center=(score_x + 50, score_y + 30)))
        screen.blit(score_val, score_val.get_rect(center=(score_x + 50, score_y + 70)))

        # === 5. 绘制方块内容 ===

        # 静态层
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.grid[y][x]:
                    draw_block_at(self.grid[y][x], x, y)

        # 动画层
        for anim in self.falling_animations:
            pixel_y = (anim['current_y_pixel'] / anim['v_size']) * dyn_block_size
            draw_block_at(anim['color'], anim['x'], 0, pixel_y_offset=pixel_y)

        # 玩家层 (当前控制的方块)
        for block in self.current_blocks:
            if block["y"] >= 0:
                draw_block_at(block["color"], block["x"], block["y"])

        # === 6. 游戏结束提示 ===
        if self.game_over_flag:
            overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            go_text = R.font.render("胜负已分", True, (220, 80, 80))
            # 放大一点
            go_text = pygame.transform.scale(go_text, (int(go_text.get_width() * 1.5), int(go_text.get_height() * 1.5)))

            score_text = R.font.render(f"最终得分: {self.score}", True, WHITE)

            screen.blit(go_text, go_text.get_rect(center=(sw // 2, sh // 2 - 60)))
            screen.blit(score_text, score_text.get_rect(center=(sw // 2, sh // 2 + 40)))
