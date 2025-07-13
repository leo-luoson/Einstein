"""
自对弈训练模块
通过AI自我对战生成训练数据
"""

import numpy as np
import random
from typing import List, Tuple
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.game_engine import GameEngine
from training.neural_network import NeuralNetwork
from shared.mcts import MCTS
from shared.config import Config

class SelfPlay:
    """自对弈训练类"""
    
    def __init__(self, model: NeuralNetwork):
        self.model = model
        self.game_engine = GameEngine()
        self.mcts = MCTS(model, self.game_engine, Config.MCTS_SIMULATIONS)
        
    def play_game(self) -> List[Tuple[np.ndarray, int, float]]:
        """
        进行一局自对弈
        返回: [(board_state, player, result), ...]
        """
        # 初始化棋盘
        board = self._initialize_board()
        game_history = []
        current_player = 0  # 0=红方先手
        
        while True:
            # 检查游戏是否结束
            is_over, winner = self.game_engine.is_game_over(board)
            if is_over:
                # 为历史记录分配奖励
                return self._assign_rewards(game_history, winner)
            
            # 记录当前状态
            game_history.append((board.copy(), current_player, 0.0))
            
            # 投掷骰子
            die = random.randint(1, 6)
            
            # 获取当前玩家的棋子
            if current_player == 0:
                pieces = self.game_engine.get_red_pieces(board)
            else:
                pieces = self.game_engine.get_blue_pieces(board)
            
            # 使用MCTS选择移动
            if pieces:
                move = self.mcts.search(board, pieces, die, current_player)
                board = self.game_engine.make_move(board, move, current_player)
            
            # 切换玩家
            current_player = 1 - current_player
            
            # 防止无限循环
            if len(game_history) > 200:
                break
        
        # 如果游戏太长，返回平局
        return self._assign_rewards(game_history, None)
    
    def _initialize_board(self) -> np.ndarray:
        """初始化棋盘（随机布局）"""
        board = np.zeros((5, 5), dtype=int)
        
        # 红方棋子位置（左上角区域）
        red_positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (2, 0)]
        red_pieces = list(range(1, 7))
        random.shuffle(red_pieces)
        
        for i, pos in enumerate(red_positions):
            board[pos[0]][pos[1]] = red_pieces[i]
        
        # 蓝方棋子位置（右下角区域）
        blue_positions = [(4, 4), (4, 3), (4, 2), (3, 4), (3, 3), (2, 4)]
        blue_pieces = list(range(7, 13))
        random.shuffle(blue_pieces)
        
        for i, pos in enumerate(blue_positions):
            board[pos[0]][pos[1]] = blue_pieces[i]
        
        return board
    
    def _assign_rewards(self, game_history: List[Tuple[np.ndarray, int, float]], 
                       winner: int) -> List[Tuple[np.ndarray, int, float]]:
        """为游戏历史分配奖励"""
        if winner is None:
            # 平局
            return [(board, player, 0.0) for board, player, _ in game_history]
        
        # 分配奖励：获胜方+1，失败方-1
        result = []
        for board, player, _ in game_history:
            if player == winner:
                reward = 1.0
            else:
                reward = -1.0
            result.append((board, player, reward))
        
        return result
    
    def generate_training_data(self, num_games: int) -> List[Tuple[np.ndarray, int, float]]:
        """生成训练数据"""
        all_data = []
        
        for game_num in range(num_games):
            if game_num % 10 == 0:
                print(f"正在进行第 {game_num + 1}/{num_games} 局自对弈...")
            
            game_data = self.play_game()
            all_data.extend(game_data)
        
        print(f"自对弈完成，生成了 {len(all_data)} 条训练数据")
        return all_data

if __name__ == "__main__":
    # 创建模型
    model = NeuralNetwork()
    
    # 开始自对弈
    self_play = SelfPlay(model)
    training_data = self_play.generate_training_data(10)
    
    print(f"生成了 {len(training_data)} 条训练样本")
