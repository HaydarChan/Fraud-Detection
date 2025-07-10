# utils/model_sailor2.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import re

# Path ke model Sailor2 hasil fine-tune (lokal)
MODEL_PATH = "fauzanazz/sailor2-fraudFinetuned-indo-4b"
max_seq_length = 2048

# Load model & tokenizer sekali saja
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    torch_dtype=torch.float16,  # atau None jika tidak pakai quant
)

PROMPT_TEMPLATE = (
    "Berdasarkan  percakapan 2 orang melalui telepon berikut, klasifikasikan label yang 1 untuk percakapan biasa dan 2 untuk penipuan telekom:\n"
    "{}\n"
    "Klasifikasi yang benar adalah: kelas"
)

def predict_fraud_sailor2(transcript: str) -> dict:
    """
    Prediksi fraud menggunakan Sailor2, input transkrip text.
    Args:
        transcript: hasil transkripsi audio (string)
    Returns:
        dict: {'fraud': 0/1, 'raw_pred': <output model>}
    """
    prompt = PROMPT_TEMPLATE.format(transcript.strip())
    inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_seq_length).to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=2,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = outputs[:, inputs["input_ids"].shape[1]:]
    pred_text = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]
    match = re.search(r"\b([12])\b", pred_text)
    if match:
        pred_class = int(match.group(1))
    else:
        pred_class = -1
    fraud = 1 if pred_class == 2 else 0
    return {
        "fraud": fraud,
        "raw_pred": pred_text
    }