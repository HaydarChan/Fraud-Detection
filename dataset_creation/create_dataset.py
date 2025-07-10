import pandas as pd
import argparse
import os
import sys
import uuid 
import csv

def main():
    """
    Mempersiapkan dataset untuk klasifikasi audio.

    Skrip ini akan:
    1. Membaca CSV input.
    2. Memilih kolom 'id', 'dialog', dan 'label'.
    3. Membuat kolom 'file' dari 'id' dengan format 'audio/dialog_{id}.wav'.
    4. Membersihkan teks di kolom 'dialog' secara menyeluruh (termasuk menghapus label aktor)
       dan menamainya 'transcription'.
    5. Memvalidasi keberadaan file audio dan menghapus baris jika file tidak ditemukan.
    6. Menyimpan hasil ke CSV output dengan kolom: 'file', 'label', 'transcription'.
    """
    try:
        df = pd.read_csv(
            "synthetic_dialogs_final.csv",
            dtype={'id': str},
        )    
    except FileNotFoundError:
        print(f"Error: File input tidak ditemukan", file=sys.stderr)
        sys.exit(1)

    required_columns = ['id', 'dialog', 'label']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV input harus memiliki kolom: {', '.join(required_columns)}", file=sys.stderr)
        sys.exit(1)

    df = df[required_columns].copy()

    print("Membersihkan teks dialog (menghapus label aktor)...")

    df['dialog'] = df['dialog'].str.replace('\n', ' ', regex=False) \
                               .str.replace(r'\w+:\s*', '', regex=True) \
                               .str.replace(r'\s+', ' ', regex=True) \
                               .str.strip()

    df.rename(columns={'dialog': 'transcription'}, inplace=True)

    df['file'] = df['id'].apply(lambda x: f'audio_dataset_azure/dialog_{x}.wav')

    df = df[['file', 'label', 'transcription']]

    print("Memvalidasi keberadaan file audio...")
    exists_mask = df['file'].apply(os.path.isfile)

    if not exists_mask.all():
        missing_count = (~exists_mask).sum()
        missing_files = df.loc[~exists_mask, 'file'].tolist()
        print(f"Peringatan: {missing_count} file tidak ditemukan dan akan dilewati:", file=sys.stderr)

        for path in missing_files[:5]: 
            print(f"  • {path}", file=sys.stderr)
        if missing_count > 5:
            print(f"  • ... dan {missing_count - 5} lainnya.", file=sys.stderr)
        
        df = df[exists_mask]

    df.to_csv("dataset.csv", index=False, encoding='utf-8')
    print(f"✔ Berhasil menulis {len(df)} entri ke dataset.csv")
    if 'missing_count' in locals() and missing_count > 0:
        print(f"Total {missing_count} entri dilewati karena file audio tidak ditemukan.")

if __name__ == "__main__":
    main()
