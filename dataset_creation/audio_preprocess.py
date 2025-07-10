import librosa
import soundfile as sf
import os

file_name = os.listdir('audio_dataset_azure')

if not os.path.exists('preprocessed_file'):
    os.makedirs('preprocessed_file')

for file in file_name:
    if file.endswith('.wav'):
        file_path = os.path.join('audio_dataset_azure', file)
        y, sr = librosa.load(file_path, sr=16000)  
        output_file_path = os.path.join('preprocessed_file', file) 
        sf.write(output_file_path, y, 16000) 
        print(f'Processed and saved: {output_file_path}')
