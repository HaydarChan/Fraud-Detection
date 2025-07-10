import csv
import time
import random
import re 
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.0-flash"  
CSV_FILENAME = "synthetic_dialogs_final.csv"
DIALOGS_PER_SCENARIO = 12

fraud_scenarios = {
    "Penipuan Phishing & Malware (APK Paling Viral)": [
=        "Penipu mengaku dari jasa pengiriman (JNE/J&T/Anteraja), mengirim 'foto resi paket' dalam format file .APK.",
        "Penipu menyebar 'undangan pernikahan digital' atau 'undangan syukuran aqiqah' palsu berformat .APK yang bisa menguras m-banking.",
        "Penipu mengaku dari Kepolisian, mengirimkan 'surat tilang elektronik (e-tilang)' palsu dalam bentuk file .APK.",
        "Penipu mengaku dari PLN/PDAM, mengirim 'tagihan bulanan' atau 'pemberitahuan pemadaman' dalam format file .APK.",
        "Penipu mengaku dari kantor pajak, mengirim 'SPT Tahunan' atau 'tagihan pajak' dalam bentuk file .APK."
    ],
    "Penipuan Perbankan (Modus Klasik & Baru)": [
        "Penipu menyamar sebagai staf bank (BCA/BRI/Mandiri), mengabarkan ada 'perubahan tarif transfer menjadi Rp150.000/bulan' dan meminta korban mengisi link phishing untuk membatalkannya.",
        "Penipu dari 'divisi anti-fraud' bank menginformasikan kartu ATM korban terindikasi skimming dan meminta 16 digit nomor kartu serta kode OTP untuk 'pemblokiran darurat'.",
        "Penipu menginformasikan korban terpilih untuk upgrade menjadi nasabah prioritas/kartu kredit premium gratis dengan syarat verifikasi data sensitif melalui telepon.",
        "Penipu menelepon dan mengatakan bahwa korban memiliki tagihan kartu kredit yang belum dibayar, mengancam akan dilaporkan ke BI Checking jika tidak segera dilunasi ke rekening pribadi."
    ],
    "Penipuan Lowongan Kerja Fiktif (Part-Time & Remote)": [
        "Penipu menawarkan pekerjaan paruh waktu (part-time) mudah seperti 'Like & Subscribe YouTube' atau 'review produk di e-commerce', namun meminta deposit untuk 'tugas' berikutnya.",
        "Penipu mengaku dari HRD perusahaan BUMN atau tambang ternama, mengundang interview online, tapi korban harus mentransfer 'biaya akomodasi/tiket' yang dijanjikan akan di-refund.",
        "Penipu menawarkan pekerjaan entri data dari rumah dengan gaji tinggi, namun mengharuskan korban membeli 'software khusus' atau 'paket membership' dari mereka terlebih dahulu."
    ],
    "Penipuan Layanan Pelanggan & E-commerce": [
        "Penipu mengaku dari provider seluler (Telkomsel/Indosat), menawarkan upgrade jaringan 4G ke 5G atau bantuan blokir nomor spam, tujuannya mengambil alih WhatsApp/akun dengan meminta kode OTP (SIM Swap).",
        "Penipu mengaku dari pihak marketplace (Tokopedia/Shopee), menginformasikan korban memenangkan undian/giveaway dan meminta data pribadi atau 'pajak pemenang' untuk klaim hadiah.",
        "Penipu (sebagai penjual) di marketplace mengabarkan barang pesanan korban kosong dan mengarahkan proses refund di luar platform (via WhatsApp) untuk menipu."
    ],
    "Penipuan Pemerasan & Ancaman (Pinjol Ilegal)": [
        "Penipu mengaku sebagai debt collector dari pinjaman online (pinjol) ilegal, menagih tunggakan fiktif dan mengancam akan menyebar data KTP/foto korban ke seluruh kontak jika tidak membayar.",
        "Penipu menelepon dengan panik, mengaku anggota keluarga korban (anak/suami) mengalami kecelakaan atau ditangkap polisi, dan meminta uang tebusan/damai segera.",
        "Penipu mengirimkan pesan berisi ancaman setelah korban menginstal APK, mengklaim telah menyadap HP korban dan akan menyebar data pribadinya."
    ],
    "Penipuan Asmara (Romance Scam Khas Indonesia)": [
        "Penipu dengan profil palsu sebagai anggota TNI/Polisi atau pekerja tambang/pelayaran, menjalin hubungan asmara online lalu meminta uang untuk 'keadaan darurat' atau 'biaya cuti'.",
        "Penipu mengaku sebagai WNA tampan/cantik yang tertahan di Bea Cukai Indonesia dengan barang mewah untuk korban, dan meminta uang untuk 'pajak tebusan'.",
    ],
    "Penipuan Modus Salah Transfer & Investasi": [
        "Penipu sengaja mentransfer sejumlah uang ke korban, lalu menelepon dengan panik/sopan mengaku salah transfer dan meminta dikembalikan ke nomor rekening yang berbeda dari pengirim.",
        "Penipu menawarkan investasi bodong dengan skema ponzi, seperti titip dana (jastip trading) atau investasi robot trading dengan jaminan keuntungan tetap (fixed profit) yang tidak masuk akal.",
    ]
}

nonfraud_scenarios = {
        "Layanan Pesan Antar Makanan & Transportasi Online": [
        "Driver Gojek/Grab mengonfirmasi alamat pengantaran dan patokannya kepada pelanggan.",
        "Pelanggan menelepon driver karena ada barang yang tertinggal di mobil/motor.",
        "Driver GoFood/GrabFood menelepon pelanggan untuk memberitahu bahwa menu yang dipesan habis dan menawarkan alternatif.",
    ],
    "Interaksi Lingkungan & Keluarga": [
        "Warga menelepon Pak RT/RW untuk menanyakan jadwal kerja bakti atau prosedur pembuatan surat pengantar.",
        "Penelepon menanyakan kabar dan bertukar cerita ringan dengan kerabat di luar kota, menanyakan kapan akan 'pulang kampung'.",
        "Penelepon mengundang kerabatnya untuk datang ke acara syukuran/tahlilan di rumahnya.",
        "Orang tua murid menelepon wali kelas untuk menginformasikan anaknya izin tidak masuk sekolah karena sakit."
    ],
    "Layanan Janji Temu (Appointment)": [
        "Resepsionis klinik mengingatkan jadwal janji temu dengan dokter gigi kepada pasien.",
        "Seseorang menelepon bengkel resmi untuk booking servis rutin kendaraan dan menanyakan ketersediaan spare part.",
        "Seseorang menelepon salon untuk reservasi potong rambut atau perawatan lainnya.",
    ],
    "Layanan Pesan Antar Makanan": [
        "Penelepon (kurir) mengonfirmasi alamat pengantaran dan patokannya kepada Penerima (pelanggan).",
        "Penelepon (pelanggan) bertanya mengenai status pesanannya kepada Penerima (restoran).",
        "Pelanggan menelepon restoran untuk komplain karena ada item pesanan yang salah atau kurang.",
    ],
    "Layanan Janji Temu (Appointment)": [
        "Penelepon ingin mengatur ulang jadwal pertemuannya dengan dokter/terapis.",
        "Penelepon (resepsionis) mengingatkan jadwal janji temu potong rambut kepada Penerima (pelanggan).",
        "Seseorang menelepon bengkel resmi untuk booking servis rutin kendaraan.",
        "Seseorang menelepon salon hewan (pet shop) untuk menjadwalkan grooming anjing/kucingnya.",
    ],
    "Konsultasi Pelanggan": [
        "Penelepon bertanya mengenai ketersediaan stok dan varian warna produk kepada toko online.",
        "Penelepon (pelanggan) meminta bantuan teknis karena produk elektronik yang baru dibeli tidak berfungsi.",
        "Seseorang menelepon agen properti untuk menanyakan detail sebuah rumah yang dikontrakkan.",
    ],
    "Layanan Transportasi Online": [
        "Penelepon (driver) mengabarkan sudah sampai di titik jemput.",
        "Penelepon (penumpang) bertanya posisi driver karena lokasi di aplikasi tidak sesuai.",
        "Penumpang menelepon driver (setelah perjalanan selesai) karena ada barang yang tertinggal di mobil.",
    ],
    "Layanan Publik & Pemerintah": [
        "Penelepon (warga) menelepon kantor kelurahan untuk menanyakan prosedur pembuatan surat keterangan.",
        "Penelepon (warga) menelepon call center penyedia layanan (PLN/PDAM) untuk melaporkan gangguan.",
        "Penelepon menanyakan jam besuk dan prosedur kunjungan ke sebuah rumah sakit.",
    ],
    "Layanan Rumah Tangga (Household Services)": [
        "Seseorang menelepon jasa servis AC untuk menjadwalkan pembersihan rutin.",
        "Seseorang menelepon tukang ledeng untuk menanyakan kemungkinan biaya perbaikan pipa bocor.",
        "Penelepon (pemilik kos) mengingatkan penyewa tentang tanggal jatuh tempo pembayaran sewa bulan depan.",
    ],
    "Interaksi Sekolah & Pendidikan": [
        "Orang tua murid menelepon wali kelas untuk menginformasikan anaknya tidak bisa masuk sekolah karena sakit.",
        "Pihak sekolah (tata usaha) menelepon orang tua untuk mengonfirmasi pembayaran SPP.",
        "Mahasiswa menelepon perpustakaan kampus untuk menanyakan ketersediaan buku.",
    ],
    "Transaksi Jual Beli (Routine Shopping)": [
        "Penelepon (calon pembeli) menawar harga barang yang diiklankan di marketplace.",
        "Penelepon (penjual) mengonfirmasi pembayaran dan alamat pengiriman kepada pembeli.",
    ],
    "Pertanyaan Transportasi (Transportation Inquiry)": [
        "Penelepon menghubungi stasiun kereta api untuk menanyakan jadwal keberangkatan.",
        "Penelepon menghubungi agen travel untuk menanyakan harga tiket bus antarkota.",
    ],
    "Interaksi Keluarga & Teman": [
        "Penelepon menanyakan kabar dan bertukar cerita ringan dengan kerabat di luar kota.",
        "Penelepon mengucapkan selamat ulang tahun dan mendoakan yang terbaik untuk temannya.",
        "Penelepon meminta tolong teman untuk dijemput karena kendaraannya mogok.",
        "Penelepon mengundang kerabatnya untuk datang ke acara syukuran di rumahnya.",
    ],
    "Koordinasi Pekerjaan/Akademis": [
        "Penelepon mendiskusikan pembagian tugas untuk proyek kantor dengan rekan kerja.",
        "Penelepon (mahasiswa) bertanya kepada temannya mengenai tugas kuliah yang belum dipahami.",
        "Atasan menelepon bawahan untuk memberikan arahan singkat atau melakukan follow-up terhadap suatu tugas.",
    ],
    "Layanan Publik & Komersial": [
        "Pelanggan menelepon call center PLN/PDAM untuk melaporkan gangguan listrik/air.",
        "Calon pembeli menelepon agen properti untuk menanyakan detail sebuah rumah yang dikontrakkan.",
        "Penelepon bertanya mengenai ketersediaan stok dan promo yang berlaku kepada sebuah toko elektronik.",
        "Pihak sekolah (tata usaha) menelepon orang tua untuk mengonfirmasi pembayaran SPP yang sudah jatuh tempo."
    ],
}


def build_prompt_revised(scenario_category, scenario_detail, label):
    fraud_example_pool = [
        """### CONTOH
Konteks Skenario: Penipuan Phishing & Malware (APK Paling Viral)
Detail spesifik: Penipu mengaku dari jasa pengiriman (JNE/J&T/Anteraja), mengirim 'foto resi paket' dalam format file .APK.
### DIALOG HASIL:
Penipu: Selamat siang, dengan Ibu Rina?
Korban: Iya benar, ini siapa ya?
Penipu: Saya Budi dari J&T Express, Bu. Mau konfirmasi paket, sepertinya alamat Ibu kurang jelas di sistem kami.
Korban: Oh ya? Perasaan alamat saya sudah benar.
Penipu: Untuk memastikan, bisa saya kirimkan foto paket dan resinya via WhatsApp Bu? Biar tidak salah kirim.
Korban: Boleh, Mas. Kirim saja.
Penipu: Baik, sudah saya kirim ya Bu. Filenya dalam bentuk aplikasi Lihat Resi, mohon di-install dulu Bu untuk melihat fotonya.
Korban: Loh kok aplikasi? Bukan foto biasa?
Penipu: Iya Bu, ini sistem keamanan baru dari pusat. Lebih aman katanya. Ditunggu ya Bu konfirmasinya.
Korban: Hmm ya sudah saya coba.""",
        """### CONTOH
Konteks Skenario: Penipuan Perbankan (Modus Klasik & Baru)
Detail spesifik: Penipu menyamar sebagai staf bank (BCA), mengabarkan ada 'perubahan tarif transfer menjadi Rp150.000/bulan'.
### DIALOG HASIL:
Penipu: Selamat pagi, kami dari HaloBCA. Berbicara dengan Bapak Wijoyo?
Korban: Pagi. Iya, saya sendiri.
Penipu: Baik Bapak Wijoyo, kami informasikan sesuai kebijakan baru Bank Indonesia, per besok biaya transaksi bulanan Bapak akan berubah menjadi seratus lima puluh ribu rupiah per bulan.
Korban: Hah? Kok mahal sekali? Saya tidak mau.
Penipu: Kami paham, Pak. Jika Bapak tidak setuju dan ingin tetap menggunakan skema tarif lama, Bapak bisa mengisi formulir pembatalan online. Linknya sudah kami kirimkan via SMS, Pak.
Korban: Oh ada linknya? Oke oke saya isi.
Penipu: Silakan diisi segera ya Pak, karena formulir hanya valid selama 10 menit. Nanti akan ada kode yang masuk ke HP Bapak, mohon diinformasikan ke kami untuk verifikasi.
Korban: Oke, saya cek SMSnya.""",
        """### CONTOH
Konteks Skenario: Penipuan Lowongan Kerja Fiktif (Part-Time & Remote)
Detail spesifik: Penipu menawarkan pekerjaan paruh waktu mudah seperti 'Like & Subscribe YouTube'.
### DIALOG HASIL:
Penipu: Halo kak, perkenalkan saya Siska dari Digital Media. Kami sedang butuh partner untuk kerja sampingan, hanya like dan subscribe channel YouTube saja. Komisinya 50 ribu per tugas, tertarik?
Korban: Oh ya? Kerjanya gimana tuh?
Penipu: Gampang kak, nanti saya kasih link channelnya. Kakak cukup like, subscribe, terus screenshot kirim ke saya. Nanti komisi langsung cair.
Korban: Wah, enak banget. Boleh deh.
Penipu: Oke. Untuk 3 tugas pertama gratis kak. Tapi untuk bisa ambil tugas selanjutnya dengan komisi lebih besar, kakak perlu upgrade keanggotaan premium dengan deposit 200 ribu. Nanti uangnya kembali kok setelah 10 tugas.
Korban: Oh harus deposit dulu ya?
Penipu: Iya kak, untuk jaminan saja. Semua member premium juga begitu kok. Mau dicoba kak?"""
    ]
    
    normal_example_pool = [
        """### CONTOH
Konteks Skenario: Layanan Pesan Antar Makanan & Transportasi Online
Detail spesifik: Driver Gojek/Grab mengonfirmasi alamat pengantaran dan patokannya kepada pelanggan.
### DIALOG HASIL:
Penelepon: Halo, selamat siang. Saya driver Gojek, sudah di titik jemput ya, Pak. Di depan Indomaret.
Penerima: Oh iya, Mas. Saya sudah lihat. Pakai jaket hijau kan?
Penelepon: Betul, Pak. Saya di dekat motor Vario hitam.
Penerima: Oke, saya ke sana sekarang. Tunggu sebentar ya.
Penelepon: Siap, Pak. Ditunggu.""",
        """### CONTOH
Konteks Skenario: Layanan Janji Temu (Appointment)
Detail spesifik: Resepsionis klinik mengingatkan jadwal janji temu dengan dokter gigi kepada pasien.
### DIALOG HASIL:
Penelepon: Selamat sore, Klinik Gigi Sehat. Bisa bicara dengan Ibu Amanda?
Penerima: Sore, iya saya sendiri.
Penelepon: Ibu Amanda, saya hanya ingin mengingatkan untuk jadwal scaling gigi Ibu dengan Dokter Wira besok jam 3 sore ya.
Penerima: Oh iya betul, Mbak. Terima kasih sudah diingatkan.
Penelepon: Baik, Bu. Diharapkan datang 15 menit lebih awal untuk registrasi ya.
Penerima: Siap, Mbak. Terima kasih.
Penelepon: Sama-sama, Bu. Selamat sore."""
    ]
    
    if label == 1:
        chosen_example = random.choice(fraud_example_pool)
    else:
        chosen_example = random.choice(normal_example_pool)

    main_instruction = """Anda adalah MESIN TRANSKRIPSI OTOMATIS yang sangat akurat. Tugas Anda adalah membuat transkrip percakapan telepon yang 100% bersih berdasarkan konteks.

ATURAN MUTLAK:
1.  Format WAJIB adalah `Nama Peran: Ucapan`. Contoh: `Penipu: Halo`.
2.  JANGAN PERNAH menggunakan format tebal, miring, atau markdown lainnya.
3.  JANGAN PERNAH menulis deskripsi tindakan, emosi, atau pikiran di dalam tanda kurung seperti `(curiga)` atau `(tertawa)`.
4.  JANGAN PERNAH menambahkan deskripsi alias atau sub-peran dalam kurung setelah nama peran. Contoh terlarang: `Penipu (Staf Bank):`.
5.  JANGAN PERNAH menulis paragraf narasi atau ringkasan cerita.
6.  Ucapan karakter HARUS realistis. Karakter tidak boleh 'sadar' mereka dalam dialog atau mengumumkan 'ini penipuan'.
7.  Untuk semua data sensitif gunakan data dummy. Contoh: `08123456789` atau t.co/DummyLink.
Output Anda HARUS sebuah transkrip murni.
"""
    
    final_prompt = f"""{main_instruction}
{chosen_example}

### TUGAS BARU
Konteks Skenario: {scenario_category}
Detail spesifik: {scenario_detail}
### DIALOG HASIL:
"""
    return final_prompt


def generate_dialog(prompt):
    """Menghasilkan dialog menggunakan Gemini API."""
    try:
        model = genai.GenerativeModel(MODEL)
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=2048,
                top_p=1.0,
                top_k=40,
            )
        )
        return response.text.strip()
    except Exception as e:
        print(f"\nError saat menghubungi Gemini API: {e}")
        return None

def clean_dialogue(text):
    """
    Membersihkan teks dialog secara paksa dari format yang tidak diinginkan
    sebagai jaring pengaman terakhir.
    """
    if not text:
        return None
    
    cleaned_text = re.sub(r'\*\*', '', text)
    
    cleaned_text = re.sub(r'\s*\([^)]*\)', '', cleaned_text)
    
    lines = cleaned_text.split('\n')
    pure_dialog_lines = [line for line in lines if ':' in line]
    cleaned_text = '\n'.join(pure_dialog_lines)
    
    return cleaned_text.strip()

def main():
    """Fungsi utama untuk membuat dataset dialog."""

    start_from_id = 1 

    file_exists = os.path.isfile(CSV_FILENAME)

    with open(CSV_FILENAME, "a", newline='', encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=["id", "kategori_skenario", "detail_skenario", "label", "dialog"]
        )
        
        if not file_exists:
            writer.writeheader()
        
        all_scenarios = []
        for category, details in fraud_scenarios.items():
            for detail in details:
                all_scenarios.append({'category': category, 'detail': detail, 'label': 1})
        for category, details in nonfraud_scenarios.items():
            for detail in details:
                all_scenarios.append({'category': category, 'detail': detail, 'label': 0})
        
        dialog_counter = 0
        total_dialogs_generated_this_run = 0

        for scenario in all_scenarios:
            for i in range(DIALOGS_PER_SCENARIO):
                dialog_counter += 1
                
                if dialog_counter < start_from_id:
                    continue

                label_text = "Penipuan" if scenario['label'] == 1 else "Normal"
                print(f"  > Membuat dialog ID {dialog_counter} (Iterasi ke-{i+1}/{DIALOGS_PER_SCENARIO} untuk skenario: '{scenario['detail']}')")

                prompt = build_prompt_revised(scenario['category'], scenario['detail'], scenario['label'])
                
                raw_dialog = generate_dialog(prompt)
                
                final_dialog = clean_dialogue(raw_dialog)
                
                if final_dialog:
                    writer.writerow({
                        "id": dialog_counter,
                        "kategori_skenario": scenario['category'],
                        "detail_skenario": scenario['detail'],
                        "label": scenario['label'],
                        "dialog": final_dialog
                    })
                    print(f"  > Dialog {dialog_counter} ({label_text}) berhasil dibuat & dibersihkan.")
                    total_dialogs_generated_this_run += 1
                else:
                    print(f"  > GAGAL membuat atau membersihkan dialog untuk skenario: {scenario['detail']}.")
                
                time.sleep(2)
                
    print(f"\nSelesai! {total_dialogs_generated_this_run} dialog baru telah dibuat dan ditambahkan ke file '{CSV_FILENAME}'")

if __name__ == "__main__":
    main()