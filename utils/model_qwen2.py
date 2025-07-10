import torch
import librosa
from transformers import Qwen2AudioForConditionalGeneration, AutoProcessor, BitsAndBytesConfig


MODEL_PATH = "fauzanazz/qwen2-audio-indo-fraudFinetune-4b"
max_seq_length = 2048

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4"
)

processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True, sampling_rate=16000)
model = Qwen2AudioForConditionalGeneration.from_pretrained(
    MODEL_PATH,
    device_map="auto",
    quantization_config=quant_config,
)

def predict_fraud_qwen2(audio_path: str) -> dict:
    conversation = [
        {"role": "system", "content": "Kamu adalah model yang menenetukan apakah percakapan yang dimasukkan dari dua orang dalam telepon tersebut adalah penipuan telekom atau tidak."},
        {"role": "user", "content": [
            {"type": "audio", "audio": audio_path},
            {"type": "text", "text": "Klasifikasikan audio ini: 0 atau 1."},
        ]}
    ]
    text = processor.apply_chat_template(conversation, add_generation_prompt=True, tokenize=False)
    audio_data, _ = librosa.load(audio_path, sr=processor.feature_extractor.sampling_rate)
    audios = [audio_data]
    inputs = processor(
        text=text,
        audio=audios,
        return_tensors="pt",
        padding=True,
        truncation=True
    )
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    with torch.no_grad():
        outputs = model.generate(**inputs, max_new_tokens=2)
    generated_ids = outputs[:, inputs["input_ids"].size(1):]
    response = processor.batch_decode(generated_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
    fraud = 1 if "1" in response.strip().split() else 0
    return {
        "fraud": fraud,
        "raw_pred": response
    }