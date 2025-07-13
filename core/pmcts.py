"""
修正的概率启发的蒙特卡洛树搜索(PMCTS)算法实现
根据论文描述和用户反馈修正的关键问题：
1. 概率节点的概率分布：根节点概率为1，其他为1/6
2. 选择策略：随机选择概率节点，UCB选择最值节点
3. 扩展策略：一次性创建所有6个概率节点，避免偏差
4. 回溯路径：正确处理Max/Min节点和多父节点情况
5. 数据存储：概率节点存储骰子信息，最值节点存储统计信息
"""
from __future__ import annotations  # 添加这行

import math
import random
import numpy as np
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from core.game_engine import EinsteinGame

class ProbabilityNode:
    """
    概率节点类 - 论文3.2.1节
    用于表示骰子事件的概率节点，每个概率节点对应一个骰子点数
    """
    
    def __init__(self, dice_value: int, probability: float):
        """
        初始化概率节点
        
        参数:
            dice_value: 骰子点数 (1-6)
            probability: 该骰子点数出现的概率（根节点为1.0，其他为1/6）
        """
        self.dice_value = dice_value      # 骰子点数
        self.probability = probability    # 概率值：根节点1.0，其他1/6
        self.children: List[MCTSNode] = []               # 子节点列表 (MCTSNode类型)
        self.parent_mcts_node: Optional[MCTSNode] = None     # 父MCTS节点的引用

class MCTSNode:
    """
    MCTS树中的最值节点 - 论文中的决策节点
    每个节点代表一个游戏状态，存储访问次数、胜利次数等统计信息
    """
    
    def __init__(self, board: np.ndarray, player: int, move: Optional[Tuple[int, int, int, int]] = None, is_root: bool = False):
        """
        初始化MCTS节点
        
        参数:
            board: 当前棋盘状态
            player: 当前轮到的玩家 (1=蓝方Max节点, -1=红方Min节点)
            move: 导致此状态的移动
            is_root: 是否为根节点
        """
        self.board = board.copy()        # 当前棋盘状态的副本
        self.player = player             # 当前玩家
        self.move = move                 # 导致此状态的移动
        self.is_root = is_root          # 是否为根节点
        
        # 最值节点的统计信息
        self.visits = 0                  # 访问次数
        self.wins = 0.0                  # 胜利次数(可以是小数)
        
        # 概率子节点字典 {dice_value: ProbabilityNode}
        self.probability_children: Dict[int, ProbabilityNode] = {}   
        self.parent_prob_nodes: List[ProbabilityNode] = []      # 父概率节点列表（一个最值节点可能有多个父概率节点）
    
    def is_fully_expanded(self) -> bool:
        """检查节点是否已完全扩展(所有骰子点数都已尝试)"""
        return len(self.probability_children) == 6
    
    def get_win_rate(self) -> float:
        """
        获取当前节点的胜率值 (对于对方节点取负值)
        
        返回:
            胜率值 (-1.0 到 1.0 之间)
        """
        if self.visits == 0:
            return 0.5  # 未访问节点返回中性值
        
        # 计算胜率：wins可能为负值(对方节点)
        win_rate = self.wins / self.visits
        return win_rate
    
    def select_best_move_child_ucb(self, prob_node: ProbabilityNode) -> Optional[MCTSNode]:
        """
        使用UCB公式从概率节点的子节点中选择最佳移动节点
        这是论文中正确的做法：对最值节点使用UCB选择
        
        参数:
            prob_node: 概率节点
            
        返回:
            UCB值最高的移动节点
        """
        if not prob_node.children:
            return None
        
        best_value = -float('inf')
        best_child = None
        
        # 对概率节点的所有子节点（最值节点）计算UCB值
        for child in prob_node.children:
            if child.visits == 0:
                # 未访问的节点给最高优先级
                return child
            
            # UCB公式：平均胜率 + 探索项

            exploitation = child.get_win_rate()
         
            # 使用当前节点的访问次数计算探索项
            exploration = math.sqrt(2*math.log(self.visits) / child.visits)
            ucb_value = exploitation + exploration
            
            if ucb_value > best_value:
                best_value = ucb_value
                best_child = child
        
        return best_child
    
    def select_probability_child_random(self) -> Optional[ProbabilityNode]:
        """
        随机选择概率节点
        这是论文中正确的做法：对概率节点使用随机选择
        
        返回:
            随机选择的概率节点
        """
        if not self.probability_children:
            return None
        
        # 根据概率分布随机选择概率节点
        prob_nodes = list(self.probability_children.values())
        probabilities = [node.probability for node in prob_nodes]
        
        # 归一化概率（防止数值误差）
        total_prob = sum(probabilities)
        if total_prob > 0:
            probabilities = [p / total_prob for p in probabilities]
            # 使用numpy的随机选择函数
            selected_idx = np.random.choice(len(prob_nodes), p=probabilities)
            return prob_nodes[selected_idx]
        else:
            # 如果概率都为0，则均匀随机选择
            return random.choice(prob_nodes)
    
    def expand_all_probability_nodes(self, game: "EinsteinGame", current_die: Optional[int] = None) -> bool:
        """
        一次性扩展所有概率节点 - 根据论文步骤1-4的正确做法
        
        步骤1: 创建6个概率节点，初始化概率节点的参数d和p
        步骤2: 将概率节点加入叶子节点的孩子列表中
        步骤3: 根据叶子节点的棋盘状态生成所有合法走法，创建最值节点
        步骤4: 对于每一个骰子点数，在所有合法走法中找出骰子点数已知情况下的合法走法，
               并将对应最值节点与概率节点建立连接
        
        参数:
            game: 游戏引擎
            current_die: 当前已知骰子点数（仅对根节点有效）
            
        返回:
            是否成功扩展
        """
        if self.probability_children:
            return False  # 已经扩展过了
        
        
        # 步骤1: 创建6个概率节点，初始化概率节点的参数d和p
        for dice_value in range(1, 7):
            # 设置正确的概率值
            if self.is_root and current_die is not None:
                # 根节点：只有当前已知骰子点数概率为1，其他为0
                probability = 1.0 if dice_value == current_die else 0.0
            else:
                # 非根节点：所有骰子点数概率为1/6
                probability = 1.0/6
            
            # 创建概率节点
            prob_node = ProbabilityNode(dice_value, probability)
            prob_node.parent_mcts_node = self
            
            # 步骤2: 将概率节点加入叶子节点的孩子列表中
            self.probability_children[dice_value] = prob_node
        
        # 步骤3: 根据叶子节点的棋盘状态生成所有合法走法，创建最值节点
        # 首先收集所有可能的移动（不考虑骰子限制）
        all_possible_moves = set()
        
        for dice_value in range(1, 7):
            legal_moves = game.get_legal_moves(self.board, dice_value, self.player)
            for move in legal_moves:
                all_possible_moves.add(move)
        
        # 为每个唯一的移动创建最值节点
        move_to_node = {}  # 移动到节点的映射
        
        for move in all_possible_moves:
            # 执行移动得到新状态
            new_board = game.make_move(self.board, move)
            next_player = -self.player  # 切换玩家
            
            # 创建新的MCTS节点
            child_node = MCTSNode(new_board, next_player, move=move)
            move_to_node[move] = child_node
        
        # 步骤4: 对于每一个骰子点数，在所有合法走法中找出骰子点数已知情况下
        # 的合法走法，并将对应最值节点与概率节点建立连接
        for dice_value in range(1, 7):
            prob_node = self.probability_children[dice_value]
            legal_moves = game.get_legal_moves(self.board, dice_value, self.player)
            
            for move in legal_moves:
                if move in move_to_node:
                    child_node = move_to_node[move]
                    # 建立连接：概率节点 -> 最值节点
                    prob_node.children.append(child_node)
                    # 设置最值节点的父概率节点（一个最值节点可能有多个父概率节点）
                    child_node.parent_prob_nodes.append(prob_node)
        
        return True
    
    def simulate(self, game: "EinsteinGame", max_moves: int = 200) -> float:
        """
        从当前节点开始进行随机模拟，直到游戏结束
        
        参数:
            game: 游戏引擎
            max_moves: 最大模拟步数(防止无限循环)
            
        返回:
            模拟结果 (1.0=当前玩家获胜, 0.0=对手获胜, 0.5=平局)
        """
        current_board = self.board.copy()  # 复制当前棋盘状态
        current_player = self.player       # 当前玩家
        moves_count = 0                    # 移动计数器
        
        # 进行随机模拟直到游戏结束或达到最大步数
        while not game.is_game_over(current_board) and moves_count < max_moves:
            # 生成随机骰子点数
            die = random.randint(1, 6)
            
            # 获取当前玩家的合法移动
            legal_moves = game.get_legal_moves(current_board, die, current_player)
            
            if not legal_moves:
                break  # 没有合法移动，模拟结束
            
            # 随机选择一个移动并执行
            move = random.choice(legal_moves)
            current_board = game.make_move(current_board, move)
            
            # 切换到下一个玩家
            current_player = -current_player
            moves_count += 1
        
        # 评估最终游戏结果
        winner = game.get_winner(current_board)
        
        if winner == self.player:
            return 0.0    # 当前玩家获胜
        elif winner == -self.player:
            return 1.0    # 对手获胜
        else:
            # 游戏未结束或平局
            return 0.5
    
    def backpropagate(self, result: float) -> None:
        """
        回传模拟结果到根节点
        处理最值节点可能有多个父概率节点的情况
        
        参数:
            result: 模拟结果 (1.0=获胜, -1.0=失败，从模拟节点的玩家视角)
        """
        # 更新当前节点的统计信息
        self.visits += 1
        self.wins += result  # result可能为负值
        
        # 如果有父概率节点，需要回传结果
        if self.parent_prob_nodes:
            # 选择第一个父概率节点进行回传
            prob_node = self.parent_prob_nodes[0]
            if prob_node.parent_mcts_node:
                # 向上回溯时，结果需要反转（当前玩家的胜利对父节点是失败）
                parent_mcts_node = prob_node.parent_mcts_node
                reversed_result = -result  # 反转结果
                parent_mcts_node.backpropagate(reversed_result)


class PMCTS:
    """
    修正的概率启发的蒙特卡洛树搜索算法主类
    基于论文第3.2节实现，修正了扩展策略和选择策略
    """
    
    def __init__(self, game: "EinsteinGame", exploration_constant: float = 1.0):
        """
        初始化PMCTS
        
        参数:
            game: 游戏引擎实例
            exploration_constant: UCB公式中的探索常数
        """
        self.game = game
        self.exploration_constant = exploration_constant
    
    def search(self, board: np.ndarray, die: int, player: int, num_simulations: int) -> Optional[Tuple[int, int, int, int]]:
        """
        执行PMCTS搜索，返回最佳移动
        
        参数:
            board: 当前棋盘状态
            die: 当前骰子点数（已知）
            player: 当前玩家
            num_simulations: 模拟次数
            
        返回:
            最佳移动 (from_x, from_y, to_x, to_y)，如果没有合法移动则返回None
        """
        # 获取当前骰子点数下的所有合法移动
        legal_moves = self.game.get_legal_moves(board, die, player)
        
        if not legal_moves:
            return None  # 没有合法移动
        
        if len(legal_moves) == 1:
            return legal_moves[0]  # 只有一个合法移动，直接返回
        
        # 创建根节点（最值节点）
        root = MCTSNode(board, player, is_root=True)
        
        print(f"开始PMCTS搜索: {num_simulations}次模拟, {len(legal_moves)}个可选移动")
        
        # 一次性扩展根节点的所有概率节点
        root.expand_all_probability_nodes(self.game, current_die=die)
        
        print(f"根节点扩展完成，当前骰子点数={die}")

        # 执行指定次数的PMCTS迭代
        for simulation in range(num_simulations):
            # 第1步: 选择 - 从根节点开始选择到叶子节点
            selected_node = self._select(root)
            
            # 第2步: 扩展 - 如果游戏未结束且可以扩展，则扩展节点
            if not self.game.is_game_over(selected_node.board):
                self._expand(selected_node)
            
            # 第3步: 模拟 - 从选中的节点随机模拟到游戏结束
            result = selected_node.simulate(self.game)
            
            # 第4步: 回传 - 将结果回传到根节点
            selected_node.backpropagate(result)
            
            # 进度输出
            if (simulation + 1) % (num_simulations // 10) == 0:
                progress = (simulation + 1) / num_simulations * 100
                print(f"搜索进度: {progress:.0f}%")
        
        # 选择访问次数最多的移动
        best_move = self._select_best_move(root, die)
        
        if best_move:
            print(f"最佳移动: {best_move}")
        else:
            print("未找到最佳移动")
        
        return best_move
    
    def _select(self, root: MCTSNode) -> MCTSNode:
        """
        选择阶段：
        - 随机选择概率节点（论文正确做法）
        - UCB选择最值节点（论文正确做法）
        
        参数:
            root: 根节点
            
        返回:
            选择到的叶子节点
        """
        node = root
        
        # 向下选择直到找到叶子节点或终止状态
        while node.probability_children and not self.game.is_game_over(node.board):
            # 随机选择概率子节点
            prob_node = node.select_probability_child_random()
            if not prob_node or not prob_node.children:
                break
            
            # 使用UCB从概率节点的子节点中选择最佳移动节点
            next_node = node.select_best_move_child_ucb(prob_node)
            if not next_node:
                break
            
            node = next_node
        
        return node

    def _expand(self, node: MCTSNode) -> None:
        """
        扩展阶段：一次性扩展所有概率节点，从所有新创建的节点中选择一个
        
        参数:
            node: 要扩展的节点
            
        返回:
            不需要返回任何东西只需扩展即可
        """
        # 如果节点还没有完全扩展，一次性扩展所有概率节点
        if not node.is_fully_expanded():
            success = node.expand_all_probability_nodes(self.game)

    def _select_best_move(self, root: MCTSNode, die: int) -> Optional[Tuple[int, int, int, int]]:
        """
        选择最佳移动
        
        参数:
            root: 根节点
            die: 当前骰子点数
            
        返回:
            最佳移动
        """
        # 获取当前骰子点数对应的概率节点
        if die not in root.probability_children:
            return None
        
        prob_node = root.probability_children[die]
        if not prob_node.children:
            return None
        
        # 选择访问次数最多的子节点对应的移动
        best_child = max(prob_node.children, key=lambda c: c.visits)
        
        # 输出统计信息
        win_rate = best_child.get_win_rate()
        print(f"最佳移动访问{best_child.visits}次, 获胜次数{best_child.wins},胜率{win_rate:.2%}")
        
        return best_child.move