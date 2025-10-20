from transformers import AutoTokenizer

def get_tokenizer(name='bert-base-uncased'):
    return AutoTokenizer.from_pretrained(name)
