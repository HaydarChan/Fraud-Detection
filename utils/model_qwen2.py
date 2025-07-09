import torch
import librosa
from transformers import AutoProcessor, Qwen2AudioForConditionalGeneration, BitsAndBytesConfig
from urllib.request import urlopen
from io import BytesIO
import os

# --- Quantization config sesuai training ---
quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

# --- Load processor dan model  ---
MODEL_PATH = "models/qwen2-audio-finetuned"  # Ganti ke path model fine-tuned
processor = AutoProcessor.from_pretrained(
    MODEL_PATH,
    trust_remote_code=True,
    sampling_rate=16000
)
model = Qwen2AudioForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    quantization_config=quant_config,
    device_map="auto",
)

def predict_fraud_qwen2(audio_path: str, transcript: str = None) -> dict:
    """
    Inference Qwen2-Audio-7B untuk klasifikasi fraud.
    Args:
        audio_path: path ke file audio (wav)
        transcript: (opsional) transkrip, tidak dipakai di Qwen2
    Returns:
        dict: {'fraud': 0/1, 'response': <raw model output>}
    """
    # Siapkan prompt chat template sesuai training
    conversation = [
        {"role": "system", "content": "Kamu adalah model yang menenetukan apakah percakapan yang dimasukkan dari dua orang dalam telepon tersebut adalah penipuan telekom atau tidak."},
        {"role": "user", "content": [
            {"type": "audio", "audio": audio_path},
            {"type": "text", "text": "Klasifikasikan audio ini: 0 atau 1."},
        ]}
    ]
    text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)

    # Load audio (pastikan sr=16000)
    audio_data, _ = librosa.load(audio_path, sr=processor.feature_extractor.sampling_rate)
    audios = [audio_data]

    # Tokenize input
    inputs = processor(
        text=text,
        audio=audios,
        return_tensors="pt",
        padding=True,
        truncation=True
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # Inference
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=2)
    # Ambil token baru saja
    generated_ids = generated_ids[:, inputs["input_ids"].size(1):]
    response = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]

    # Ekstrak label 0/1 dari response (pastikan robust)
    fraud = 1 if "1" in response.strip().split() else 0

    return {"fraud": fraud, "response": response}