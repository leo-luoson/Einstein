"""
Core模块初始化文件
这个文件让Python把core目录识别为一个包(package)
"""

# 导入主要的类，方便其他模块使用
from .game_engine import EinsteinGame
from .pmcts import ProbabilityNode, MCTSNode, PMCTS
from .file_handler import FileHandler
from .config import Config

# 定义包的版本和作者信息
__version__ = "1.0.0"
__author__ = "Einstein Chess AI Team"

# 定义当使用 from core import * 时导入的内容
__all__ = [
    'EinsteinGame',   # 游戏引擎
    'PMCTS',          # 概率蒙特卡洛树搜索算法
    'MCTSNode',      # MCTS节点
    'FileHandler',   # 文件处理
    'Config'         # 配置
]