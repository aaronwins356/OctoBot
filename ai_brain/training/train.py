import torch
from torch.utils.data import DataLoader
from transformers import AdamW

def train(model, dataset, config):
    dataloader = DataLoader(dataset, batch_size=config['batch_size'], shuffle=True)
    optimizer = AdamW(model.parameters(), lr=config['learning_rate'])
    model.train()
    for epoch in range(config['epochs']):
        for batch in dataloader:
            loss = model(**batch).loss
            loss.backward()
            optimizer.step()
            optimizer.zero_grad()
