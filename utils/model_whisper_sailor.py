# Inference pipeline Whisper + Sailor2 untuk deteksi fraud dari audio
import torch
import re
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

# Konfigurasi model dan quantization
base_model_id = "sail/Sailor2-8B"
adapter_id = "models/sailor2-finetuned"

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# Load model dan tokenizer
model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    quantization_config=quantization_config,
    torch_dtype=torch.bfloat16,
    device_map="auto"
)

tokenizer = AutoTokenizer.from_pretrained(base_model_id)
model = PeftModel.from_pretrained(model, adapter_id)
PROMPT_TEMPLATE = (
    "Berdasarkan  percakapan 2 orang melalui telepon berikut, klasifikasikan label yang 1 untuk percakapan biasa dan 2 untuk penipuan telekom:\n"
    "{}\n"
    "Klasifikasi yang benar adalah: kelas"
)

# Fungsi utama: transkripsi audio dengan Whisper, lalu prediksi fraud dengan Sailor2
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
