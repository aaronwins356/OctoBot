import torch.nn as nn
from .transformer_blocks import TransformerBlock

class SimpleTransformer(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.layers = nn.ModuleList([TransformerBlock(config['hidden_size'], config['num_heads']) for _ in range(config['num_layers'])])
        self.lm_head = nn.Linear(config['hidden_size'], config['vocab_size'], bias=False)

    def forward(self, x):
        for layer in self.layers:
            x = layer(x)
        return self.lm_head(x)
