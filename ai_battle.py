"""
机机对弈系统 - 用于训练和评估AI性能
支持批量对战、性能统计、数据收集等功能
为后续价值网络训练提供数据支持
"""

import numpy as np
import time
import json
import random
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.game_engine import EinsteinGame
from core.pmcts import PMCTS
from core.config import Config

@dataclass
class GameResult:
    """游戏结果数据类"""
    winner: int  # 1=蓝方获胜, -1=红方获胜, 0=平局
    total_moves: int  # 总移动数
    game_duration: float  # 游戏时长(秒)
    blue_thinking_time: float  # 蓝方总思考时间
    red_thinking_time: float  # 红方总思考时间
    final_board: np.ndarray  # 最终棋盘状态
    move_history: List[Tuple[int, int, int, int, int, int]]  # 移动历史 (move, player, die)
    board_states: List[np.ndarray]  # 所有棋盘状态(用于训练数据)

@dataclass
class AIPlayer:
    """AI玩家配置"""
    name: str
    player_id: int  # 1=蓝方, -1=红方
    simulation_count: int
    exploration_constant: float
    time_limit: Optional[float] = None  # 思考时间限制(秒)

class AIBattleSystem:
    """AI对战系统"""
    
    def __init__(self):
        """初始化对战系统"""
        self.game = EinsteinGame()
        self.battle_results: List[GameResult] = []
        self.statistics = {
            'total_games': 0,
            'blue_wins': 0,
            'red_wins': 0,
            'draws': 0,
            'average_game_length': 0.0,
            'average_thinking_time': 0.0
        }
    
    def create_ai_player(self, name: str, player_id: int, difficulty: int, 
                        custom_simulations: Optional[int] = None,
                        custom_exploration: Optional[float] = None) -> AIPlayer:
        """
        创建AI玩家
        
        参数:
            name: 玩家名称
            player_id: 玩家ID (1=蓝方, -1=红方)
            difficulty: 难度等级 (3-5)
            custom_simulations: 自定义模拟次数
            custom_exploration: 自定义探索常数
            
        返回:
            AI玩家对象
        """
        simulations = custom_simulations or Config.MCTS_SIMULATIONS.get(difficulty, 2000)
        exploration = custom_exploration or Config.UCB_CONSTANT
        
        return AIPlayer(
            name=name,
            player_id=player_id,
            simulation_count=simulations,
            exploration_constant=exploration
        )
    
    def single_battle(self, blue_ai: AIPlayer, red_ai: AIPlayer, 
                     initial_board: Optional[np.ndarray] = None,
                     max_moves: int = 200,
                     verbose: bool = False) -> GameResult:
        """
        执行单场AI对战
        
        参数:
            blue_ai: 蓝方AI
            red_ai: 红方AI
            initial_board: 初始棋盘(None则使用默认布局)
            max_moves: 最大移动数
            verbose: 是否输出详细信息
            
        返回:
            游戏结果
        """
        if verbose:
            print(f"开始对战: {blue_ai.name} vs {red_ai.name}")
        
        # 初始化游戏状态
        if initial_board is not None:
            board = initial_board.copy()
        else:
            board = self._generate_default_board()
        
        current_player = 1  # 蓝方先手
        move_count = 0
        start_time = time.time()
        
        # 记录数据
        move_history = []
        board_states = [board.copy()]
        blue_thinking_time = 0.0
        red_thinking_time = 0.0
        
        # 创建AI实例
        blue_pmcts = PMCTS(self.game, blue_ai.exploration_constant)
        red_pmcts = PMCTS(self.game, red_ai.exploration_constant)
        
        while not self.game.is_game_over(board) and move_count < max_moves:
            # 生成随机骰子
            die = random.randint(1, 6)
            
            # 检查是否有合法移动
            legal_moves = self.game.get_legal_moves(board, die, current_player)
            if not legal_moves:
                if verbose:
                    player_name = "蓝方" if current_player == 1 else "红方"
                    print(f"{player_name} 无合法移动，跳过回合")
                current_player = -current_player
                continue
            
            # AI思考
            think_start = time.time()
            
            if current_player == 1:  # 蓝方回合
                best_move = blue_pmcts.search(board, die, current_player, blue_ai.simulation_count)
                blue_thinking_time += time.time() - think_start
                ai_name = blue_ai.name
            else:  # 红方回合
                best_move = red_pmcts.search(board, die, current_player, red_ai.simulation_count)
                red_thinking_time += time.time() - think_start
                ai_name = red_ai.name
            
            if best_move is None:
                if verbose:
                    print(f"{ai_name} 未找到合法移动")
                current_player = -current_player
                continue
            
            # 执行移动
            board = self.game.make_move(board, best_move)
            move_count += 1
            
            # 记录移动
            move_history.append((*best_move, current_player, die))
            board_states.append(board.copy())
            
            if verbose:
                print(f"第{move_count}回合: {ai_name} 骰子{die} 移动 {best_move}")
            
            # 切换玩家
            current_player = -current_player
        
        # 计算结果
        game_duration = time.time() - start_time
        winner = self.game.get_winner(board)
        
        if verbose:
            if winner == 1:
                print(f"游戏结束: {blue_ai.name} 获胜！")
            elif winner == -1:
                print(f"游戏结束: {red_ai.name} 获胜！")
            else:
                print("游戏结束: 平局")
            print(f"总回合数: {move_count}, 游戏时长: {game_duration:.2f}秒")
        
        return GameResult(
            winner=winner,
            total_moves=move_count,
            game_duration=game_duration,
            blue_thinking_time=blue_thinking_time,
            red_thinking_time=red_thinking_time,
            final_board=board,
            move_history=move_history,
            board_states=board_states
        )
    
    def batch_battle(self, blue_ai: AIPlayer, red_ai: AIPlayer,
                    num_games: int = 100,
                    parallel: bool = True,
                    max_workers: int = 4,
                    progress_callback = None) -> List[GameResult]:
        """
        批量对战
        
        参数:
            blue_ai: 蓝方AI配置
            red_ai: 红方AI配置
            num_games: 对战场数
            parallel: 是否并行执行
            max_workers: 最大工作线程数
            progress_callback: 进度回调函数
            
        返回:
            所有游戏结果列表
        """
        print(f"开始批量对战: {num_games} 场")
        print(f"{blue_ai.name} vs {red_ai.name}")
        
        results = []
        
        if parallel and num_games > 1:
            # 并行执行
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                
                for game_idx in range(num_games):
                    future = executor.submit(
                        self.single_battle,
                        blue_ai, red_ai,
                        initial_board=None,
                        verbose=False
                    )
                    futures.append(future)
                
                # 收集结果
                for i, future in enumerate(as_completed(futures)):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if progress_callback:
                            progress_callback(len(results), num_games)
                        
                        if (len(results)) % 10 == 0:
                            print(f"已完成 {len(results)}/{num_games} 场对战")
                            
                    except Exception as e:
                        print(f"游戏 {i+1} 执行出错: {e}")
        else:
            # 串行执行
            for game_idx in range(num_games):
                try:
                    result = self.single_battle(blue_ai, red_ai, verbose=False)
                    results.append(result)
                    
                    if progress_callback:
                        progress_callback(game_idx + 1, num_games)
                    
                    if (game_idx + 1) % 10 == 0:
                        print(f"已完成 {game_idx + 1}/{num_games} 场对战")
                        
                except Exception as e:
                    print(f"游戏 {game_idx + 1} 执行出错: {e}")
        
        # 保存结果
        self.battle_results.extend(results)
        self._update_statistics(results)
        
        print(f"批量对战完成，共 {len(results)} 场有效对战")
        return results
    
    def tournament(self, ai_configs: List[Dict], 
                  games_per_match: int = 50) -> Dict:
        """
        锦标赛模式 - 多个AI互相对战
        
        参数:
            ai_configs: AI配置列表，每个包含name, difficulty, simulations等
            games_per_match: 每对AI之间的对战场数
            
        返回:
            锦标赛结果统计
        """
        print(f"开始锦标赛: {len(ai_configs)} 个AI参与")
        
        tournament_results = {}
        match_results = []
        
        # 创建AI玩家
        ai_players = []
        for config in ai_configs:
            ai_players.append(self.create_ai_player(
                name=config['name'],
                player_id=1,  # 会在对战时调整
                difficulty=config.get('difficulty', 4),
                custom_simulations=config.get('simulations'),
                custom_exploration=config.get('exploration')
            ))
        
        # 两两对战
        for i, ai1 in enumerate(ai_players):
            for j, ai2 in enumerate(ai_players):
                if i >= j:  # 避免重复对战和自己对战自己
                    continue
                
                print(f"对战: {ai1.name} vs {ai2.name}")
                
                # AI1作为蓝方，AI2作为红方
                blue_ai = AIPlayer(ai1.name + "(蓝)", 1, ai1.simulation_count, ai1.exploration_constant)
                red_ai = AIPlayer(ai2.name + "(红)", -1, ai2.simulation_count, ai2.exploration_constant)
                
                results = self.batch_battle(blue_ai, red_ai, games_per_match, parallel=True)
                
                # 统计这场比赛的结果
                blue_wins = sum(1 for r in results if r.winner == 1)
                red_wins = sum(1 for r in results if r.winner == -1)
                draws = sum(1 for r in results if r.winner == 0)
                
                match_result = {
                    'ai1': ai1.name,
                    'ai2': ai2.name,
                    'ai1_wins': blue_wins,
                    'ai2_wins': red_wins,
                    'draws': draws,
                    'total_games': len(results)
                }
                match_results.append(match_result)
                
                print(f"结果: {ai1.name} {blue_wins}胜 vs {ai2.name} {red_wins}胜, 平局 {draws}")
        
        # 计算总排名
        ai_scores = {ai.name: 0 for ai in ai_players}
        
        for match in match_results:
            ai1, ai2 = match['ai1'], match['ai2']
            ai1_wins, ai2_wins = match['ai1_wins'], match['ai2_wins']
            
            # 计分规则：胜利3分，平局1分，失败0分
            if ai1_wins > ai2_wins:
                ai_scores[ai1] += 3
            elif ai2_wins > ai1_wins:
                ai_scores[ai2] += 3
            else:
                ai_scores[ai1] += 1
                ai_scores[ai2] += 1
        
        # 排序
        ranking = sorted(ai_scores.items(), key=lambda x: x[1], reverse=True)
        
        tournament_results = {
            'match_results': match_results,
            'final_ranking': ranking,
            'ai_scores': ai_scores
        }
        
        self._print_tournament_results(tournament_results)
        return tournament_results
    
    def collect_training_data(self, num_games: int = 1000,
                             save_path: str = "training_data.json") -> List[Dict]:
        """
        收集训练数据用于价值网络训练
        
        参数:
            num_games: 收集的游戏数量
            save_path: 保存路径
            
        返回:
            训练数据列表
        """
        print(f"开始收集训练数据: {num_games} 场游戏")
        
        # 创建不同强度的AI进行对战，增加数据多样性
        ai_configs = [
            {'name': 'Weak', 'difficulty': 3},
            {'name': 'Medium', 'difficulty': 4},
            {'name': 'Strong', 'difficulty': 5},
        ]
        
        training_data = []
        games_per_config = num_games // len(ai_configs)
        
        for config in ai_configs:
            print(f"使用 {config['name']} AI 收集数据...")
            
            blue_ai = self.create_ai_player(f"Blue_{config['name']}", 1, config['difficulty'])
            red_ai = self.create_ai_player(f"Red_{config['name']}", -1, config['difficulty'])
            
            results = self.batch_battle(blue_ai, red_ai, games_per_config, parallel=True)
            
            # 处理每场游戏的数据
            for result in results:
                game_data = self._extract_training_data(result)
                training_data.extend(game_data)
        
        # 保存数据
        if save_path:
            self._save_training_data(training_data, save_path)
            print(f"训练数据已保存到: {save_path}")
        
        print(f"共收集到 {len(training_data)} 个训练样本")
        return training_data
    
    def _extract_training_data(self, result: GameResult) -> List[Dict]:
        """
        从游戏结果中提取训练数据
        每个样本包含：棋盘状态、当前玩家、最终结果
        """
        training_samples = []
        
        # 为每个棋盘状态创建训练样本
        for i, board_state in enumerate(result.board_states[:-1]):  # 排除最终状态
            # 确定当前玩家（根据移动历史）
            if i < len(result.move_history):
                current_player = result.move_history[i][4]  # move_history中的player
            else:
                current_player = 1  # 默认蓝方开始
            
            # 计算价值标签（从当前玩家视角）
            if result.winner == current_player:
                value = 1.0  # 胜利
            elif result.winner == -current_player:
                value = -1.0  # 失败
            else:
                value = 0.0  # 平局
            
            sample = {
                'board_state': board_state.tolist(),
                'current_player': current_player,
                'value': value,
                'game_length': result.total_moves,
                'move_index': i
            }
            training_samples.append(sample)
        
        return training_samples
    
    def _save_training_data(self, training_data: List[Dict], filepath: str):
        """保存训练数据到文件"""
        import os
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
    
    def _generate_default_board(self) -> np.ndarray:
        """生成默认初始棋盘布局"""
        board = np.array([
            [0, 0, 0, 0, 12],
            [0, 0, 0, 11, 0],
            [0, 0, 10, 9, 8],
            [0, 7, 0, 0, 0],
            [1, 0, 0, 0, 0]
        ])
        
        # 随机放置剩余棋子
        empty_positions = [(i, j) for i in range(5) for j in range(5) if board[i, j] == 0]
        remaining_pieces = [2, 3, 4, 5, 6]  # 红方剩余棋子
        
        random.shuffle(empty_positions)
        for i, piece in enumerate(remaining_pieces):
            if i < len(empty_positions):
                row, col = empty_positions[i]
                board[row, col] = piece
        
        return board
    
    def _update_statistics(self, results: List[GameResult]):
        """更新统计信息"""
        self.statistics['total_games'] += len(results)
        
        for result in results:
            if result.winner == 1:
                self.statistics['blue_wins'] += 1
            elif result.winner == -1:
                self.statistics['red_wins'] += 1
            else:
                self.statistics['draws'] += 1
        
        # 计算平均值
        if self.statistics['total_games'] > 0:
            total_moves = sum(r.total_moves for r in results)
            total_time = sum(r.blue_thinking_time + r.red_thinking_time for r in results)
            
            self.statistics['average_game_length'] = total_moves / len(results)
            self.statistics['average_thinking_time'] = total_time / len(results)
    
    def _print_tournament_results(self, results: Dict):
        """打印锦标赛结果"""
        print("\n" + "="*50)
        print("锦标赛结果")
        print("="*50)
        
        print("\n最终排名:")
        for i, (ai_name, score) in enumerate(results['final_ranking']):
            print(f"{i+1:2d}. {ai_name:15s} - {score:3d} 分")
        
        print("\n详细对战结果:")
        for match in results['match_results']:
            print(f"{match['ai1']:12s} vs {match['ai2']:12s} | "
                  f"{match['ai1_wins']:2d}胜 {match['ai2_wins']:2d}负 {match['draws']:2d}平")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        stats = self.statistics.copy()
        
        if stats['total_games'] > 0:
            stats['blue_win_rate'] = stats['blue_wins'] / stats['total_games']
            stats['red_win_rate'] = stats['red_wins'] / stats['total_games']
            stats['draw_rate'] = stats['draws'] / stats['total_games']
        else:
            stats['blue_win_rate'] = 0.0
            stats['red_win_rate'] = 0.0
            stats['draw_rate'] = 0.0
        
        return stats
    
    def save_results(self, filepath: str):
        """保存对战结果到文件"""
        results_data = {
            'statistics': self.get_statistics(),
            'battle_results': []
        }
        
        # 转换结果为可序列化格式
        for result in self.battle_results:
            result_dict = {
                'winner': result.winner,
                'total_moves': result.total_moves,
                'game_duration': result.game_duration,
                'blue_thinking_time': result.blue_thinking_time,
                'red_thinking_time': result.red_thinking_time,
                'final_board': result.final_board.tolist(),
                'move_history': result.move_history
            }
            results_data['battle_results'].append(result_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        print(f"对战结果已保存到: {filepath}")


class BattleGUI:
    """机机对弈图形界面"""
    
    def __init__(self, battle_system: AIBattleSystem):
        """初始化对弈界面"""
        import tkinter as tk
        from tkinter import ttk
        
        self.battle_system = battle_system
        self.root = tk.Tk()
        self.root.title("AI对战系统")
        self.root.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        import tkinter as tk
        from tkinter import ttk
        
        # 主框架
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # AI配置区域
        config_frame = tk.LabelFrame(main_frame, text="AI配置", font=("Arial", 12))
        config_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 蓝方AI配置
        blue_frame = tk.Frame(config_frame)
        blue_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        
        tk.Label(blue_frame, text="蓝方AI", font=("Arial", 11, "bold"), fg="blue").pack()
        
        tk.Label(blue_frame, text="难度:").pack(anchor=tk.W)
        self.blue_difficulty = tk.Scale(blue_frame, from_=3, to=5, orient=tk.HORIZONTAL)
        self.blue_difficulty.set(4)
        self.blue_difficulty.pack(fill=tk.X)
        
        tk.Label(blue_frame, text="模拟次数:").pack(anchor=tk.W)
        self.blue_simulations = tk.Entry(blue_frame)
        self.blue_simulations.insert(0, "10000")
        self.blue_simulations.pack(fill=tk.X)
        
        # 红方AI配置
        red_frame = tk.Frame(config_frame)
        red_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)
        
        tk.Label(red_frame, text="红方AI", font=("Arial", 11, "bold"), fg="red").pack()
        
        tk.Label(red_frame, text="难度:").pack(anchor=tk.W)
        self.red_difficulty = tk.Scale(red_frame, from_=3, to=5, orient=tk.HORIZONTAL)
        self.red_difficulty.set(4)
        self.red_difficulty.pack(fill=tk.X)
        
        tk.Label(red_frame, text="模拟次数:").pack(anchor=tk.W)
        self.red_simulations = tk.Entry(red_frame)
        self.red_simulations.insert(0, "10000")
        self.red_simulations.pack(fill=tk.X)
        
        # 对战控制区域
        control_frame = tk.LabelFrame(main_frame, text="对战控制", font=("Arial", 12))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 对战场数
        games_frame = tk.Frame(control_frame)
        games_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(games_frame, text="对战场数:").pack(side=tk.LEFT)
        self.num_games = tk.Entry(games_frame, width=10)
        self.num_games.insert(0, "100")
        self.num_games.pack(side=tk.LEFT, padx=(5, 20))
        
        tk.Label(games_frame, text="并行线程:").pack(side=tk.LEFT)
        self.max_workers = tk.Entry(games_frame, width=10)
        self.max_workers.insert(0, "4")
        self.max_workers.pack(side=tk.LEFT, padx=5)
        
        # 按钮区域
        button_frame = tk.Frame(control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_button = tk.Button(button_frame, text="开始对战", 
                                     command=self.start_battle,
                                     bg="#4CAF50", fg="white", font=("Arial", 12))
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.tournament_button = tk.Button(button_frame, text="锦标赛模式",
                                          command=self.start_tournament,
                                          bg="#2196F3", fg="white", font=("Arial", 12))
        self.tournament_button.pack(side=tk.LEFT, padx=5)
        
        self.collect_data_button = tk.Button(button_frame, text="收集训练数据",
                                            command=self.collect_training_data,
                                            bg="#FF9800", fg="white", font=("Arial", 12))
        self.collect_data_button.pack(side=tk.LEFT, padx=5)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='determinate')
        self.progress.pack(fill=tk.X, padx=5, pady=5)
        
        # 结果显示区域
        result_frame = tk.LabelFrame(main_frame, text="对战结果", font=("Arial", 12))
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 统计信息
        stats_frame = tk.Frame(result_frame)
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=8, font=("Consolas", 10))
        stats_scrollbar = tk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 详细结果
        details_frame = tk.Frame(result_frame)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.details_text = tk.Text(details_frame, font=("Consolas", 9))
        details_scrollbar = tk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=details_scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def start_battle(self):
        """开始对战"""
        import tkinter as tk
        try:
            # 获取配置
            blue_ai = self.battle_system.create_ai_player(
                "蓝方AI", 1, int(self.blue_difficulty.get()),
                custom_simulations=int(self.blue_simulations.get())
            )
            red_ai = self.battle_system.create_ai_player(
                "红方AI", -1, int(self.red_difficulty.get()),
                custom_simulations=int(self.red_simulations.get())
            )
            
            num_games = int(self.num_games.get())
            max_workers = int(self.max_workers.get())
            
            self.start_button.config(state=tk.DISABLED)
            self.progress['value'] = 0
            self.progress['maximum'] = num_games
            
            def progress_callback(completed, total):
                _ = total  # Mark parameter as used
                self.progress['value'] = completed
                self.root.update()
            
            def battle_thread():
                results = self.battle_system.batch_battle(
                    blue_ai, red_ai, num_games,
                    parallel=True, max_workers=max_workers,
                    progress_callback=progress_callback
                )
                
                # 更新UI
                self.root.after(0, lambda: self.update_results(results))
                self.root.after(0, lambda: self.start_button.config(state=tk.NORMAL))
            
            threading.Thread(target=battle_thread, daemon=True).start()
            
        except ValueError as e:
            import tkinter.messagebox as messagebox
            messagebox.showerror("参数错误", f"请检查输入参数: {e}")
    
    def start_tournament(self):
        """开始锦标赛"""
        # 创建锦标赛配置对话框
        TournamentDialog(self.root, self.battle_system, self.update_results)
    
    def collect_training_data(self):
        """收集训练数据"""
        from tkinter import simpledialog, messagebox
        
        num_games = simpledialog.askinteger("训练数据", "收集多少场游戏数据？", initialvalue=1000)
        if num_games:
            def collect_thread():
                try:
                    training_data = self.battle_system.collect_training_data(num_games)
                    self.root.after(0, lambda: messagebox.showinfo("完成", f"已收集 {len(training_data)} 个训练样本"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"数据收集失败: {e}"))
            
            threading.Thread(target=collect_thread, daemon=True).start()
    
    def update_results(self, results: List[GameResult]):
        """更新结果显示"""
        # 清空之前的结果
        import tkinter as tk
        self.stats_text.delete(1.0, tk.END)
        self.details_text.delete(1.0, tk.END)
        
        # 统计信息
        stats = self.battle_system.get_statistics()
        stats_text = f"""
对战统计:
总场数: {stats['total_games']}
蓝方胜利: {stats['blue_wins']} ({stats['blue_win_rate']:.2%})
红方胜利: {stats['red_wins']} ({stats['red_win_rate']:.2%})
平局: {stats['draws']} ({stats['draw_rate']:.2%})
平均回合数: {stats['average_game_length']:.1f}
平均思考时间: {stats['average_thinking_time']:.2f}秒
"""
        self.stats_text.insert(tk.END, stats_text)
        
        # 详细结果
        for i, result in enumerate(results[-50:]):  # 只显示最近50场
            winner_text = "蓝方获胜" if result.winner == 1 else "红方获胜" if result.winner == -1 else "平局"
            detail_text = f"第{i+1}场: {winner_text}, {result.total_moves}回合, {result.game_duration:.1f}秒\n"
            self.details_text.insert(tk.END, detail_text)
    
    def run(self):
        """运行界面"""
        self.root.mainloop()


class TournamentDialog:
    """锦标赛配置对话框"""
    
    def __init__(self, parent, battle_system, result_callback):
        import tkinter as tk
        from tkinter import ttk
        
        self.parent = parent
        self.battle_system = battle_system
        self.result_callback = result_callback
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("锦标赛配置")
        self.dialog.geometry("500x400")
        self.dialog.grab_set()
        
        self.ai_configs = []
        self.setup_dialog()
    
    def setup_dialog(self):
        """设置对话框"""
        import tkinter as tk
        from tkinter import ttk
        
        # AI列表
        list_frame = tk.LabelFrame(self.dialog, text="参赛AI")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.ai_listbox = tk.Listbox(list_frame)
        self.ai_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 添加AI按钮
        button_frame = tk.Frame(list_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="添加AI", command=self.add_ai).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="删除AI", command=self.remove_ai).pack(side=tk.LEFT, padx=5)
        
        # 预设一些AI
        default_ais = [
            {'name': 'Easy_AI', 'difficulty': 3, 'simulations': 1000},
            {'name': 'Medium_AI', 'difficulty': 4, 'simulations': 5000},
            {'name': 'Hard_AI', 'difficulty': 5, 'simulations': 20000},
        ]
        
        for ai_config in default_ais:
            self.ai_configs.append(ai_config)
            self.ai_listbox.insert(tk.END, f"{ai_config['name']} (难度{ai_config['difficulty']}, {ai_config['simulations']}次模拟)")
        
        # 对战设置
        settings_frame = tk.LabelFrame(self.dialog, text="锦标赛设置")
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(settings_frame, text="每对AI对战场数:").pack(anchor=tk.W, padx=5)
        self.games_per_match = tk.Entry(settings_frame)
        self.games_per_match.insert(0, "50")
        self.games_per_match.pack(fill=tk.X, padx=5, pady=2)
        
        # 开始按钮
        tk.Button(self.dialog, text="开始锦标赛", command=self.start_tournament,
                 bg="#4CAF50", fg="white", font=("Arial", 12)).pack(pady=10)
    
    def add_ai(self):
        """添加AI"""
        AddAIDialog(self.dialog, self.add_ai_callback)
    
    def add_ai_callback(self, ai_config):
        """添加AI回调"""
        import tkinter as tk
        self.ai_configs.append(ai_config)
        self.ai_listbox.insert(tk.END, f"{ai_config['name']} (难度{ai_config['difficulty']}, {ai_config['simulations']}次模拟)")
    
    def remove_ai(self):
        """删除选中的AI"""
        selection = self.ai_listbox.curselection()
        if selection:
            idx = selection[0]
            self.ai_listbox.delete(idx)
            del self.ai_configs[idx]
    
    def start_tournament(self):
        """开始锦标赛"""
        
        if len(self.ai_configs) < 2:
            import tkinter.messagebox as messagebox
            messagebox.showerror("错误", "至少需要2个AI参加锦标赛")
            return
        
        games_per_match = int(self.games_per_match.get())
        
        def tournament_thread():
            results = self.battle_system.tournament(self.ai_configs, games_per_match)
            # 这里可以调用结果回调来显示锦标赛结果
        
        import threading
        threading.Thread(target=tournament_thread, daemon=True).start()
        self.dialog.destroy()


class AddAIDialog:
    """添加AI对话框"""
    
    def __init__(self, parent, callback):
        import tkinter as tk
        
        self.callback = callback
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("添加AI")
        self.dialog.geometry("300x250")
        self.dialog.grab_set()
        
        self.setup_dialog()
    
    def setup_dialog(self):
        """设置对话框"""
        import tkinter as tk
        
        tk.Label(self.dialog, text="AI名称:").pack(anchor=tk.W, padx=10, pady=5)
        self.name_entry = tk.Entry(self.dialog)
        self.name_entry.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(self.dialog, text="难度等级:").pack(anchor=tk.W, padx=10, pady=5)
        self.difficulty_scale = tk.Scale(self.dialog, from_=3, to=5, orient=tk.HORIZONTAL)
        self.difficulty_scale.set(4)
        self.difficulty_scale.pack(fill=tk.X, padx=10, pady=2)
        
        tk.Label(self.dialog, text="模拟次数:").pack(anchor=tk.W, padx=10, pady=5)
        self.simulations_entry = tk.Entry(self.dialog)
        self.simulations_entry.insert(0, "10000")
        self.simulations_entry.pack(fill=tk.X, padx=10, pady=2)
        
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="确定", command=self.apply).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def apply(self):
        """应用配置"""
        ai_config = {
            'name': self.name_entry.get() or f"AI_{random.randint(1000, 9999)}",
            'difficulty': self.difficulty_scale.get(),
            'simulations': int(self.simulations_entry.get() or 10000)
        }
        
        self.callback(ai_config)
        self.dialog.destroy()


def main():
    """主函数 - 演示机机对弈系统的使用"""
    print("爱因斯坦棋 AI对战系统")
    print("="*50)
    
    # 创建对战系统
    battle_system = AIBattleSystem()
    
    # 示例1: 简单对战
    print("\n1. 执行简单对战演示...")
    blue_ai = battle_system.create_ai_player("蓝方测试AI", 1, difficulty=3)
    red_ai = battle_system.create_ai_player("红方测试AI", -1, difficulty=3)
    
    result = battle_system.single_battle(blue_ai, red_ai, verbose=True)
    print(f"对战结果: {'蓝方获胜' if result.winner == 1 else '红方获胜' if result.winner == -1 else '平局'}")
    
    # 示例2: 批量对战
    print("\n2. 执行批量对战演示...")
    results = battle_system.batch_battle(blue_ai, red_ai, num_games=10, parallel=False)
    stats = battle_system.get_statistics()
    print(f"批量对战完成，蓝方胜率: {stats['blue_win_rate']:.2%}")
    
    # 启动图形界面（可选）
    import sys
    if "--gui" in sys.argv:
        print("\n3. 启动图形界面...")
        gui = BattleGUI(battle_system)
        gui.run()


if __name__ == "__main__":
    main()