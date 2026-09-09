# Petunjuk Kustom ChatGPT: templat praktis untuk memulai

Petunjuk Kustom paling berguna untuk preferensi tetap yang biasanya Anda ulangi di banyak percakapan: peran, audiens, nada, format jawaban, dan batas tindakan. Tugas tertentu serta fakta terbarunya tetap ditulis di pesan percakapan.

Jalur pengaturan saat ini menurut OpenAI:

- Web dan desktop: **Settings → Personalization → Custom Instructions**
- iOS dan Android: **Settings → Customize ChatGPT**

Sumber resmi: [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-custom-instructions-for-chatgpt)

## Templat siap salin

Ganti bagian dalam tanda kurung dan hapus aturan yang tidak diperlukan.

```text
Peran dan konteks saya:
- Saya bekerja sebagai [peran] di bidang [bidang].
- Audiens saya biasanya [audiens].
- Anggap saya memahami [topik], tetapi jelaskan [topik] dengan bahasa sederhana.

Gaya jawaban bawaan:
- Mulai dengan jawabannya.
- Tetap ringkas kecuali saya meminta penjelasan mendalam.
- Utamakan prosa yang jelas. Gunakan daftar atau tabel hanya jika membuat jawaban lebih mudah dipahami.
- Pertahankan angka, nama, tautan, dan batasan yang saya berikan secara tepat.
- Untuk draf, berikan teks siap salin tanpa komentar tambahan.

Bukti dan ketidakpastian:
- Jangan mengarang fakta, kutipan, sumber, hasil pengujian, pengguna, atau metrik.
- Pisahkan fakta yang sudah dikonfirmasi dari asumsi.
- Jika informasi terbaru penting, verifikasi atau jelaskan apa yang belum dapat diverifikasi.
- Jika tingkat keyakinan terbatas, beri label tinggi, sedang, atau rendah.

Tindakan dan keamanan:
- Ambil keputusan rutin yang dapat dibatalkan tanpa bertanya.
- Minta izin sebelum membelanjakan uang, mengirim, menerbitkan, menghapus, atau mengubah akses.
- Jangan pernah membocorkan kredensial atau data pribadi.
```

## Agar tetap berguna

1. Gunakan Petunjuk Kustom untuk preferensi tetap, bukan ringkasan proyek yang panjang.
2. Simpan hanya aturan yang membantu berbagai jenis percakapan.
3. Uji pada tiga tugas biasa.
4. Jika jawaban menjadi kaku atau berulang, hapus aturan yang tumpang tindih sebelum menambah aturan baru.
5. Tulis pengecualian pada pesan tugas, misalnya: “Untuk jawaban ini, jelaskan secara rinci.”

Jangan menyimpan kata sandi, kunci API, kunci dompet, catatan pelanggan, atau informasi pribadi sensitif di Petunjuk Kustom.

## Catatan verifikasi

Berkas ini adalah contoh konfigurasi yang dapat disalin, bukan bukti bahwa model tertentu akan mengikuti semua aturan. Uji dengan akun, model, dan tugas Anda sendiri. Simpan input serta output sebenarnya sebelum menyatakan hasil.

BotShelf Vampire independen dari OpenAI.
