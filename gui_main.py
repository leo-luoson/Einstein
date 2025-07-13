"""
爱因斯坦棋双模式GUI - 支持人机对弈和机人对弈
人机对弈: 人类(红方) vs AI(蓝方) - ai_blue.py, JavaOut.txt/JavaIn.txt
机人对弈: AI(红方) vs 人类(蓝方) - ai_red.py, JavaOut1.txt/JavaIn1.txt
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import numpy as np
import threading
import time
import os
import subprocess
import json
import sys
import random
from datetime import datetime
from typing import Optional, Tuple, List, Dict

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 导入核心模块
try:
    from core.game_engine import EinsteinGame
    from core.file_handler import FileHandler
    from core.config import Config
except ImportError as e:
    print(f"导入核心模块失败: {e}")
    print("请确保core模块在正确的位置")
    sys.exit(1)

class DualModeEinsteinGUI:
    """支持双模式的爱因斯坦棋GUI"""
    
    def __init__(self):
        """初始化GUI"""
        self.root = tk.Tk()
        self.root.title("爱因斯坦棋 - 双模式对弈系统")
        self.root.geometry("1100x750")
        self.root.configure(bg="#f5f5f5")
        
        # 游戏核心
        self.game = EinsteinGame()
        self.board = np.zeros((5, 5), dtype=int)
        
        # 游戏模式配置
        self.game_mode = "human_vs_ai"  # "human_vs_ai" 或 "ai_vs_human"
        self.human_player = 1  # 1=红方, -1=蓝方
        self.ai_player = -1    # 与人类相对
        
        # 游戏状态
        self.current_player = 1  # 总是红方先手
        self.current_die = 1
        self.game_running = False
        self.selected_piece = None
        self.legal_moves = []
        self.move_history = []
        self.game_record = {"game_info": {}, "moves": []}
        
        # 难度设置
        self.difficulty_level = 4
        
        # UI组件
        self.canvas = None
        self.dice_entry = None
        self.status_label = None
        self.history_text = None
        self.player_label = None
        self.mode_label = None
        
        # 初始化
        self.setup_ui()
        self.reset_game()
        
    def setup_ui(self):
        """设置用户界面"""
        # 菜单栏
        self.setup_menu_bar()
        
        # 主框架
        main_frame = tk.Frame(self.root, bg="#f5f5f5")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 三列布局
        self.setup_control_panel(main_frame)
        self.setup_board_area(main_frame)
        self.setup_info_panel(main_frame)
        
        # 状态栏
        self.setup_status_bar()
        
    def setup_menu_bar(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="保存棋谱", command=self.save_game_record)
        file_menu.add_command(label="加载棋谱", command=self.load_game_record)
        file_menu.add_separator()
        file_menu.add_command(label="导出棋盘", command=self.export_board)
        file_menu.add_command(label="导入棋盘", command=self.import_board)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_game)
        
        # 游戏菜单
        game_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="游戏", menu=game_menu)
        game_menu.add_command(label="新游戏", command=self.new_game)
        game_menu.add_command(label="重置棋盘", command=self.reset_game)
        game_menu.add_command(label="悔棋", command=self.undo_move)
        game_menu.add_separator()
        game_menu.add_command(label="切换模式", command=self.switch_game_mode)
        game_menu.add_command(label="设置难度", command=self.set_difficulty)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="游戏规则", command=self.show_rules)
        help_menu.add_command(label="关于", command=self.show_about)
        
    def setup_control_panel(self, parent):
        """设置左侧控制面板"""
        control_frame = tk.LabelFrame(parent, text="游戏控制", font=("Arial", 12, "bold"), 
                                     bg="#e8e8e8", relief=tk.GROOVE, bd=2)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 游戏模式选择
        mode_frame = tk.LabelFrame(control_frame, text="游戏模式", font=("Arial", 11), bg="#e8e8e8")
        mode_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.mode_var = tk.StringVar(value="human_vs_ai")
        
        tk.Radiobutton(mode_frame, text="人机对弈 (人类红方)", variable=self.mode_var,
                      value="human_vs_ai", bg="#e8e8e8", command=self.on_mode_change).pack(anchor=tk.W, padx=5)
        tk.Radiobutton(mode_frame, text="机人对弈 (人类蓝方)", variable=self.mode_var,
                      value="ai_vs_human", bg="#e8e8e8", command=self.on_mode_change).pack(anchor=tk.W, padx=5)
        
        # 当前模式显示
        self.mode_label = tk.Label(mode_frame, text="人类: 红方, AI: 蓝方", 
                                  font=("Arial", 10, "bold"), bg="#e8e8e8", fg="blue")
        self.mode_label.pack(pady=5)
        
        # 骰子输入区域
        dice_frame = tk.LabelFrame(control_frame, text="骰子输入", font=("Arial", 11), bg="#e8e8e8")
        dice_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(dice_frame, text="骰子点数 (1-6):", bg="#e8e8e8").pack(anchor=tk.W, padx=5, pady=2)
        
        dice_input_frame = tk.Frame(dice_frame, bg="#e8e8e8")
        dice_input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.dice_entry = tk.Entry(dice_input_frame, width=8, font=("Arial", 14), justify=tk.CENTER)
        self.dice_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.dice_entry.bind('<Return>', lambda e: self.confirm_dice())
        
        self.confirm_dice_btn = tk.Button(dice_input_frame, text="确认", command=self.confirm_dice,
                                         bg="#4CAF50", fg="white", font=("Arial", 10))
        self.confirm_dice_btn.pack(side=tk.LEFT)
        
        tk.Button(dice_frame, text="随机骰子", command=self.random_dice,
                 bg="#FF9800", fg="white", font=("Arial", 10)).pack(fill=tk.X, padx=5, pady=2)
        
        # 游戏控制按钮
        button_frame = tk.LabelFrame(control_frame, text="游戏操作", font=("Arial", 11), bg="#e8e8e8")
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        buttons = [
            ("新游戏", self.new_game, "#4CAF50"),
            ("重置", self.reset_game, "#2196F3"),
            ("切换模式", self.switch_game_mode, "#9C27B0"),
            ("悔棋", self.undo_move, "#FF9800"),
            ("保存棋谱", self.save_game_record, "#795548"),
            ("加载棋谱", self.load_game_record, "#607D8B")
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                           bg=color, fg="white", font=("Arial", 10))
            btn.pack(fill=tk.X, padx=5, pady=2)
        
        # 难度设置
        difficulty_frame = tk.LabelFrame(control_frame, text="AI难度", font=("Arial", 11), bg="#e8e8e8")
        difficulty_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.difficulty_var = tk.IntVar(value=4)
        difficulty_scale = tk.Scale(difficulty_frame, from_=3, to=5, orient=tk.HORIZONTAL,
                                   variable=self.difficulty_var, bg="#e8e8e8",
                                   command=self.on_difficulty_change)
        difficulty_scale.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(difficulty_frame, text="3=简单 4=中等 5=困难", 
                font=("Arial", 9), bg="#e8e8e8").pack()
        
    def setup_board_area(self, parent):
        """设置中间棋盘区域"""
        board_frame = tk.Frame(parent, bg="#f5f5f5")
        board_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = tk.Label(board_frame, text="爱因斯坦棋盘", 
                              font=("Arial", 16, "bold"), bg="#f5f5f5")
        title_label.pack(pady=10)
        
        # 当前玩家显示
        self.player_label = tk.Label(board_frame, text="当前玩家: 红方", 
                                    font=("Arial", 14, "bold"), fg="red", bg="#f5f5f5")
        self.player_label.pack(pady=5)
        
        # 棋盘画布
        canvas_frame = tk.Frame(board_frame, relief=tk.SUNKEN, bd=3)
        canvas_frame.pack(pady=10)
        
        self.canvas = tk.Canvas(canvas_frame, width=450, height=450, bg="white")
        self.canvas.pack()
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_board_click)
        self.canvas.bind("<Motion>", self.on_mouse_motion)
        
        # 当前骰子和模式显示
        info_frame = tk.Frame(board_frame, bg="#f5f5f5")
        info_frame.pack(pady=10)
        
        # 骰子显示
        dice_frame = tk.Frame(info_frame, bg="#f5f5f5")
        dice_frame.pack(side=tk.LEFT, padx=20)
        
        tk.Label(dice_frame, text="当前骰子:", font=("Arial", 12), bg="#f5f5f5").pack()
        self.dice_display = tk.Label(dice_frame, text="?", font=("Arial", 20, "bold"), 
                                    bg="white", relief=tk.RAISED, bd=3, width=3, height=1)
        self.dice_display.pack()
        
        # 模式显示
        mode_display_frame = tk.Frame(info_frame, bg="#f5f5f5")
        mode_display_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Label(mode_display_frame, text="当前模式:", font=("Arial", 12), bg="#f5f5f5").pack()
        self.mode_display = tk.Label(mode_display_frame, text="人机对弈", 
                                    font=("Arial", 12, "bold"), bg="#f5f5f5", fg="blue")
        self.mode_display.pack()
        
    def setup_info_panel(self, parent):
        """设置右侧信息面板"""
        info_frame = tk.LabelFrame(parent, text="游戏信息", font=("Arial", 12, "bold"), 
                                  bg="#e8e8e8", relief=tk.GROOVE, bd=2)
        info_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        
        # 游戏状态
        status_frame = tk.LabelFrame(info_frame, text="游戏状态", font=("Arial", 11), bg="#e8e8e8")
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.game_status_label = tk.Label(status_frame, text="等待开始", 
                                         font=("Arial", 12), bg="#e8e8e8")
        self.game_status_label.pack(pady=5)
        
        # 玩家信息
        player_info_frame = tk.LabelFrame(info_frame, text="玩家信息", font=("Arial", 11), bg="#e8e8e8")
        player_info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.red_player_label = tk.Label(player_info_frame, text="红方: 人类", 
                                        font=("Arial", 11), fg="red", bg="#e8e8e8")
        self.red_player_label.pack(anchor=tk.W, padx=5)
        
        self.blue_player_label = tk.Label(player_info_frame, text="蓝方: AI", 
                                         font=("Arial", 11), fg="blue", bg="#e8e8e8")
        self.blue_player_label.pack(anchor=tk.W, padx=5)
        
        # 棋子统计
        stats_frame = tk.LabelFrame(info_frame, text="棋子统计", font=("Arial", 11), bg="#e8e8e8")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.red_count_label = tk.Label(stats_frame, text="红方: 6", 
                                       font=("Arial", 11), fg="red", bg="#e8e8e8")
        self.red_count_label.pack(anchor=tk.W, padx=5)
        
        self.blue_count_label = tk.Label(stats_frame, text="蓝方: 6", 
                                        font=("Arial", 11), fg="blue", bg="#e8e8e8")
        self.blue_count_label.pack(anchor=tk.W, padx=5)
        
        # 移动历史
        history_frame = tk.LabelFrame(info_frame, text="移动历史", font=("Arial", 11), bg="#e8e8e8")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_frame = tk.Frame(history_frame, bg="#e8e8e8")
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.history_text = tk.Text(text_frame, width=25, height=12, font=("Consolas", 9),
                                   wrap=tk.WORD, state=tk.DISABLED)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=scrollbar.set)
        
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # AI状态
        ai_frame = tk.LabelFrame(info_frame, text="AI状态", font=("Arial", 11), bg="#e8e8e8")
        ai_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ai_status_label = tk.Label(ai_frame, text="待机", 
                                       font=("Arial", 11), bg="#e8e8e8")
        self.ai_status_label.pack(pady=5)
        
    def setup_status_bar(self):
        """设置状态栏"""
        self.status_label = tk.Label(self.root, text="准备就绪", 
                                    relief=tk.SUNKEN, anchor=tk.W, 
                                    font=("Arial", 10), bg="#e0e0e0")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_mode_change(self):
        """模式改变事件"""
        self.game_mode = self.mode_var.get()
        
        if self.game_mode == "human_vs_ai":
            self.human_player = 1   # 人类红方
            self.ai_player = -1     # AI蓝方
            if self.mode_label:
                self.mode_label.config(text="人类: 红方, AI: 蓝方")
            if self.mode_display:
                self.mode_display.config(text="人机对弈")
            if self.red_player_label:
                self.red_player_label.config(text="红方: 人类")
            if self.blue_player_label:
                self.blue_player_label.config(text="蓝方: AI")
        else:  # ai_vs_human
            self.human_player = -1  # 人类蓝方
            self.ai_player = 1      # AI红方
            if self.mode_label:
                self.mode_label.config(text="AI: 红方, 人类: 蓝方")
            if self.mode_display:
                self.mode_display.config(text="机人对弈")
            if self.red_player_label:
                self.red_player_label.config(text="红方: AI")
            if self.blue_player_label:
                self.blue_player_label.config(text="蓝方: 人类")
        
        # 如果游戏正在进行，询问是否重新开始
        if self.game_running:
            if messagebox.askyesno("模式切换", "切换模式将重新开始游戏，确定吗？"):
                self.new_game()
    
    def switch_game_mode(self):
        """切换游戏模式"""
        if self.game_mode == "human_vs_ai":
            self.mode_var.set("ai_vs_human")
        else:
            self.mode_var.set("human_vs_ai")
        self.on_mode_change()
    
    def draw_board(self):
        """绘制棋盘"""
        if not self.canvas:
            return
            
        self.canvas.delete("all")
        
        cell_size = 80
        margin = 25
        
        # 绘制棋盘网格
        for i in range(6):
            x = margin + i * cell_size
            self.canvas.create_line(x, margin, x, margin + 5 * cell_size, fill="black", width=2)
            y = margin + i * cell_size
            self.canvas.create_line(margin, y, margin + 5 * cell_size, y, fill="black", width=2)
        
        # 绘制格子背景
        for i in range(5):
            for j in range(5):
                x1 = margin + j * cell_size
                y1 = margin + i * cell_size
                x2 = x1 + cell_size
                y2 = y1 + cell_size
                
                color = "#F5DEB3" if (i + j) % 2 == 0 else "#DEB887"
                
                # 目标位置标记
                if i == 0 and j == 0:  # 蓝方目标
                    color = "#87CEEB"
                elif i == 4 and j == 4:  # 红方目标
                    color = "#FFB6C1"
                
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
        
        # 绘制坐标
        for i in range(5):
            y = margin + i * cell_size + cell_size // 2
            self.canvas.create_text(margin - 15, y, text=str(i), font=("Arial", 10))
            x = margin + i * cell_size + cell_size // 2
            self.canvas.create_text(x, margin - 15, text=str(i), font=("Arial", 10))
        
        # 绘制棋子
        for i in range(5):
            for j in range(5):
                piece = self.board[i, j]
                if piece != 0:
                    self.draw_piece(i, j, piece)
        
        # 高亮显示
        self.highlight_legal_moves()
        if self.selected_piece:
            self.highlight_selected_piece()
    
    def draw_piece(self, row: int, col: int, piece: int):
        """绘制棋子"""
        if not self.canvas:
            return
            
        cell_size = 80
        margin = 25
        
        x = margin + col * cell_size + cell_size // 2
        y = margin + row * cell_size + cell_size // 2
        radius = 28
        
        if 1 <= piece <= 6:  # 红方
            bg_color = "#FF6B6B"
            text_color = "white"
            text = str(piece)
            outline_color = "#D32F2F"
        else:  # 蓝方 (7-12)
            bg_color = "#42A5F5"
            text_color = "white"
            text = str(piece - 6)
            outline_color = "#1976D2"
        
        # 阴影
        self.canvas.create_oval(x - radius + 2, y - radius + 2, 
                               x + radius + 2, y + radius + 2,
                               fill="gray", outline="")
        
        # 棋子主体
        self.canvas.create_oval(x - radius, y - radius, x + radius, y + radius,
                               fill=bg_color, outline=outline_color, width=3,
                               tags=f"piece_{row}_{col}")
        
        # 编号
        self.canvas.create_text(x, y, text=text, font=("Arial", 16, "bold"),
                               fill=text_color, tags=f"piece_{row}_{col}")
    
    def highlight_legal_moves(self):
        """高亮合法移动"""
        if not self.legal_moves:
            return
        
        if not self.canvas:
            return
        cell_size = 80
        margin = 25
        
        for move in self.legal_moves:
            from_row, from_col, to_row, to_col = move
            
            x = margin + to_col * cell_size + cell_size // 2
            y = margin + to_row * cell_size + cell_size // 2
            
            # 绿色圆圈表示可移动
            self.canvas.create_oval(x - 35, y - 35, x + 35, y + 35,
                                   outline="green", width=4, fill="", tags="legal_move")
            
            # 红色标记吃子
            if self.board[to_row, to_col] != 0:
                self.canvas.create_oval(x - 30, y - 30, x + 30, y + 30,
                                       outline="red", width=3, fill="", tags="capture_move")
    
    def highlight_selected_piece(self):
        """高亮选中棋子"""
        if not self.selected_piece:
            return
        if not self.canvas:
            return
        row, col = self.selected_piece
        cell_size = 80
        margin = 25
        
        x = margin + col * cell_size + cell_size // 2
        y = margin + row * cell_size + cell_size // 2
        
        self.canvas.create_oval(x - 35, y - 35, x + 35, y + 35,
                               outline="yellow", width=4, fill="", tags="selected_piece")
    
    def on_board_click(self, event):
        """处理棋盘点击"""
        if not self.game_running or not self.is_human_turn():
            return
            
        cell_size = 80
        margin = 25
        
        col = (event.x - margin) // cell_size
        row = (event.y - margin) // cell_size
        
        if 0 <= row < 5 and 0 <= col < 5:
            self.handle_board_click(row, col)
    
    def on_mouse_motion(self, event):
        """鼠标移动提示"""
        if self.status_label is None:
            return
            
        cell_size = 80
        margin = 25
        
        col = (event.x - margin) // cell_size
        row = (event.y - margin) // cell_size
        
        if 0 <= row < 5 and 0 <= col < 5:
            piece = self.board[row, col]
            if piece != 0:
                piece_name = f"红{piece}" if 1 <= piece <= 6 else f"蓝{piece-6}"
                self.status_label.config(text=f"位置 ({row},{col}): {piece_name}")
            else:
                self.status_label.config(text=f"位置 ({row},{col}): 空格")
    
    def is_human_turn(self) -> bool:
        """检查是否是人类回合"""
        return self.current_player == self.human_player
    
    def is_ai_turn(self) -> bool:
        """检查是否是AI回合"""
        return self.current_player == self.ai_player
    
    def handle_board_click(self, row: int, col: int):
        """处理棋盘点击"""
        piece = self.board[row, col]
        
        if piece != 0 and self.is_player_piece(piece, self.current_player):
            # 选择己方棋子
            self.selected_piece = (row, col)
            self.legal_moves = self.get_piece_legal_moves(row, col)
            self.draw_board()
            
            if not self.legal_moves:
                messagebox.showinfo("提示", "该棋子无法移动")
                self.selected_piece = None
                
        elif self.selected_piece:
            # 移动到目标位置
            from_row, from_col = self.selected_piece
            move = (from_row, from_col, row, col)
            
            if move in self.legal_moves:
                self.execute_human_move(move)
            else:
                messagebox.showwarning("无效移动", "这不是一个合法的移动")
                
            self.selected_piece = None
            self.legal_moves = []
            self.draw_board()
    
    def is_player_piece(self, piece: int, player: int) -> bool:
        """检查棋子是否属于指定玩家"""
        if player == 1:  # 红方
            return 1 <= piece <= 6
        else:  # 蓝方
            return 7 <= piece <= 12
    
    def get_piece_legal_moves(self, row: int, col: int) -> List[Tuple[int, int, int, int]]:
        """获取棋子合法移动"""
        all_moves = self.game.get_legal_moves(self.board, self.current_die, self.current_player)
        return [move for move in all_moves if move[0] == row and move[1] == col]
    
    def confirm_dice(self):
        """确认骰子输入"""
        if not self.dice_entry or not self.status_label:
            return
            
        try:
            die_value = int(self.dice_entry.get())
            if 1 <= die_value <= 6:
                self.current_die = die_value
                if self.dice_display:
                    self.dice_display.config(text=str(die_value))
                self.dice_entry.delete(0, tk.END)
                
                if self.is_human_turn():
                    self.process_human_turn()
                    
                self.status_label.config(text=f"骰子: {die_value}, 请选择要移动的棋子")
            else:
                messagebox.showerror("错误", "骰子点数必须在1-6之间")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def random_dice(self):
        """随机生成骰子"""
        die_value = random.randint(1, 6)
        if not self.dice_entry:
            return
        self.dice_entry.delete(0, tk.END)
        self.dice_entry.insert(0, str(die_value))
        self.confirm_dice()
    
    def process_human_turn(self):
        """处理人类回合"""
        legal_moves = self.game.get_legal_moves(self.board, self.current_die, self.current_player)
        
        if not legal_moves:
            messagebox.showinfo("跳过回合", "没有合法移动，跳过回合")
            self.switch_to_ai_turn()
        else:
            self.legal_moves = legal_moves
            self.game_status_label.config(text="等待人类移动")
    
    def execute_human_move(self, move: Tuple[int, int, int, int]):
        """执行人类移动"""
        # 记录移动
        move_record = {
            "player": self.current_player,
            "die": self.current_die,
            "move": move,
            "board_before": self.board.copy().tolist()
        }
        
        # 执行移动
        self.board = self.game.make_move(self.board, move)
        move_record["board_after"] = self.board.copy().tolist()
        
        # 添加到历史
        self.move_history.append(move_record)
        self.game_record["moves"].append(move_record)
        
        # 更新显示
        self.add_move_to_history(move, self.current_player, self.current_die)
        self.update_game_display()
        
        # 检查游戏结束
        if self.game.is_game_over(self.board):
            self.handle_game_over()
        else:
            # 写入AI输入文件
            self.write_ai_input_file()
            # 切换到AI回合
            self.switch_to_ai_turn()
    
    def switch_to_ai_turn(self):
        """切换到AI回合"""
        self.current_player = self.ai_player
        if not self.player_label:
            return
        if self.current_player == 1:  # AI红方
            self.player_label.config(text="当前玩家: 红方 (AI)", fg="red")
        else:  # AI蓝方
            self.player_label.config(text="当前玩家: 蓝方 (AI)", fg="blue")
            
        self.game_status_label.config(text="AI思考中...")
        
        # 禁用人类操作
        self.confirm_dice_btn.config(state=tk.DISABLED)
        if not self.dice_entry:
            return
        self.dice_entry.config(state=tk.DISABLED)
        
        # 在新线程中执行AI
        threading.Thread(target=self.execute_ai_turn, daemon=True).start()
    
    def execute_ai_turn(self):
        """执行AI回合"""
        try:
            self.ai_status_label.config(text="AI分析中...")
            
            # 生成AI骰子
            ai_die = random.randint(1, 6)
            
            # 根据模式选择AI程序和文件
            if self.game_mode == "human_vs_ai":
                # 人机对弈: AI是蓝方，调用ai_blue.py
                ai_script = "ai_blue.py"
                input_file = Config.BLUE_INPUT_FILE   # JavaOut.txt
                output_file = Config.BLUE_OUTPUT_FILE # JavaIn.txt
            else:
                # 机人对弈: AI是红方，调用ai_red.py
                ai_script = "ai_red.py"
                input_file = Config.RED_INPUT_FILE    # JavaOut1.txt
                output_file = Config.RED_OUTPUT_FILE  # JavaIn1.txt
            
            # 确保目录存在
            os.makedirs(os.path.dirname(input_file), exist_ok=True)
            
            # 写入AI输入文件
            with open(input_file, 'w') as f:
                f.write(f"{self.difficulty_level} {ai_die}\n")
                for row in self.board:
                    f.write(' '.join(map(str, row)) + '\n')
            
            # 调用AI程序
            self.ai_status_label.config(text="调用AI程序...")
            result = subprocess.run(['python', ai_script], 
                                  capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                # 读取AI输出
                if os.path.exists(output_file):
                    new_board = self.read_ai_output(output_file)
                    
                    if new_board is not None:
                        # 找到AI移动
                        ai_move = self.find_move_difference(self.board, new_board)
                        
                        if ai_move:
                            # 记录AI移动
                            move_record = {
                                "player": self.current_player,
                                "die": ai_die,
                                "move": ai_move,
                                "board_before": self.board.copy().tolist(),
                                "board_after": new_board.tolist()
                            }
                            
                            self.board = new_board
                            self.move_history.append(move_record)
                            self.game_record["moves"].append(move_record)
                            
                            # 更新UI
                            self.root.after(0, lambda: self.finish_ai_turn(ai_move, ai_die))
                        else:
                            self.root.after(0, lambda: self.handle_ai_error("AI未执行有效移动"))
                    else:
                        self.root.after(0, lambda: self.handle_ai_error("读取AI输出失败"))
                else:
                    self.root.after(0, lambda: self.handle_ai_error("AI输出文件不存在"))
            else:
                error_msg = result.stderr or "AI程序执行失败"
                self.root.after(0, lambda: self.handle_ai_error(error_msg))
                
        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.handle_ai_error("AI响应超时"))
        except Exception as e:
            self.root.after(0, lambda: self.handle_ai_error(f"AI执行错误: {str(e)}"))
    
    def finish_ai_turn(self, ai_move: Tuple[int, int, int, int], ai_die: int):
        """完成AI回合"""
        # 更新显示
        self.current_die = ai_die
        self.dice_display.config(text=str(ai_die))
        self.add_move_to_history(ai_move, self.current_player, ai_die)
        self.update_game_display()
        
        self.ai_status_label.config(text="AI移动完成")
        
        # 检查游戏结束
        if self.game.is_game_over(self.board):
            self.handle_game_over()
        else:
            # 切换回人类回合
            self.switch_to_human_turn()
    
    def switch_to_human_turn(self):
        """切换到人类回合"""
        self.current_player = self.human_player
        if not self.player_label:
            return
        if self.current_player == 1:  # 人类红方
            self.player_label.config(text="当前玩家: 红方 (人类)", fg="red")
        else:  # 人类蓝方
            self.player_label.config(text="当前玩家: 蓝方 (人类)", fg="blue")
            
        self.game_status_label.config(text="等待人类输入骰子")
        
        # 启用人类操作
        self.confirm_dice_btn.config(state=tk.NORMAL)
        if not self.dice_entry:
            return
        self.dice_entry.config(state=tk.NORMAL)
        self.dice_entry.focus()
        if not self.status_label:
            return
        self.status_label.config(text="请输入骰子点数")
    
    def handle_ai_error(self, error_msg: str):
        """处理AI错误"""
        self.ai_status_label.config(text="AI错误")
        messagebox.showerror("AI错误", f"AI执行失败: {error_msg}")
        
        # 恢复人类回合
        self.switch_to_human_turn()
    
    def write_ai_input_file(self):
        """写入AI输入文件"""
        try:
            # 根据模式选择输入文件
            if self.game_mode == "human_vs_ai":
                # 人机对弈: 人类走完后给蓝方AI
                input_file = Config.BLUE_INPUT_FILE  # JavaOut.txt
            else:
                # 机人对弈: 人类走完后给红方AI
                input_file = Config.RED_INPUT_FILE   # JavaOut1.txt
            
            os.makedirs(os.path.dirname(input_file), exist_ok=True)
            
            with open(input_file, 'w') as f:
                f.write(f"{self.difficulty_level} 0\n")  # 骰子由AI生成
                for row in self.board:
                    f.write(' '.join(map(str, row)) + '\n')
                    
        except Exception as e:
            print(f"写入AI输入文件错误: {e}")
    
    def read_ai_output(self, output_file: str) -> Optional[np.ndarray]:
        """读取AI输出文件"""
        try:
            with open(output_file, 'r') as f:
                lines = f.readlines()
            
            board = []
            for line in lines:
                row = list(map(int, line.strip().split()))
                if len(row) == 5:
                    board.append(row)
            
            if len(board) == 5:
                return np.array(board, dtype=int)
            else:
                return None
                
        except Exception as e:
            print(f"读取AI输出错误: {e}")
            return None
    
    def find_move_difference(self, old_board: np.ndarray, new_board: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """找到棋盘变化对应的移动"""
        diff = old_board - new_board
        
        disappeared = np.where(diff > 0)
        appeared = np.where(diff < 0)
        
        if len(disappeared[0]) == 1 and len(appeared[0]) == 1:
            from_row, from_col = disappeared[0][0], disappeared[1][0]
            to_row, to_col = appeared[0][0], appeared[1][0]
            return (from_row, from_col, to_row, to_col)
        
        return None
    
    def add_move_to_history(self, move: Tuple[int, int, int, int], player: int, die: int):
        """添加移动到历史记录"""
        from_row, from_col, to_row, to_col = move
        
        if player == 1:
            player_name = "红方"
            if self.game_mode == "human_vs_ai":
                player_type = "(人类)"
            else:
                player_type = "(AI)"
        else:
            player_name = "蓝方"
            if self.game_mode == "human_vs_ai":
                player_type = "(AI)"
            else:
                player_type = "(人类)"
        
        move_text = f"{len(self.move_history)}. {player_name}{player_type}(骰子{die}): ({from_row},{from_col})→({to_row},{to_col})\n"
        if not self.history_text:
            return
        self.history_text.config(state=tk.NORMAL)
        self.history_text.insert(tk.END, move_text)
        self.history_text.see(tk.END)
        self.history_text.config(state=tk.DISABLED)
    
    def update_game_display(self):
        """更新游戏显示"""
        self.draw_board()
        self.update_piece_count()
    
    def update_piece_count(self):
        """更新棋子统计"""
        red_count = int(np.sum((self.board >= 1) & (self.board <= 6)))
        blue_count = int(np.sum((self.board >= 7) & (self.board <= 12)))
        
        self.red_count_label.config(text=f"红方: {red_count}")
        self.blue_count_label.config(text=f"蓝方: {blue_count}")
    
    def handle_game_over(self):
        """处理游戏结束"""
        winner = self.game.get_winner(self.board)
        self.game_running = False
        
        # 更新游戏记录
        self.game_record["game_info"]["end_time"] = datetime.now().isoformat()
        
        if winner == 1:  # 红方获胜
            if self.game_mode == "human_vs_ai":
                result_text = "红方 (人类) 获胜！"
                self.game_record["game_info"]["result"] = "human_wins"
            else:
                result_text = "红方 (AI) 获胜！"
                self.game_record["game_info"]["result"] = "ai_wins"
            self.game_status_label.config(text="红方获胜")
        elif winner == -1:  # 蓝方获胜
            if self.game_mode == "human_vs_ai":
                result_text = "蓝方 (AI) 获胜！"
                self.game_record["game_info"]["result"] = "ai_wins"
            else:
                result_text = "蓝方 (人类) 获胜！"
                self.game_record["game_info"]["result"] = "human_wins"
            self.game_status_label.config(text="蓝方获胜")
        else:
            result_text = "平局！"
            self.game_record["game_info"]["result"] = "draw"
            self.game_status_label.config(text="平局")
        
        messagebox.showinfo("游戏结束", result_text)
        
        # 禁用操作
        self.confirm_dice_btn.config(state=tk.DISABLED)
        if not self.dice_entry:
            return
        self.dice_entry.config(state=tk.DISABLED)
        
        # 提示保存棋谱
        if messagebox.askyesno("保存棋谱", "是否保存这局游戏的棋谱？"):
            self.save_game_record()
    
    def new_game(self):
        """开始新游戏"""
        if self.game_running:
            if not messagebox.askyesno("确认", "当前游戏正在进行，确定要开始新游戏吗？"):
                return
        
        self.reset_game()
        self.game_running = True
        self.game_status_label.config(text="游戏开始")
        
        # 初始化游戏记录
        mode_name = "人机对弈" if self.game_mode == "human_vs_ai" else "机人对弈"
        self.game_record = {
            "game_info": {
                "start_time": datetime.now().isoformat(),
                "difficulty": self.difficulty_level,
                "mode": mode_name,
                "human_player": "红方" if self.human_player == 1 else "蓝方",
                "ai_player": "蓝方" if self.ai_player == -1 else "红方"
            },
            "moves": []
        }
        
        # 红方先手，检查是否是AI
        if self.current_player == self.ai_player:
            self.switch_to_ai_turn()
        else:
            self.switch_to_human_turn()
    
    def reset_game(self):
        """重置游戏"""
        self.game_running = False
        self.current_player = 1  # 红方先手
        self.current_die = 1
        self.selected_piece = None
        self.legal_moves = []
        self.move_history = []
        
        # 设置初始棋盘
        self.setup_initial_board()
        
        # 重置UI
        self.dice_display.config(text="?")
        if not self.dice_entry:
            return
        self.dice_entry.delete(0, tk.END)
        if not self.player_label:
            return
        self.player_label.config(text="当前玩家: 红方", fg="red")
        self.game_status_label.config(text="等待开始")
        self.ai_status_label.config(text="待机")
        
        # 清空历史
        if not self.history_text:
            return
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        self.history_text.config(state=tk.DISABLED)
        
        self.update_game_display()
        if not self.status_label:
            return
        self.status_label.config(text="游戏已重置")
    
    def setup_initial_board(self):
        """设置初始棋盘布局"""
        self.board = np.array([
            [0, 0, 0, 11, 12],
            [0, 10, 0, 0, 0],
            [0, 0, 9, 8, 0],
            [0, 7, 0, 0, 0],
            [1, 2, 3, 4, 5]
        ])
        
        # 随机放置第6个蓝方棋子
        empty_positions = [(i, j) for i in range(5) for j in range(5) if self.board[i, j] == 0]
        if empty_positions:
            pos = random.choice(empty_positions)
            self.board[pos[0], pos[1]] = 6
    
    def undo_move(self):
        """悔棋功能"""
        if not self.move_history:
            messagebox.showinfo("提示", "没有可以悔棋的移动")
            return
            
        if not messagebox.askyesno("确认悔棋", "确定要悔棋吗？"):
            return
        
        # 移除最后的移动
        last_move = self.move_history.pop()
        self.game_record["moves"].pop()
        
        # 恢复棋盘状态
        self.board = np.array(last_move["board_before"])
        
        # 如果悔棋的是AI移动，再悔棋一步人类移动
        if last_move["player"] != self.human_player and self.move_history:
            prev_move = self.move_history.pop()
            self.game_record["moves"].pop()
            self.board = np.array(prev_move["board_before"])
        
        # 重置到人类回合
        self.switch_to_human_turn()
        self.update_game_display()
        
        # 更新历史显示
        if not self.history_text:
            return
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)
        for i, move_record in enumerate(self.move_history):
            move = move_record["move"]
            player = move_record["player"]
            die = move_record["die"]
            self.add_move_to_history(move, player, die)
        self.history_text.config(state=tk.DISABLED)
    
    def save_game_record(self):
        """保存棋谱"""
        if not self.game_record["moves"]:
            messagebox.showinfo("提示", "没有可保存的游戏记录")
            return
        
        filename = filedialog.asksaveasfilename(
            title="保存棋谱",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.game_record, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("保存成功", f"棋谱已保存到: {filename}")
                if not self.status_label:
                    return
                self.status_label.config(text=f"棋谱已保存: {filename}")
            except Exception as e:
                messagebox.showerror("保存失败", f"保存棋谱时出错: {str(e)}")
    
    def load_game_record(self):
        """加载棋谱"""
        if self.game_running:
            if not messagebox.askyesno("确认", "当前游戏正在进行，确定要加载棋谱吗？"):
                return
        
        filename = filedialog.askopenfilename(
            title="加载棋谱",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    loaded_record = json.load(f)
                
                # 重置游戏
                self.reset_game()
                
                # 加载游戏记录
                self.game_record = loaded_record
                self.move_history = loaded_record["moves"]
                
                # 恢复模式设置
                if "mode" in loaded_record["game_info"]:
                    if loaded_record["game_info"]["mode"] == "人机对弈":
                        self.mode_var.set("human_vs_ai")
                    else:
                        self.mode_var.set("ai_vs_human")
                    self.on_mode_change()
                
                # 重播移动
                self.replay_moves()
                
                messagebox.showinfo("加载成功", f"棋谱已加载: {filename}")
                if not self.status_label:
                    return
                self.status_label.config(text=f"已加载棋谱: {filename}")
                
            except Exception as e:
                messagebox.showerror("加载失败", f"加载棋谱时出错: {str(e)}")
    
    def replay_moves(self):
        """重播移动"""
        self.setup_initial_board()
        
        for move_record in self.move_history:
            move = move_record["move"]
            player = move_record["player"]
            die = move_record["die"]
            
            # 执行移动
            self.board = self.game.make_move(self.board, move)
            
            # 添加到历史显示
            self.add_move_to_history(move, player, die)
        
        self.update_game_display()
        
        # 检查游戏状态
        if self.game.is_game_over(self.board):
            self.handle_game_over()
        else:
            self.game_running = True
            # 根据下一个该谁下棋来决定回合
            if self.is_human_turn():
                self.switch_to_human_turn()
            else:
                self.switch_to_ai_turn()
    
    def export_board(self):
        """导出当前棋盘"""
        filename = filedialog.asksaveasfilename(
            title="导出棋盘",
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    for row in self.board:
                        f.write(' '.join(map(str, row)) + '\n')
                messagebox.showinfo("导出成功", f"棋盘已导出到: {filename}")
            except Exception as e:
                messagebox.showerror("导出失败", f"导出棋盘时出错: {str(e)}")
    
    def import_board(self):
        """导入棋盘"""
        filename = filedialog.askopenfilename(
            title="导入棋盘",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                
                board = []
                for line in lines:
                    row = list(map(int, line.strip().split()))
                    if len(row) == 5:
                        board.append(row)
                
                if len(board) == 5:
                    self.board = np.array(board, dtype=int)
                    self.update_game_display()
                    messagebox.showinfo("导入成功", f"棋盘已从 {filename} 导入")
                else:
                    messagebox.showerror("导入失败", "文件格式不正确")
                    
            except Exception as e:
                messagebox.showerror("导入失败", f"导入棋盘时出错: {str(e)}")
    
    def on_difficulty_change(self, value):
        """难度改变事件"""
        self.difficulty_level = int(value)
        difficulty_names = {3: "简单", 4: "中等", 5: "困难"}
        if not self.status_label:
            return
        self.status_label.config(text=f"难度已设置为: {difficulty_names.get(self.difficulty_level, '未知')}")
    
    def set_difficulty(self):
        """设置难度对话框"""
        difficulty = simpledialog.askinteger(
            "设置难度", 
            "请输入AI难度等级 (3-5):\n3=简单, 4=中等, 5=困难",
            initialvalue=self.difficulty_level,
            minvalue=3,
            maxvalue=5
        )
        
        if difficulty:
            self.difficulty_level = difficulty
            self.difficulty_var.set(difficulty)
    
    def show_rules(self):
        """显示游戏规则"""
        rules_text = """
爱因斯坦棋游戏规则:

1. 棋盘: 5×5方格棋盘
2. 棋子: 每方6个棋子，编号1-6
3. 目标: 
   - 红方: 任意棋子到达右下角(4,4)
   - 蓝方: 任意棋子到达左上角(0,0)
   - 或吃光对方所有棋子

4. 移动规则:
   - 掷骰子确定可移动的棋子
   - 如果对应编号棋子不存在，移动最接近的棋子
   - 红方只能向右下方向移动
   - 蓝方只能向左上方向移动

5. 双模式支持:
   - 人机对弈: 人类(红方) vs AI(蓝方)
   - 机人对弈: AI(红方) vs 人类(蓝方)

6. 操作说明:
   - 选择游戏模式
   - 输入骰子点数并确认
   - 点击要移动的棋子
   - 点击目标位置完成移动
        """
        messagebox.showinfo("游戏规则", rules_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
爱因斯坦棋双模式对弈系统 v1.0

基于PMCTS算法的人工智能对弈系统

特色功能:
- 双模式对弈 (人机/机人)
- 智能AI对手 (3个难度等级)
- 棋谱保存/加载
- 悔棋功能
- 棋盘导入/导出

技术特点:
- Python + tkinter界面
- PMCTS算法AI
- 文件通信机制
- 完整的游戏记录

© 2024 All Rights Reserved
        """
        messagebox.showinfo("关于", about_text)
    
    def quit_game(self):
        """退出游戏"""
        if self.game_running:
            if not messagebox.askyesno("确认退出", "游戏正在进行，确定要退出吗？"):
                return
        
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """运行主程序"""
        self.root.mainloop()


def main():
    """主函数"""
    # 创建必要的目录
    os.makedirs("test_files", exist_ok=True)
    
    try:
        # 启动GUI
        app = DualModeEinsteinGUI()
        app.run()
    except Exception as e:
        print(f"启动GUI失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()