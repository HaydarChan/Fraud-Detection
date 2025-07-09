# Fraud Call Detector

A comprehensive system for detecting fraudulent phone calls using audio analysis and machine learning. This project provides tools to generate synthetic audio datasets, preprocess and train models, and a Streamlit web app to analyze and compare fraud detection results using two models: Qwen2-Audio and Whisper+Sailor.

---

## Features
- **Streamlit Web App**: Upload `.wav` or `.mp4` files to detect and compare fraud predictions using two different models.
- **Dataset Creation Pipeline**: Generate synthetic fraud/non-fraud scripts, convert them to audio using Azure TTS, and prepare datasets for training.
- **Training Notebooks**: Jupyter notebooks for finetuning Qwen2-Audio and Whisper+Sailor models.

---

## Folder Structure

- `app.py` — Streamlit web app for fraud detection.
- `dataset_creation/` — Scripts for generating scripts, audio, and datasets:
  - `generateScript.py`: Generate synthetic dialog scripts (fraud & non-fraud) using Gemini API.
  - `generateAudio.py`: Convert scripts to audio using Azure TTS.
  - `create_dataset.py`: Prepare the final dataset CSV for training.
  - `audio_preprocess.py`: (If present) Additional audio preprocessing utilities.
- `utils/` — Utility modules for audio processing and model inference.
- `training_notebook/` — Jupyter notebooks for model finetuning:
  - `finetune-qwen2-audio.ipynb`
  - `finetune-sailor2.ipynb`
- `audio-testing/` — Example/test audio files.

---

## Step-by-Step Usage

### 1. Clone the Repository
```bash
git clone https://github.com/HaydarChan/Fraud-Detection.git
cd fraud
```

### 2. Create and Activate a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Set Up API Keys (Required for Dataset Creation)
- **Azure Speech Service**: For TTS in `generateAudio.py`
  - Set environment variables:
    - `AZURE_SPEECH_KEY` (your Azure Speech API key)
    - `AZURE_SPEECH_REGION` (e.g., `southeastasia`)
- **Gemini API**: For script generation in `generateScript.py`
  - Set environment variable:
    - `GEMINI_API_KEY` (your Gemini API key)

You can use a `.env` file or export variables in your shell:
```bash
export AZURE_SPEECH_KEY=your_key
export AZURE_SPEECH_REGION=southeastasia
export GEMINI_API_KEY=your_gemini_key
```

### 5. Generate Synthetic Dialog Scripts
```bash
cd dataset_creation
python generateScript.py
```
- This will create `synthetic_dialogs_final.csv` with synthetic fraud and non-fraud dialogs.

### 6. Generate Audio Files from Scripts
```bash
python generateAudio.py
```
- This will use Azure TTS to generate audio files for each dialog in `audio_dataset_azure/`.

### 7. Create the Final Dataset CSV
```bash
python create_dataset.py
```
- This will produce `dataset.csv` with columns: `file`, `label`, `transcription`.

### 8. Run the Streamlit App
From the project root:
```bash
streamlit run app.py
```
- Open the provided local URL in your browser.
- Upload a `.wav` or `.mp4` file to analyze and compare fraud detection results.

### 9. Run the Training Notebooks
- Open the notebooks in `training_notebook/` using Jupyter or VSCode:
  - `finetune-qwen2-audio.ipynb`
  - `finetune-sailor2.ipynb`
- Follow the instructions in each notebook to finetune the models on your dataset.

---

## Example Usage
- **App**: Upload an audio file, view the transcript, listen to the audio, and compare model predictions.
- **Dataset Creation**: Generate new scripts and audio to expand your dataset for better model training.

---

## Requirements
- Python 3.8+
- Packages (see `requirements.txt`):
  - streamlit
  - moviepy
  - pydub
  - imageio-ffmpeg
- Additional (for dataset creation):
  - azure-cognitiveservices-speech
  - python-dotenv
  - google-generativeai
  - pandas

Install extra packages as needed:
```bash
pip install azure-cognitiveservices-speech python-dotenv google-generativeai pandas
```

---

## Notes
- **API Keys**: Required for dataset creation scripts. The Streamlit app does not require them for inference.
- **Audio Format**: The app supports `.wav` and `.mp4` files. For best results, use clear, single-speaker audio.
- **Troubleshooting**:
  - Ensure all environment variables are set before running dataset creation scripts.
  - If you encounter missing dependencies, install them with pip as shown above.
  - For large dataset generation, ensure you have sufficient Azure/Gemini API quota.
