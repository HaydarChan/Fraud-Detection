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
        # Baca CSV, pastikan 'id' dibaca sebagai string
        df = pd.read_csv(
            "synthetic_dialogs_final.csv",
            dtype={'id': str},
        )    
    except FileNotFoundError:
        print(f"Error: File input tidak ditemukan", file=sys.stderr)
        sys.exit(1)

    # Kolom yang dibutuhkan dari file asli
    required_columns = ['id', 'dialog', 'label']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: CSV input harus memiliki kolom: {', '.join(required_columns)}", file=sys.stderr)
        sys.exit(1)

    # Pilih kolom yang relevan
    df = df[required_columns].copy()

    # --- PERUBAHAN UTAMA DIMULAI DI SINI ---

    # 1. Bersihkan teks dialog secara menyeluruh
    print("Membersihkan teks dialog (menghapus label aktor)...")
    #    - Ganti baris baru ('\n') dengan spasi.
    #    - Hapus label aktor seperti "Penipu: " atau "Korban: " (regex: \w+:\s*).
    #    - Ganti beberapa spasi dengan satu spasi.
    #    - Hapus spasi di awal/akhir.
    df['dialog'] = df['dialog'].str.replace('\n', ' ', regex=False) \
                               .str.replace(r'\w+:\s*', '', regex=True) \
                               .str.replace(r'\s+', ' ', regex=True) \
                               .str.strip()

    # 2. Ganti nama kolom 'dialog' menjadi 'transcription'
    df.rename(columns={'dialog': 'transcription'}, inplace=True)

    # 3. Buat path file dari kolom 'id'
    df['file'] = df['id'].apply(lambda x: f'audio_dataset_azure/dialog_{x}.wav')

    # --- AKHIR PERUBAHAN UTAMA ---

    # Susun ulang dan pilih kolom akhir untuk file output
    df = df[['file', 'label', 'transcription']]

    # Validasi keberadaan file audio
    print("Memvalidasi keberadaan file audio...")
    exists_mask = df['file'].apply(os.path.isfile)

    if not exists_mask.all():
        missing_count = (~exists_mask).sum()
        missing_files = df.loc[~exists_mask, 'file'].tolist()
        print(f"Peringatan: {missing_count} file tidak ditemukan dan akan dilewati:", file=sys.stderr)
        # Tampilkan beberapa file yang hilang untuk debugging
        for path in missing_files[:5]: # Tampilkan maksimal 5
            print(f"  • {path}", file=sys.stderr)
        if missing_count > 5:
            print(f"  • ... dan {missing_count - 5} lainnya.", file=sys.stderr)
        
        # Hapus baris di mana file tidak ada
        df = df[exists_mask]

    # Simpan ke CSV baru tanpa kolom indeks
    df.to_csv("dataset.csv", index=False, encoding='utf-8')
    print(f"✔ Berhasil menulis {len(df)} entri ke dataset.csv")
    if 'missing_count' in locals() and missing_count > 0:
        print(f"Total {missing_count} entri dilewati karena file audio tidak ditemukan.")

if __name__ == "__main__":
    main()
