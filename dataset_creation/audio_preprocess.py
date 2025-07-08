import librosa
import soundfile as sf
import os

file_name = os.listdir('audio_dataset_azure')

if not os.path.exists('preprocessed_file'):
    os.makedirs('preprocessed_file')

for file in file_name:
    if file.endswith('.wav'):
        file_path = os.path.join('audio_dataset_azure', file)
        y, sr = librosa.load(file_path, sr=16000)  # Load the audio file with a sample rate of 16kHz
        output_file_path = os.path.join('preprocessed_file', file)  # Define the output path
        sf.write(output_file_path, y, 16000)  # Save the processed audio file
        print(f'Processed and saved: {output_file_path}')
