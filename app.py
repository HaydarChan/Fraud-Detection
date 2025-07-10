import streamlit as st
import tempfile
import os

from utils.model_whisper import transcribe_audio
from utils.model_sailor2 import predict_fraud_sailor2
from utils.model_qwen2 import predict_fraud_qwen2

st.set_page_config(page_title="Fraud Call Detector", layout="centered")
st.title("Fraud Call Detector")
st.markdown("Upload a `.wav`, `.mp3`, or `.mp4` file to analyze and classify fraud using Whisper, Sailor2, and Qwen2-Audio.")

uploaded_file = st.file_uploader("Upload audio or video file", type=["wav", "mp3", "mp4", "ogg", "m4a"])

if uploaded_file:
    # Simpan file upload ke temp
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
        tmp.write(uploaded_file.read())
        audio_path = tmp.name

    st.markdown("### Listen to the audio")
    st.audio(audio_path, format="audio/wav", start_time=0)

    with st.spinner("Transcribing with Whisper..."):
        transcript = transcribe_audio(audio_path)

    st.markdown("### Transcript (from Whisper)")
    st.code(transcript, language="text")

    with st.spinner("Predicting with Sailor2..."):
        sailor2_result = predict_fraud_sailor2(transcript)

    with st.spinner("Predicting with Qwen2-Audio..."):
        qwen2_result = predict_fraud_qwen2(audio_path)

    st.markdown("### Results Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Qwen2-Audio")
        st.markdown(f"**Prediction:** {'1 (Fraud)' if qwen2_result['fraud'] else '0 (Not Fraud)'}")
        st.markdown(f"**Raw model output:** {qwen2_result['raw_pred']}")
    with col2:
        st.subheader("Whisper + Sailor2")
        st.markdown(f"**Prediction:** {'1 (Fraud)' if sailor2_result['fraud'] else '0 (Not Fraud)'}")
        st.markdown(f"**Raw model output:** {sailor2_result['raw_pred']}")

    # Clean up temp file
    os.remove(audio_path)