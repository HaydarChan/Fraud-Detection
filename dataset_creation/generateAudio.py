import pandas as pd
import os
import re
import shutil
import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
import logging
from dotenv import load_dotenv
load_dotenv()

# ==============================================================================
# LANGKAH 1: KONFIGURASI DAN SETUP
# ==============================================================================

# Setup logging dasar
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Konfigurasi yang Dapat Diubah ---
METADATA_CSV_PATH = "synthetic_dialogs_final.csv"
OUTPUT_AUDIO_FOLDER = "audio_dataset_azure"
SILENCE_BETWEEN_CLIPS_MS = 2000  # Jeda antar kalimat dalam milidetik

# --- Konfigurasi Azure Speech Service (DIAMBIL DARI ENVIRONMENT VARIABLES) ---
# PENTING: Jangan tulis kunci API langsung di dalam kode.
# Atur environment variables di sistem Anda.
# Contoh di terminal:
# export AZURE_SPEECH_KEY="kunci_rahasia_anda"
# export AZURE_SPEECH_REGION="southeastasia"
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

# Voice mapping untuk setiap speaker
VOICE_CONFIG = {
    'penipu': 'id-ID-ArdiNeural',      # Suara pria untuk penipu
    'korban': 'id-ID-GadisNeural',     # Suara wanita untuk korban
    'penerima': 'id-ID-GadisNeural',    # Suara wanita untuk penerima
    'penelepon': 'id-ID-ArdiNeural',  # Suara pria untuk penelpon
}

# ==============================================================================
# LANGKAH 2: FUNGSI AZURE TTS YANG SUDAH DIPERBAIKI
# ==============================================================================

def create_speech_synthesizer(voice_name, output_path):
    """Membuat dan mengonfigurasi SpeechSynthesizer."""
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    
    # Mengatur output langsung ke format WAV berkualitas tinggi
    speech_config.set_speech_synthesis_output_format(speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm)
    speech_config.speech_synthesis_voice_name = voice_name
    
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    
    return speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

def synthesize_text_to_wav(synthesizer, text):
    """Menggunakan Azure TTS untuk mengubah teks menjadi file audio WAV."""
    if not text or not text.strip():
        logging.warning("Teks kosong dilewati.")
        return False
        
    try:
        result = synthesizer.speak_text_async(text).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return True
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            logging.error(f"Sintesis suara dibatalkan: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                logging.error(f"Detail error: {cancellation_details.error_details}")
            return False
        else:
            logging.error(f"Sintesis suara gagal karena: {result.reason}")
            return False
            
    except Exception as e:
        logging.error(f"Terjadi error saat sintesis: {e}", exc_info=True)
        return False

# ==============================================================================
# LANGKAH 3: FUNGSI UNTUK MEMERIKSA FILE YANG HILANG
# ==============================================================================

def check_missing_files(df):
    """
    Memeriksa file audio mana yang hilang atau rusak dari folder output.
    Returns list of dialog IDs yang perlu dibuat ulang.
    """
    missing_files = []
    corrupted_files = []
    
    for _, row in df.iterrows():
        dialogue_id = row['id'] 
        output_file_path = os.path.join(OUTPUT_AUDIO_FOLDER, f"dialog_{dialogue_id}.wav")
        
        if not os.path.exists(output_file_path):
            missing_files.append(dialogue_id)
            logging.info(f"File hilang: dialog_{dialogue_id}.wav")
        else:
            # Periksa apakah file kosong atau rusak
            try:
                file_size = os.path.getsize(output_file_path)
                if file_size < 1024:  # File kurang dari 1KB kemungkinan rusak
                    corrupted_files.append(dialogue_id)
                    logging.warning(f"File mungkin rusak (ukuran {file_size} bytes): dialog_{dialogue_id}.wav")
            except Exception as e:
                corrupted_files.append(dialogue_id)
                logging.error(f"Error membaca file dialog_{dialogue_id}.wav: {e}")
    
    total_missing = len(missing_files) + len(corrupted_files)
    
    if missing_files:
        logging.info(f"Ditemukan {len(missing_files)} file yang hilang.")
    if corrupted_files:
        logging.info(f"Ditemukan {len(corrupted_files)} file yang mungkin rusak.")
    
    if total_missing == 0:
        logging.info("Semua file audio sudah ada dan dalam kondisi baik!")
    else:
        logging.info(f"Total {total_missing} file perlu diregenerasi.")
    
    return missing_files + corrupted_files

def backup_corrupted_files(corrupted_ids):
    """
    Memindahkan file yang rusak ke folder backup sebelum diregenerasi.
    """
    if not corrupted_ids:
        return
    
    backup_folder = os.path.join(OUTPUT_AUDIO_FOLDER, "backup_corrupted")
    os.makedirs(backup_folder, exist_ok=True)
    
    for dialogue_id in corrupted_ids:
        original_path = os.path.join(OUTPUT_AUDIO_FOLDER, f"dialog_{dialogue_id}.wav")
        backup_path = os.path.join(backup_folder, f"dialog_{dialogue_id}_backup.wav")
        
        try:
            if os.path.exists(original_path):
                shutil.move(original_path, backup_path)
                logging.info(f"File rusak dipindahkan ke backup: dialog_{dialogue_id}.wav")
        except Exception as e:
            logging.error(f"Gagal membackup file dialog_{dialogue_id}.wav: {e}")

# ==============================================================================
# LANGKAH 4: PROSES GENERASI AUDIO DARI CSV
# ==============================================================================

def generate_and_combine_dialogue_audio(dialog_id, dialogue_text, output_path):
    """
    Menghasilkan audio untuk setiap baris dialog, lalu menggabungkannya menjadi satu file.
    Menggunakan folder sementara yang akan dihapus secara otomatis.
    """
    logging.info(f"Memproses Dialog ID: {dialog_id}...")

    temp_folder = os.path.join(OUTPUT_AUDIO_FOLDER, f"temp_{dialog_id}")
    os.makedirs(temp_folder, exist_ok=True)

    try:
        lines = dialogue_text.strip().split('\n')
        audio_clip_paths = []

        for i, line in enumerate(lines):
            match = re.match(r'^\s*(penipu|korban|penerima|penelepon):\s*(.*)', line, re.IGNORECASE)
            if not match:
                continue

            speaker, text_to_speak = match.groups()
            speaker = speaker.lower()

            if not text_to_speak.strip():
                continue

            voice_name = VOICE_CONFIG.get(speaker)
            if not voice_name:
                logging.warning(f"Tidak ada voice config untuk speaker '{speaker}'. Menggunakan default.")
                voice_name = 'id-ID-ArdiNeural'

            temp_clip_path_wav = os.path.join(temp_folder, f"line_{i}.wav")

            synthesizer = create_speech_synthesizer(voice_name, temp_clip_path_wav)

            success = synthesize_text_to_wav(synthesizer, text_to_speak)

            if success and os.path.exists(temp_clip_path_wav):
                audio_clip_paths.append(temp_clip_path_wav)
                logging.info(f"  Berhasil: {speaker} - '{text_to_speak[:50]}...'")
            else:
                logging.error(f"  Gagal: {speaker} - '{text_to_speak[:50]}...'")

        if audio_clip_paths:
            silence = AudioSegment.silent(duration=SILENCE_BETWEEN_CLIPS_MS)
            combined_audio = AudioSegment.empty()

            for clip_path in audio_clip_paths:
                clip = AudioSegment.from_wav(clip_path)
                combined_audio += clip + silence

            combined_audio.export(output_path, format="wav")
            logging.info(f"Sukses! Audio dialog disimpan di: {output_path}")
            return True
        else:
            logging.warning(f"Tidak ada audio yang berhasil dibuat untuk Dialog ID: {dialog_id}")
            return False

    except Exception as e:
        logging.error(f"Error saat memproses Dialog ID {dialog_id}: {e}", exc_info=True)
        return False

def main():
    """Fungsi utama untuk menjalankan seluruh proses."""
    # Validasi konfigurasi Azure yang krusial
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        logging.critical("Error: Environment variable AZURE_SPEECH_KEY dan AZURE_SPEECH_REGION harus diatur!")
        logging.critical("Anda bisa mendapatkannya dari portal Azure di bawah layanan 'Speech Services'.")
        return
    
    os.makedirs(OUTPUT_AUDIO_FOLDER, exist_ok=True)
    
    try:
        df = pd.read_csv(METADATA_CSV_PATH,  # Perbaiki masalah baris buruk
)
    except FileNotFoundError:
        logging.critical(f"Error: File CSV '{METADATA_CSV_PATH}' tidak ditemukan!")
        return
    
    logging.info(f"Memeriksa status file audio untuk {len(df)} dialog...")
    
    # Periksa file yang hilang atau rusak
    files_to_regenerate = check_missing_files(df)
    
    if not files_to_regenerate:
        logging.info("Tidak ada file yang perlu diregenerasi. Semua file sudah lengkap!")
        return
    
    # Filter DataFrame untuk hanya memproses file yang perlu diregenerasi
    df_to_process = df[df['id'].isin(files_to_regenerate)]
    
    logging.info(f"Memulai regenerasi untuk {len(files_to_regenerate)} file...")
    logging.info("Konfigurasi Suara:")
    for speaker, voice in VOICE_CONFIG.items():
        logging.info(f"  {speaker}: {voice}")
    
    # Backup file yang rusak terlebih dahulu
    corrupted_files = []
    for dialogue_id in files_to_regenerate:
        output_file_path = os.path.join(OUTPUT_AUDIO_FOLDER, f"dialog_{dialogue_id}.wav")
        if os.path.exists(output_file_path):
            corrupted_files.append(dialogue_id)
    
    if corrupted_files:
        backup_corrupted_files(corrupted_files)
    
    # Proses regenerasi
    success_count = 0
    failed_count = 0
    
    for _, row in df_to_process.iterrows():
        dialogue_id = row['id']
        dialogue_text = str(row['dialog']) # Pastikan tipe data string
        
        output_file_path = os.path.join(OUTPUT_AUDIO_FOLDER, f"dialog_{dialogue_id}.wav")
        
        success = generate_and_combine_dialogue_audio(dialogue_id, dialogue_text, output_file_path)
        
        if success:
            success_count += 1
        else:
            failed_count += 1
    
    logging.info(f"\nProses regenerasi selesai!")
    logging.info(f"Berhasil: {success_count} file")
    logging.info(f"Gagal: {failed_count} file")
    
    if failed_count > 0:
        logging.warning("Ada beberapa file yang gagal dibuat. Periksa log di atas untuk detail.")

if __name__ == "__main__":
    main()