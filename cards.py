# baqi/cards.py
import random
from settings import CARD_TIER_WEIGHTS

# 卡牌数据库
ALL_CARDS = {
    # --- 1系：消除与技能增强 ---
    "0101": {"name": "璃月港口",  "desc": "消除任何方块时，减少技能20%冷却，冷却10s"},
    "0102": {"name": "钟离假死",  "desc": "接下来30组方块减少一种颜色"},
    "0103": {"name": "磨损",      "desc": "未来掉落所有灰色石头的时间间隔增加50%"},
    "0104": {"name": "劳逸结合",  "desc": "所有消除分数永久提升20%"},
    "0105": {"name": "八奇·朱赤","desc": "每60秒消除所有红色方块"},
    "0106": {"name": "八奇·无妄","desc": "每60秒消除所有蓝色方块"},
    "0107": {"name": "八奇·云来","desc": "每60秒消除所有紫色方块"},
    "0108": {"name": "八奇·万象","desc": "每60秒消除所有绿色方块"},
    "0109": {"name": "八奇·金目","desc": "每60秒消除所有黄色方块"},
    "0110": {"name": "闲云冲击波","desc": "三连消减少100%E技能冷却，二连消减少20%"},
    "0111": {"name": "兹白之力",  "desc": "获得Q技能：暂停时间20秒，无方块下落"},
    "0112": {"name": "画龙点睛",  "desc": "获得Q技能：若陀之力，毁灭全场方块后落下三行石头"},
    "0113": {"name": "璃月水神",  "desc": "概率触发两列雨帘剑消除，堆叠越高概率越大"},
    "0114": {"name": "钟离之力",  "desc": "清除全场石头，并获得玉璋护盾抵挡石头"},
    # --- 2系：规则改变 ---
    "0201": {"name": "岩与契约",  "desc": "舍弃顶层两行，获得40%冷却减免和双倍得分，但高度限制更严"},
    "0202": {"name": "山崩岩崒",  "desc": "同色概率提升，但同色下落会震碎周围方块"},
    "0203": {"name": "无妄坡",    "desc": "概率出现迷雾遮罩，遮罩方块会逐渐消失"},
    # --- 3系：特殊/恶搞 ---
    "0301": {"name": "围观食客",  "desc": "中毒debuff：禁用下键，消除引发3x3爆炸"},
    "0302": {"name": "我编的",    "desc": "蓝砚之力：E技能获得随机效果"},
    "0303": {"name": "仙人来栽",  "desc": "随机种植薄荷，消除薄荷方块获得大量分数"},
    "0304": {"name": "往生堂账",  "desc": "每秒扣分，获得[刷新]能力"},
    "0305": {"name": "荒星破顶",  "desc": "无视顶部判定失败，但失去上方视野，超限使用技能判负"},
}


class CardManager:
    def __init__(self):
        self.reroll_counts = 0

    def draw_three_cards(self, owned_cards=None):
        """
        【修复 6】加权无放回抽卡：
          01系权重 > 02系权重 > 03系权重（权重值在 settings.CARD_TIER_WEIGHTS 中调整）
        """
        if owned_cards is None:
            owned_cards = []
        pool = [k for k in ALL_CARDS if k not in owned_cards]
        if len(pool) <= 3:
            return pool

        # 根据系别权重进行无放回加权随机采样
        weights   = [CARD_TIER_WEIGHTS.get(cid[:2], 1) for cid in pool]  # ← [可调] 权重来自 settings.py
        result    = []
        remaining = list(pool)
        rem_w     = list(weights)

        for _ in range(3):
            if not remaining:
                break
            total = sum(rem_w)
            r     = random.uniform(0, total)
            cumul = 0.0
            for i, (card, w) in enumerate(zip(remaining, rem_w)):
                cumul += w
                if r <= cumul:
                    result.append(card)
                    remaining.pop(i)
                    rem_w.pop(i)
                    break

        return result

    def apply_card_effect(self, game, card_id):
        if card_id not in game.owned_cards:
            game.owned_cards.append(card_id)

        # ── 立即生效的效果（带可调系数注释）──
        if card_id == "0102":
            game.color_reduce_charges = 30          # ← [可调] 减色持续组数
        elif card_id == "0103":
            game.stone_interval_multiplier *= 1.5   # ← [可调] 石头间隔延长倍率
        elif card_id == "0104":
            game.score_multiplier += 0.2            # ← [可调] 得分加成增量
        elif card_id == "0111":
            game.q_skill_id = "0111"
        elif card_id == "0112":
            game.q_skill_id = "0112"
        elif card_id == "0114":
            game.q_skill_id = "0114"
        elif card_id == "0201":
            game.grid_height_limit = int(game.grid_height_limit * 0.8)  # ← [可调] 高度限制缩减比例
            game.score_multiplier  *= 2.0                                # ← [可调] 双倍得分倍率
        elif card_id == "0202":
            game.same_color_prob_boost = True
        elif card_id == "0301":
            game.disable_down_key = True
        elif card_id == "0304":
            self.reroll_counts += 3                 # ← [可调] 获得刷新次数

        elif card_id == "0305":
            game.ignore_top_limit = True

        # 【修复】移除了错误的 game.internal_state = 0
        # resume_from_card_select() 会在 main.py 中正确恢复状态