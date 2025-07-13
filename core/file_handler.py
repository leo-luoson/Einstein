"""
文件处理模块 - 负责与Java程序的文件通信
支持PMCTS算法的文件输入输出处理
"""

import numpy as np
from typing import Tuple, List

class FileHandler:
    """文件输入输出处理类"""
    
    @staticmethod
    def parse_input_file(filename: str) -> Tuple[int, int, np.ndarray]:
        """
        解析Java程序传来的输入文件
        
        参数:
            filename: 输入文件名 (如 "JavaOut.txt")
            
        返回:
            difficulty: 难度等级 (3-5)
            die: 骰子点数 (1-6)  
            board: 5x5棋盘数组
        """
        try:
            # 打开文件并读取所有行
            with open(filename, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            # 解析第一行: "难度 骰子点数"
            first_line = lines[0].strip().split()  # 去除空白并分割
            difficulty = int(first_line[0])        # 转换为整数
            die = int(first_line[1])
            
            # 解析棋盘(第2-6行)
            board = []
            for i in range(1, 6):  # 从第2行开始,共5行
                # 将每行分割并转换为整数列表
                row = list(map(int, lines[i].strip().split()))
                board.append(row)
            
            # 转换为numpy数组便于操作
            board_array = np.array(board, dtype=int)
            
            print(f"成功读取文件 {filename}: 难度={difficulty}, 骰子={die}")
            return difficulty, die, board_array
            
        except Exception as error:
            # 发生错误时输出错误信息并返回默认值
            print(f"读取文件 {filename} 出错: {error}")
            # 返回默认的空棋盘
            default_board = np.zeros((5, 5), dtype=int)
            return 4, 1, default_board  # 默认难度4,骰子1
    
    @staticmethod
    def write_output_file(filename: str, board: np.ndarray) -> bool:
        """
        将AI决策结果写入输出文件供Java程序读取
        
        参数:
            filename: 输出文件名 (如 "JavaIn.txt")
            board: 5x5棋盘数组
            
        返回:
            bool: 是否写入成功
        """
        try:
            # 打开文件准备写入
            with open(filename, 'w', encoding='utf-8') as file:
                # 逐行写入棋盘状态
                for row in board:
                    # 将每行数字用空格连接并写入
                    line = ' '.join(map(str, row))
                    file.write(line + '\n')
            
            print(f"成功写入文件 {filename}")
            return True
            
        except Exception as error:
            print(f"写入文件 {filename} 出错: {error}")
            return False
    
    @staticmethod
    def log_move_info(player_name: str, difficulty: int, die: int):
        """
        记录移动信息到控制台
        支持PMCTS算法的日志记录
        
        参数:
            player_name: 玩家名称 ("Blue PMCTS"或"Red PMCTS")
            difficulty: 难度等级
            die: 骰子点数
        """
        import datetime
        # 获取当前时间
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        # 输出格式化的日志信息，标注使用PMCTS算法
        print(f"[{current_time}] {player_name} AI开始思考: 难度={difficulty}, 骰子={die}")
        print(f"[{current_time}] 使用概率启发的蒙特卡洛树搜索(PMCTS)算法")