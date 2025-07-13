"""Training modules package"""
from .self_play import SelfPlayTrainer
from .trainer import NetworkTrainer

__all__ = ['SelfPlayTrainer', 'NetworkTrainer']