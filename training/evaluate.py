"""模型评估"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

import torch
import numpy as np
from training.neural_network import EinsteinNet
from shared.game_engine import EinsteinGame
from shared.mcts import MCTS
import random

class AIEvaluator:
    def __init__(self, model_path=None):
        self.game = EinsteinGame()
        self.neural_net = EinsteinNet()
        
        if model_path and os.path.exists(model_path):
            self.neural_net.load_state_dict(torch.load(model_path, map_location='cpu'))
            self.neural_net.eval()
            print(f"Loaded model from {model_path}")
        else:
            print("Using random initialization")
        
        self.mcts = MCTS(self.game, self.neural_net, num_simulations=1000)
    
    def play_vs_random(self, ai_player=1, num_games=50):
        """AI vs 随机玩家"""
        wins = 0
        draws = 0
        
        for game_num in range(num_games):
            board = self._get_initial_board()
            current_player = 1
            move_count = 0
            max_moves = 200
            
            while not self.game.is_terminal(board) and move_count < max_moves:
                die = random.randint(1, 6)
                
                if current_player == ai_player:
                    # AI回合
                    best_action = self.mcts.search(board, die, current_player)
                    if best_action is not None:
                        board = self.game.apply_action(board, best_action, die, current_player)
                else:
                    # 随机玩家回合
                    legal_actions = self.game.get_legal_actions(board, die, current_player)
                    if legal_actions:
                        action = random.choice(legal_actions)
                        board = self.game.apply_action(board, action, die, current_player)
                
                current_player = -current_player
                move_count += 1
            
            # 判断结果
            if self.game.is_terminal(board):
                reward = self.game.get_reward(board, ai_player)
                if reward > 0:
                    wins += 1
                elif reward == 0:
                    draws += 1
            else:
                draws += 1  # 超时算平局
            
            if (game_num + 1) % 10 == 0:
                print(f"Game {game_num + 1}/{num_games}: "
                      f"Wins={wins}, Draws={draws}, Losses={game_num + 1 - wins - draws}")
        
        win_rate = wins / num_games
        return win_rate, wins, draws, num_games - wins - draws
    
    def _get_initial_board(self):
        """获取初始棋盘"""
        board = np.zeros((5, 5), dtype=int)
        
        # 红方
        red_positions = [(0,0), (0,1), (0,2), (1,0), (1,1), (2,0)]
        for i, pos in enumerate(red_positions):
            board[pos] = i + 1
        
        # 蓝方
        blue_positions = [(2,4), (3,3), (3,4), (4,2), (4,3), (4,4)]
        for i, pos in enumerate(blue_positions):
            board[pos] = i + 7
        
        return board

def evaluate_model(model_path, num_games=100):
    """评估模型性能"""
    print(f"Evaluating model: {model_path}")
    print(f"Number of games: {num_games}")
    print("-" * 50)
    
    evaluator = AIEvaluator(model_path)
    
    # 作为蓝方vs随机
    print("AI as Blue vs Random...")
    win_rate_blue, wins_blue, draws_blue, losses_blue = evaluator.play_vs_random(
        ai_player=1, num_games=num_games//2
    )
    
    print(f"Blue AI: Win Rate = {win_rate_blue:.2%} "
          f"({wins_blue}W-{draws_blue}D-{losses_blue}L)")
    
    # 作为红方vs随机
    print("\nAI as Red vs Random...")
    win_rate_red, wins_red, draws_red, losses_red = evaluator.play_vs_random(
        ai_player=-1, num_games=num_games//2
    )
    
    print(f"Red AI: Win Rate = {win_rate_red:.2%} "
          f"({wins_red}W-{draws_red}D-{losses_red}L)")
    
    # 总体统计
    overall_win_rate = (wins_blue + wins_red) / num_games
    print(f"\nOverall Win Rate: {overall_win_rate:.2%}")
    
    if overall_win_rate >= 0.8:
        print("🎉 Excellent performance!")
    elif overall_win_rate >= 0.6:
        print("✅ Good performance!")
    elif overall_win_rate >= 0.4:
        print("⚠️  Acceptable performance")
    else:
        print("❌ Poor performance - needs more training")
    
    return overall_win_rate

if __name__ == "__main__":
    model_path = "../models/shared_model.pth"
    
    if not os.path.exists(model_path):
        print(f"Model not found: {model_path}")
        print("Please train a model first using train_model.py")
    else:
        evaluate_model(model_path, num_games=50)