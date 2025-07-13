
Einstein/
├── README.md                    # 项目说明文档
├── requirements.txt             # Python依赖包列表
│
├── ai_blue.py                   # 蓝方AI主程序 → EinsteinAI_Blue.exe
├── ai_red.py                    # 红方AI主程序 → EinsteinAI_Red.exe
│
├── core/                        # 核心模块目录
│   ├── __init__.py             # Python包初始化文件
│   ├── game_engine.py          # 游戏规则引擎
│   ├── mcts.py                 # MCTS算法实现
│   ├── file_handler.py         # 文件读写处理
│   └── config.py               # 配置参数
│
├── modelS/                      # 神经网络模块(预留)
│   ├── __init__.py             # Python包初始化文件
│   ├── network.py              # 神经网络实现(空文件,预留)
│   └── trainer.py              # 训练系统(空文件,预留)
│
├── test_files/                  # 测试文件目录
│   ├── JavaOut.txt             # 蓝方AI测试输入
│   ├── JavaOut1.txt            # 红方AI测试输入
│   ├── JavaIn.txt              # 蓝方AI输出(程序生成)
│   └── JavaIn1.txt             # 红方AI输出(程序生成)


