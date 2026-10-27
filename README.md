# Simulasi Pesan Aman: Diffie-Hellman & ElGamal (Tiara, Diva, & Oscar)

---

## Cara Menjalankan Program

1. Buka terminal di folder project ini:
   ```bash
   python server.py
   ```
2. Buka browser favoritmu (Chrome / Edge / Firefox) dan akses:
   👉 **`http://localhost:8000`**
3. Tampilan pesan akan terbuka dan sesi kriptografi disiapkan otomatis.
4. Isi nama **Dari**, **Kepada**, dan isi pesan, lalu tekan **Kirim pesan**.
5. Pada setiap pesan, panel **Oscar menyadap jaringan** menampilkan ciphertext dan tag integritas (tag bukan ciphertext), tanpa isi asli. Tekan **Coba baca sebagai Oscar** untuk melihat mengapa paket tidak dapat dibaca tanpa kunci privat penerima.
6. Pesan hasil dekripsi dan status integritas tampil langsung pada kartu pesan. Di bawahnya, panel Oscar menunjukkan data yang dapat disadap. Buka **Lihat rincian tahapan Diffie–Hellman & ElGamal** untuk melihat fungsi Tahap 0–6 serta nilai hitungannya.

Parameter dan pembangkitan kunci diproses otomatis oleh backend. Nama pengirim dan penerima dapat diganti sebagai label tampilan, tetapi backend masih memakai satu kunci penerima demo (Diva). Sesi memakai parameter demo 32-bit agar karakter Unicode umum dapat diproses. Program ini menggunakan pustaka standar Python dan HTML, CSS, serta JavaScript tanpa framework atau library eksternal. Simulasi ini untuk pembelajaran, bukan layanan pesan sungguhan atau kriptografi siap produksi.

---

## Struktur File Proyek

| Nama File | Peran & Deskripsi |
| :--- | :--- |
| **`crypto_core.py`** | **Otak Matematika Kriptografi murni**: berisi implementasi manual *Square-and-Multiply*, *Extended Euclidean*, *Miller-Rabin Primality*, *Sophie Germain Safe Prime*, *Primitive Root Generator*, *Diffie-Hellman*, dan *ElGamal*. |
| **`server.py`** | Server web lokal menggunakan pustaka standar bawaan Python (`http.server` & `json`) tanpa memerlukan library eksternal. |
| **`index.html`** | Antarmuka pesan dengan isian pengirim, penerima, dan isi pesan. |
| **`style.css`** | Tampilan responsif dengan riwayat pesan dan tahapan kriptografi yang dapat dibuka. |
| **`app.js`** | Logika kirim pesan, status verifikasi, dan penjelasan setiap tahap melalui REST API Python. |

---

## Tahapan 0–6 Kriptografi (Untuk Penjelasan ke Dosen)

### Tahap 0: Parameter Publik $(p, g)$
- Mencari bilangan prima aman (*Safe Prime*) berorde tinggi: $p = 2q + 1$, di mana $q$ juga bilangan prima (Sophie Germain).
- Mencari generator akar primitif $g$ dengan menguji bahwa $g^2 \not\equiv 1 \pmod p$ dan $g^q \not\equiv 1 \pmod p$.
- Nilai $p$ dan $g$ disebarkan secara publik ke jaringan.

### Tahap 1: Diffie-Hellman Key Exchange (Kesepakatan Kunci Sesi)
- **Tiara** memilih integer rahasia $a \in [2, p-2]$, lalu menghitung kunci publik $A = g^a \pmod p$.
- **Diva** memilih integer rahasia $b \in [2, p-2]$, lalu menghitung kunci publik $B = g^b \pmod p$.
- Tiara dan Diva saling menukar $A$ dan $B$ melalui jaringan publik.
- **Kunci Sesi Rahasia Bersama ($K$):**
  $$\text{Tiara: } K = B^a \pmod p = (g^b)^a \pmod p = g^{ab} \pmod p$$
  $$\text{Diva: } K = A^b \pmod p = (g^a)^b \pmod p = g^{ab} \pmod p$$
  Kedua pihak memiliki kunci rahasia $K$ yang persis sama tanpa pernah mengirimkan nilai $K$ ke jaringan!

### Tahap 2: Pembangkitan Kunci ElGamal Diva
- Diva memilih kunci privat rahasia $x \in [2, p-2]$.
- Diva menghitung kunci publik ElGamal miliknya: $y = g^x \pmod p$.
- Pasangan kunci Diva: Kunci Privat = $x$ (hanya Diva yang tahu), Kunci Publik = $(p, g, y)$ (publik).

### Tahap 3: Tiara Mengenkripsi Pesan (ElGamal) & Menandatangani Tag
- Untuk setiap karakter dengan kode ASCII $m$:
  1. Tiara memilih bilangan acak sesaat (*ephemeral key*) $k \in [2, p-2]$.
  2. Menghitung $c_1 = g^k \pmod p$.
  3. Menghitung rahasia sesaat $s = y^k \pmod p$.
  4. Menghitung ciphertext karakter: $c_2 = (m \cdot s) \pmod p$.
- Tiara membubuhkan Tag otentikasi integritas menggunakan kunci sesi Diffie-Hellman $K$:
  $$\text{Tag} = (\text{Checksum}(M) \times K) \pmod p$$

### Tahap 4: Penyadapan di Jaringan oleh Oscar
- Pada panel Oscar, setiap **Blok** menampilkan ciphertext ElGamal $(c_1, c_2)$. **Tag integritas** ditampilkan terpisah dan bukan bagian dari ciphertext.
- Dalam model ElGamal, pihak yang hanya melihat ciphertext tidak memiliki kunci privat penerima untuk mendekripsinya. Rincian tahap untuk pembelajaran juga menampilkan nilai rahasia agar perhitungannya dapat diperiksa.
- **Mengapa Oscar Gagal Membaca Pesan?**
  Oscar membutuhkan $s = c_1^x \pmod p$, tetapi tidak memiliki $x$. Pada penggunaan nyata, tingkat kesulitannya bergantung pada ukuran parameter dan implementasi; ukuran demo 32-bit di program ini tidak aman untuk melindungi pesan sungguhan.

### Tahap 5: Diva Mendekripsi Pesan
- Diva menggunakan kunci privat rahasianya $x$:
  1. Diva menghitung rahasia bersama sesaat: $s = c_1^x \pmod p = (g^k)^x = g^{kx} = (g^x)^k = y^k \pmod p$.
  2. Diva mencari invers perkalian modular $s^{-1} \pmod p$ menggunakan **Extended Euclidean Algorithm**:
     $$s \cdot s^{-1} \equiv 1 \pmod p$$
  3. Diva memulihkan kode karakter asli $m$:
     $$m = (c_2 \cdot s^{-1}) \pmod p = ((m \cdot s) \cdot s^{-1}) \pmod p = m$$
  4. Mengonversi angka $m$ kembali menjadi huruf aslinya.

### Tahap 6: Diva Memverifikasi Integritas Pesan
- Diva menghitung ulang ringkasan pesan yang didekripsi:
  $$\text{Tag}_{\text{Diva}} = (\text{Checksum}(M_{\text{dekripsi}}) \times K) \pmod p$$
- Diva membandingkan $\text{Tag}_{\text{terima}} == \text{Tag}_{\text{Diva}}$:
  - **Jika Cocok:** Tag pada simulasi cocok dengan hasil hitung ulang.
  - **Jika Berbeda:** Simulasi menandai pesan sebagai berubah atau tag tidak cocok.
- Tag ini adalah checksum sederhana untuk demonstrasi, bukan MAC atau tanda tangan digital yang aman. Jadi, hasil cocok pada program ini bukan jaminan keaslian pesan untuk penggunaan nyata.
