import streamlit as st
from utils.audio_processing import extract_audio
from utils.model_qwen2 import predict_fraud_qwen2
from utils.model_whisper_sailor import transcribe_and_predict_whisper_sailor
from utils.audio_processing import preprocess_audio
import tempfile
import os

st.set_page_config(page_title="Fraud Call Detector", layout="centered")
st.title("Fraud Call Detector")
st.markdown("Upload a `.wav` or `.mp4` file to analyze and compare fraud detection using Qwen2-Audio and Whisper+Sailor.")

uploaded_file = st.file_uploader("Upload audio or video file", type=["wav", "mp4"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    with st.spinner("Extracting audio..."):
        audio_path = extract_audio(input_path)
        preprocessed_audio_path = preprocess_audio(audio_path)

    with st.spinner("Transcribing with Whisper+Sailor..."):
        whisper_result = transcribe_and_predict_whisper_sailor(audio_path)
        transcript = whisper_result['transcript']

    st.markdown("### Transcript (from Whisper+Sailor)")
    st.code(transcript, language="text")

    st.markdown("### Listen to the audio")
    st.audio(audio_path, format="audio/wav", start_time=0)

    with st.spinner("Predicting with Qwen2-Audio..."):
        qwen2_pred = predict_fraud_qwen2(audio_path, transcript)  # transcript bisa dipakai jika model Qwen2 kamu butuh text

    st.markdown("### Results Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Qwen2-Audio-7B (Finetuned)")
        st.markdown(f"**Prediction:** {'1 (Fraud)' if qwen2_pred['fraud'] else '0 (Not Fraud)'}")
    with col2:
        st.subheader("Whisper + Sailor")
        st.markdown(f"**Prediction:** {'1 (Fraud)' if whisper_result['fraud'] else '0 (Not Fraud)'}")

    # Clean up temp files
    os.remove(input_path)
    if audio_path != input_path:
        os.remove(audio_path)