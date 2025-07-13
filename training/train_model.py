"""训练主程序"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))

import torch
from training.neural_network import EinsteinNet
from self_play import SelfPlayTrainer
from trainer import NetworkTrainer

def train_model(num_iterations=50, games_per_iteration=100, training_epochs=10):
    """训练神经网络模型"""
    print("Starting Einstein Chess AI Training...")
    
    # 创建模型和训练器
    neural_net = EinsteinNet()
    network_trainer = NetworkTrainer(neural_net)
    self_play_trainer = SelfPlayTrainer(neural_net)
    
    # 训练循环
    for iteration in range(num_iterations):
        print(f"\n=== Training Iteration {iteration + 1}/{num_iterations} ===")
        
        # 自对弈生成数据
        print(f"Generating {games_per_iteration} self-play games...")
        training_data = []
        
        for game_num in range(games_per_iteration):
            if (game_num + 1) % 10 == 0:
                print(f"  Game {game_num + 1}/{games_per_iteration}")
            
            examples = self_play_trainer.play_game()
            training_data.extend(examples)
        
        print(f"Generated {len(training_data)} training examples")
        
        # 训练网络
        print("Training neural network...")
        for epoch in range(training_epochs):
            metrics = network_trainer.train_on_examples(training_data, batch_size=32)
            
            if epoch % 3 == 0:
                print(f"  Epoch {epoch + 1}/{training_epochs}: "
                      f"Loss={metrics['total_loss']:.4f}, "
                      f"Policy={metrics['policy_loss']:.4f}, "
                      f"Value={metrics['value_loss']:.4f}")
        
        # 保存模型
        if (iteration + 1) % 10 == 0:
            model_path = f"../models/model_iter_{iteration + 1}.pth"
            torch.save(neural_net.state_dict(), model_path)
            print(f"Model saved to {model_path}")
    
    # 保存最终模型
    torch.save(neural_net.state_dict(), "../models/shared_model.pth")
    torch.save(neural_net.state_dict(), "../models/blue_model.pth")
    torch.save(neural_net.state_dict(), "../models/red_model.pth")
    
    print("\nTraining completed!")
    print("Models saved:")
    print("  - ../models/shared_model.pth")
    print("  - ../models/blue_model.pth") 
    print("  - ../models/red_model.pth")

if __name__ == "__main__":
    # 创建models目录
    os.makedirs("../models", exist_ok=True)
    
    # 开始训练
    train_model(num_iterations=30, games_per_iteration=50, training_epochs=5)