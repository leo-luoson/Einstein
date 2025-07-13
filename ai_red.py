"""
红方PMCTS AI主程序 - 负责处理机人对战模式中的AI逻辑
基于概率启发的蒙特卡洛树搜索(PMCTS)算法
这个程序会被Java调用，读取JavaOut1.txt，输出JavaIn1.txt
"""

# 导入我们自己编写的模块
from core.game_engine import EinsteinGame
from core.pmcts import PMCTS  # 使用PMCTS算法替代原来的MCTS
from core.file_handler import FileHandler
from core.config import Config


class RedAI:
    """红方PMCTS AI类 - 封装所有红方AI的逻辑"""
    
    def __init__(self):
        """初始化红方PMCTS AI"""
        print("初始化红方PMCTS AI...")
        
        # 创建游戏引擎实例
        self.game = EinsteinGame()
        print("✓ 游戏引擎初始化完成")
        
        # 创建PMCTS搜索算法实例，使用论文中的参数设置
        self.pmcts = PMCTS(self.game, exploration_constant=Config.UCB_CONSTANT)
        print("✓ PMCTS算法初始化完成")
        
        # 红方玩家编号固定为-1
        self.player = -1
        print("✓ 红方PMCTS AI初始化完成")
    
    def get_best_move(self, board, die, difficulty):
        """
        使用PMCTS算法获取AI认为的最佳移动
        
        参数:
            board: 当前棋盘状态 (5x5数组)
            die: 骰子点数 (1-6)
            difficulty: 难度等级 (3-5)
            
        返回:
            新的棋盘状态 (执行移动后的棋盘)
        """
        print(f"红方PMCTS AI开始分析局面...")
        print(f"当前棋盘状态:")
        print(board)
        
        # 根据难度等级确定PMCTS模拟次数
        num_simulations = Config.MCTS_SIMULATIONS.get(difficulty, 2000)
        print(f"难度等级: {difficulty}, PMCTS模拟次数: {num_simulations}")
        print(f"骰子点数: {die}")
        
        # 使用PMCTS算法搜索最佳移动
        # 与传统MCTS不同，PMCTS会考虑骰子的概率分布
        best_move = self.pmcts.search(board, die, self.player, num_simulations)
        
        if best_move is None:
            # 没有找到合法移动，返回原棋盘
            print("警告: 没有找到合法移动，返回原棋盘")
            return board
        
        # 执行最佳移动
        print(f"执行PMCTS选择的移动: ({best_move[0]},{best_move[1]}) -> ({best_move[2]},{best_move[3]})")
        new_board = self.game.make_move(board, best_move)
        
        print("移动后棋盘:")
        print(new_board)
        
        return new_board


def main():
    """
    主函数 - 程序入口点
    这个函数被Java程序调用时执行
    """
    try:
        print("="*50)
        print("红方PMCTS AI程序启动")
        print("="*50)
        
        # 第1步: 读取Java程序传来的输入文件
        print("第1步: 读取输入文件...")
        difficulty, die, board = FileHandler.parse_input_file(Config.RED_INPUT_FILE)
        
        # 记录当前状况
        FileHandler.log_move_info("Red PMCTS", difficulty, die)
        
        # 第2步: 创建红方PMCTS AI并计算最佳移动
        print("第2步: PMCTS AI开始思考...")
        red_ai = RedAI()
        new_board = red_ai.get_best_move(board, die, difficulty)
        
        # 第3步: 将结果写入输出文件供Java程序读取
        print("第3步: 写入输出文件...")
        success = FileHandler.write_output_file(Config.RED_OUTPUT_FILE, new_board)
        
        if success:
            print("✓ 红方PMCTS AI移动完成")
        else:
            print("✗ 输出文件写入失败")
        
        print("="*50)
        
    except Exception as error:
        # 如果出现任何错误，输出错误信息
        print(f"红方PMCTS AI出现错误: {error}")
        
        # 尝试进行错误恢复：输出原始棋盘
        try:
            print("尝试错误恢复...")
            _, _, original_board = FileHandler.parse_input_file(Config.RED_INPUT_FILE)
            FileHandler.write_output_file(Config.RED_OUTPUT_FILE, original_board)
            print("✓ 错误恢复完成，输出原始棋盘")
        except:
            print("✗ 错误恢复失败")


# 当这个文件被直接运行时，执行main函数
if __name__ == "__main__":
    main()