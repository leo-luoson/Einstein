"""
配置文件 - 存储所有PMCTS AI参数设置
基于论文"概率启发的并行蒙特卡洛树搜索算法"实现
"""

class Config:
    """PMCTS AI配置类 - 集中管理所有参数"""
    
    # 游戏基本参数
    BOARD_SIZE = 5           # 棋盘大小 5x5
    MAX_PIECES = 6           # 每方最大棋子数量
    
    # PMCTS算法参数 - 基于论文实验设置
    MCTS_SIMULATIONS = {     # 不同难度的模拟次数
        3: 1000,            # 简单难度: 1000次模拟
        4: 10000,            # 普通难度: 10000次模拟  
        5: 50000             # 困难难度: 50000次模拟
    }
    
    # PMCTS特有参数
    UCB_CONSTANT = 1.0       # UCB公式中的探索常数，论文中使用cof=1
    MAX_GAME_MOVES = 200     # 最大游戏步数(防止无限循环)
    
    # 概率节点参数 - 论文3.2.1节
    DICE_FACES = 6           # 骰子面数 (1-6)
    DICE_PROBABILITY = 1.0/6 # 每个骰子面的概率 (均匀分布)
    
    # 文件路径配置
    BLUE_INPUT_FILE = "test_files/JavaOut.txt"    # 蓝方AI输入文件
    BLUE_OUTPUT_FILE ="test_files/JavaIn.txt"    # 蓝方AI输出文件
    RED_INPUT_FILE = "test_files/JavaOut1.txt"    # 红方AI输入文件
    RED_OUTPUT_FILE = "test_files/JavaIn1.txt"    # 红方AI输出文件
    
    # 调试开关
    DEBUG_MODE = True        # 是否输出调试信息
    LOG_MOVES = True         # 是否记录移动日志