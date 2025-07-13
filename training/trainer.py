"""神经网络训练器"""
import torch
import torch.nn as nn
import numpy as np
from typing import List, Tuple

class NetworkTrainer:
    def __init__(self, neural_net, learning_rate=0.001, weight_decay=1e-4):
        self.neural_net = neural_net
        self.optimizer = torch.optim.Adam(
            neural_net.parameters(), 
            lr=learning_rate, 
            weight_decay=weight_decay
        )
        self.scheduler = torch.optim.lr_scheduler.StepLR(
            self.optimizer, 
            step_size=10, 
            gamma=0.9
        )
        
        self.policy_loss_fn = nn.KLDivLoss(reduction='batchmean')
        self.value_loss_fn = nn.MSELoss()
        
    def train_on_examples(self, examples: List[Tuple], batch_size=32, epochs=1):
        """在训练样本上训练网络"""
        self.neural_net.train()
        
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_loss = 0.0
        num_batches = 0
        
        for epoch in range(epochs):
            # 随机打乱样本
            indices = np.random.permutation(len(examples))
            
            for i in range(0, len(examples), batch_size):
                batch_indices = indices[i:i + batch_size]
                batch = [examples[idx] for idx in batch_indices]
                
                if len(batch) < 2:  # 跳过太小的batch
                    continue
                
                # 准备batch数据
                states = torch.cat([ex[0] for ex in batch])
                target_policies = self._prepare_policy_targets(batch)
                target_values = torch.tensor([ex[2] for ex in batch], dtype=torch.float32)
                
                # 前向传播
                log_probs, values = self.neural_net(states)
                
                # 计算损失
                policy_loss = self.policy_loss_fn(log_probs, target_policies)
                value_loss = self.value_loss_fn(values.squeeze(), target_values)
                loss = policy_loss + value_loss
                
                # 反向传播
                self.optimizer.zero_grad()
                loss.backward()
                
                # 梯度裁剪
                torch.nn.utils.clip_grad_norm_(self.neural_net.parameters(), max_norm=1.0)
                
                self.optimizer.step()
                
                # 统计
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_loss += loss.item()
                num_batches += 1
        
        # 更新学习率
        self.scheduler.step()
        
        if num_batches > 0:
            avg_policy_loss = total_policy_loss / num_batches
            avg_value_loss = total_value_loss / num_batches
            avg_total_loss = total_loss / num_batches
            
            return {
                'policy_loss': avg_policy_loss,
                'value_loss': avg_value_loss,
                'total_loss': avg_total_loss,
                'learning_rate': self.scheduler.get_last_lr()[0]
            }
        else:
            return {'policy_loss': 0, 'value_loss': 0, 'total_loss': 0, 'learning_rate': 0}
    
    def _prepare_policy_targets(self, batch: List[Tuple]) -> torch.Tensor:
        """准备策略目标"""
        batch_size = len(batch)
        policy_targets = torch.zeros(batch_size, 75)  # 最大动作空间
        
        for i, (_, action_probs, _) in enumerate(batch):
            for action, prob in action_probs.items():
                if action < 75:
                    policy_targets[i, action] = prob
        
        # 确保每行和为1
        row_sums = policy_targets.sum(dim=1, keepdim=True)
        row_sums[row_sums == 0] = 1  # 避免除零
        policy_targets = policy_targets / row_sums
        
        return policy_targets