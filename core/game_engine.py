"""
游戏引擎模块 - 实现爱因斯坦棋的所有规则
为PMCTS算法提供游戏状态管理和规则验证
"""

import numpy as np
from typing import List, Tuple, Optional
import random

class EinsteinGame:
    """
    爱因斯坦棋游戏规则引擎
    为PMCTS算法提供游戏状态转换和评估功能
    """
    
    def __init__(self):
        """初始化游戏引擎"""
        self.board_size = 5  # 棋盘大小5x5
    
    def get_legal_moves(self, board: np.ndarray, die: int, player: int) -> List[Tuple[int, int, int, int]]:
        """
        获取当前状态下的所有合法移动
        这是PMCTS算法选择阶段的核心函数
        
        参数:
            board: 5x5棋盘数组
            die: 骰子点数 (1-6) - PMCTS概率节点对应的事件
            player: 当前玩家 (1=蓝方, -1=红方)
            
        返回:
            合法移动列表，每个移动是(起始x, 起始y, 目标x, 目标y)
        """
        moves = []
        
        # 第1步: 根据骰子点数找到可以移动的棋子(可能有多个)
        movable_pieces = self._find_movable_pieces(board, die, player)
        if not movable_pieces:
            return moves  # 没有可移动的棋子
        
        # 第2步: 为每个可移动的棋子生成所有合法移动
        for piece in movable_pieces:
            # 找到这个棋子在棋盘上的位置
            piece_position = self._find_piece_position(board, piece)
            if piece_position is None:
                continue  # 棋子不在棋盘上，跳过
            
            from_x, from_y = piece_position
            
            # 获取这个玩家可以移动的方向
            directions = self._get_movement_directions(player)
            
            # 检查每个方向是否可以移动
            for dx, dy in directions:
                to_x = from_x + dx  # 计算目标位置
                to_y = from_y + dy
                
                # 检查目标位置是否在棋盘内
                if self._is_position_valid(to_x, to_y):
                    moves.append((from_x, from_y, to_x, to_y))
        
        return moves
    
    def make_move(self, board: np.ndarray, move: Tuple[int, int, int, int]) -> np.ndarray:
        """
        执行一个移动，返回新的棋盘状态
        PMCTS算法扩展阶段使用此函数生成新状态
        
        参数:
            board: 当前棋盘状态
            move: 移动 (起始x, 起始y, 目标x, 目标y)
            
        返回:
            新的棋盘状态
        """
        # 复制棋盘以避免修改原棋盘
        new_board = board.copy()
        
        from_x, from_y, to_x, to_y = move
        
        # 获取要移动的棋子
        piece = new_board[from_x, from_y]
        
        # 清空起始位置
        new_board[from_x, from_y] = 0
        
        # 将棋子放到目标位置(可能吃掉对方棋子)
        new_board[to_x, to_y] = piece
        
        return new_board
    
    def is_game_over(self, board: np.ndarray) -> bool:
        """
        检查游戏是否结束
        PMCTS算法模拟阶段使用此函数判断终止条件
        
        参数:
            board: 棋盘状态
            
        返回:
            bool: 游戏是否结束
        """
        # 胜利条件1: 红方棋子到达右下角(4,4)
        if 1 <= board[4, 4] <= 6:
            return True
        
        # 胜利条件2: 蓝方棋子到达左上角(0,0)  
        if 7 <= board[0, 0] <= 12:
            return True
        
        # 胜利条件3: 一方棋子全部被吃光
        red_mask = (board >= 1) & (board <= 6)
        blue_mask = (board >= 7) & (board <= 12)
        red_count = int(np.sum(red_mask))    # 统计红方棋子
        blue_count = int(np.sum(blue_mask))  # 统计蓝方棋子
        
        if red_count == 0 or blue_count == 0:
            return True
        
        return False
    
    def get_winner(self, board: np.ndarray) -> int:
        """
        获取游戏获胜方
        PMCTS算法回传阶段使用此函数确定胜负
        
        参数:
            board: 棋盘状态
            
        返回:
            1: 蓝方获胜, -1: 红方获胜, 0: 游戏未结束或平局
        """
        # 红方到达目标
        if 1 <= board[4, 4] <= 6:
            return -1  # 红方获胜
        
        # 蓝方到达目标
        if 7 <= board[0, 0] <= 12:
            return 1   # 蓝方获胜
        
        # 统计棋子数量
        red_mask = (board >= 1) & (board <= 6)
        blue_mask = (board >= 7) & (board <= 12)
        red_count = int(np.sum(red_mask))
        blue_count = int(np.sum(blue_mask))
        
        if red_count == 0:
            return 1   # 红方棋子被吃光，蓝方获胜
        if blue_count == 0:
            return -1  # 蓝方棋子被吃光，红方获胜
        
        return 0  # 游戏未结束
    
    def evaluate_position(self, board: np.ndarray, player: int) -> float:
        """
        简单的位置评估函数
        PMCTS算法模拟阶段用于评估非终局状态
        
        参数:
            board: 棋盘状态
            player: 评估的玩家视角
            
        返回:
            评估分数，正数表示对该玩家有利
        """
        score = 0.0
        
        # 棋子数量优势
        red_mask = (board >= 1) & (board <= 6)
        blue_mask = (board >= 7) & (board <= 12)
        red_count = int(np.sum(red_mask))
        blue_count = int(np.sum(blue_mask))
        
        if player == 1:  # 蓝方视角
            score += (blue_count - red_count) * 10
        else:  # 红方视角
            score += (red_count - blue_count) * 10
        
        # 位置优势(越接近目标越好)
        for i in range(5):
            for j in range(5):
                piece = board[i, j]
                if 1 <= piece <= 6:  # 红方棋子
                    # 距离右下角(4,4)越近越好
                    distance_to_goal = abs(4-i) + abs(4-j)
                    position_value = 10 - distance_to_goal
                    if player == -1:  # 红方视角
                        score += position_value
                    else:  # 蓝方视角
                        score -= position_value
                        
                elif 7 <= piece <= 12:  # 蓝方棋子
                    # 距离左上角(0,0)越近越好
                    distance_to_goal = abs(0-i) + abs(0-j)
                    position_value = 10 - distance_to_goal
                    if player == 1:  # 蓝方视角
                        score += position_value
                    else:  # 红方视角
                        score -= position_value
        
        return score
    
    def check_immediate_win(self, board: np.ndarray, die: int, player: int) -> Optional[Tuple[int, int, int, int]]:
        """
        检查是否有立即获胜的移动
        用于AI优先选择获胜步骤
        
        参数:
            board: 当前棋盘状态
            die: 骰子点数
            player: 当前玩家
            
        返回:
            获胜移动，如果没有则返回None
        """
        legal_moves = self.get_legal_moves(board, die, player)
        
        for move in legal_moves:
            # 模拟执行这个移动
            new_board = self.make_move(board, move)
            
            # 检查是否获胜
            if self.is_game_over(new_board) and self.get_winner(new_board) == player:
                print(f"发现获胜移动: {move}")
                return move
        
        return None
    
    # === 私有辅助方法 ===
    
    def _find_movable_pieces(self, board: np.ndarray, die: int, player: int) -> List[int]:
        """
        根据骰子点数和玩家找到所有可以移动的棋子
        爱因斯坦棋规则: 可以移动骰子对应编号的棋子，如果该棋子不存在，
        则移动编号最接近的存活棋子(最多2个)
        
        参数:
            board: 棋盘状态
            die: 骰子点数 (1-6)
            player: 玩家 (1=蓝方, -1=红方)
            
        返回:
            可移动的棋子编号列表
        """
        movable_pieces = []
        
        if player == 1:  # 蓝方 (棋子编号7-12)
            target_piece = die + 6  # 蓝方1号棋子编号是7
            piece_range = range(7, 13)
        else:  # 红方 (棋子编号1-6)
            target_piece = die       # 红方1号棋子编号是1
            piece_range = range(1, 7)
        
        # 获取当前玩家存活的棋子编号
        alive_pieces = set()
        for piece_num in piece_range:
            if self._piece_exists_on_board(board, piece_num):
                alive_pieces.add(piece_num)
        
        # 规则1：如果骰子点数对应的棋子存在，直接移动
        if target_piece in alive_pieces:
            movable_pieces.append(target_piece)
            return movable_pieces
        
        # 规则2：如果该棋子不存在，找逻辑相邻的棋子
        
        # 向上找：比target_piece大的最小存在棋子
        upper_candidate = None
        for piece_num in range(target_piece + 1, max(piece_range) + 1):
            if piece_num in alive_pieces:
                upper_candidate = piece_num
                break  # 找到第一个（最小的）就停止
        
        # 向下找：比target_piece小的最大存在棋子
        lower_candidate = None
        for piece_num in range(target_piece - 1, min(piece_range) - 1, -1):
            if piece_num in alive_pieces:
                lower_candidate = piece_num
                break  # 找到第一个（最大的）就停止
        
        # 添加找到的候选棋子
        if upper_candidate is not None:
            movable_pieces.append(upper_candidate)
        
        if lower_candidate is not None:
            movable_pieces.append(lower_candidate)
        
        return movable_pieces
    
    def _find_piece_position(self, board: np.ndarray, piece: int) -> Optional[Tuple[int, int]]:
        """找到指定棋子在棋盘上的位置"""
        positions = np.where(board == piece)  # 查找棋子位置
        if len(positions[0]) > 0:
            return (int(positions[0][0]), int(positions[1][0]))  # 返回第一个找到的位置
        return None
    
    def _get_movement_directions(self, player: int) -> List[Tuple[int, int]]:
        """
        获取玩家的移动方向
        红方只能向右下方向移动，蓝方只能向左上方向移动
        """
        if player == 1:  # 蓝方向左上移动
            return [(-1, 0), (0, -1), (-1, -1)]  # 上、左、左上
        else:  # 红方向右下移动
            return [(1, 0), (0, 1), (1, 1)]      # 下、右、右下
    
    def _is_position_valid(self, x: int, y: int) -> bool:
        """检查位置是否在棋盘范围内"""
        return 0 <= x < self.board_size and 0 <= y < self.board_size
    
    def _piece_exists_on_board(self, board: np.ndarray, piece: int) -> bool:
        """检查指定棋子是否还在棋盘上"""
        return bool(np.any(board == piece))