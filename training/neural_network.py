"""神经网络模型"""
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np

class EinsteinNet(nn.Module):
    def __init__(self, input_channels=4, hidden_size=256):
        super(EinsteinNet, self).__init__()
        
        # 卷积层
        self.conv1 = nn.Conv2d(input_channels, 64, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.conv3 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
        
        # 批归一化
        self.bn1 = nn.BatchNorm2d(64)
        self.bn2 = nn.BatchNorm2d(128)
        self.bn3 = nn.BatchNorm2d(128)
        
        # 全连接层
        conv_output_size = 128 * 5 * 5
        self.fc_common = nn.Linear(conv_output_size, hidden_size)
        
        # 策略头
        self.policy_head = nn.Sequential(
            nn.Linear(hidden_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, 75),  # 最大动作空间
        )
        
        # 价值头
        self.value_head = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1),
            nn.Tanh()
        )
    
    def forward(self, x):
        # 卷积层 + 批归一化 + 激活
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        
        # 展平
        x = x.view(x.size(0), -1)
        
        # 公共特征
        x = F.relu(self.fc_common(x))
        
        # 输出
        policy = F.log_softmax(self.policy_head(x), dim=1)
        value = self.value_head(x)
        
        return policy, value

def state_to_tensor(board: np.ndarray, die: int, player: int) -> torch.Tensor:
    """将游戏状态转换为神经网络输入"""
    # 创建4个通道
    red_channel = ((board >= 1) & (board <= 6)).astype(np.float32)
    blue_channel = ((board >= 7) & (board <= 12)).astype(np.float32)
    die_channel = np.full((5, 5), die / 6.0, dtype=np.float32)
    player_channel = np.full((5, 5), (player + 1) / 2.0, dtype=np.float32)
    
    # 堆叠通道
    state_tensor = np.stack([red_channel, blue_channel, die_channel, player_channel])
    
    return torch.FloatTensor(state_tensor).unsqueeze(0)