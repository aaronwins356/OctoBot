from datasets import load_dataset

def load_data(name='wikitext', split='train'):
    return load_dataset(name, split=split)
