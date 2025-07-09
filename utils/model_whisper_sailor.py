import torch
from unsloth import FastLanguageModel
from transformers import AutoTokenizer
import re

# --- Config sesuai training ---
model_name = "models/sailor2-finetuned"  # Ganti ke path model fine-tuned jika sudah ada
load_in_4bit = True
max_seq_length = 2048
dtype = None

# Load model & tokenizer
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = model_name,
    load_in_4bit = load_in_4bit,
    max_seq_length = max_seq_length,
    dtype = dtype,
)

# LoRA config (sama seperti training)
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    target_modules = [
        "lm_head",
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj", "all-linear"],
    lora_alpha = 32,
    lora_dropout = 0.1,
    bias = "none",    
    use_gradient_checkpointing = "unsloth",
    random_state = 12,
    use_rslora = True,
)

# Prompt template sesuai training
PROMPT_TEMPLATE = (
    "Berdasarkan  percakapan 2 orang melalui telepon berikut, klasifikasikan label yang 1 untuk percakapan biasa dan 2 untuk penipuan telekom:\n"
    "{}\n"
    "Klasifikasi yang benar adalah: kelas"
)

def transcribe_and_predict_whisper_sailor(audio_path: str) -> dict:
    """
    Fungsi ini mengasumsikan audio sudah di-transkrip (oleh Whisper).
    Fungsi ini hanya menerima transkrip (text) dan melakukan prediksi dengan Sailor2.
    """
    # --- Transkripsi audio dengan Whisper ---
    from transformers import pipeline
    whisper_pipe = pipeline("automatic-speech-recognition", model="openai/whisper-base", device=0)
    result = whisper_pipe(audio_path)
    transcript = result['text']

    # --- Format prompt sesuai training ---
    prompt = PROMPT_TEMPLATE.format(transcript.strip())

    # --- Tokenisasi dan inference ---
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=2,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    # Ambil output baru (token setelah prompt)
    generated = outputs[:, inputs["input_ids"].shape[1]:]
    pred_text = tokenizer.batch_decode(generated, skip_special_tokens=True)[0]

    # --- Ekstrak kelas (1/2) dari output model ---
    match = re.search(r"\b([12])\b", pred_text)
    if match:
        pred_class = int(match.group(1))
    else:
        pred_class = -1  # Tidak terdeteksi

    # Mapping ke fraud: 1 = normal, 2 = fraud
    fraud = 1 if pred_class == 2 else 0

    return {
        "transcript": transcript,
        "fraud": fraud,
        "raw_pred": pred_text
    }