import streamlit as st
from utils.audio_processing import extract_audio
from utils.model import predict_fraud
import tempfile
import os

st.set_page_config(page_title="Fraud Call Detector", layout="centered")
st.title("Fraud Call Detector")
st.markdown("Upload a `.wav` or `.mp4` file to analyze whether it's a fraud call.")

uploaded_file = st.file_uploader("Upload audio or video file", type=["wav", "mp4"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        input_path = tmp.name

    with st.spinner("Processing..."):
        audio_path = extract_audio(input_path)
        is_fraud = predict_fraud(audio_path)

        st.success(f"Result: **{'1 (Fraud)' if is_fraud else '0 (Not Fraud)'}**")
        os.remove(input_path)
        if audio_path != input_path:
            os.remove(audio_path)
