# Simulasi Chat Aman: Diffie-Hellman & ElGamal (Tiara, Diva, & Oscar)

---

## Cara Menjalankan Program

1. Buka terminal di folder project ini:
   ```bash
   python server.py
   ```
2. Buka browser favoritmu (Chrome / Edge / Firefox) dan akses:
   👉 **`http://localhost:8000`**
3. Aplikasi web langsung aktif! Kamu bisa:
   - Mengubah ukuran bit prima $p$ (16, 32, 48, 64-bit) & seed acak.
   - Mengamati kesepakatan kunci Diffie-Hellman ($K_{\text{Tiara}} = K_{\text{Diva}}$).
   - Mengetik pesan rahasia di kolom Tiara dan menekan tombol **"Enkripsi & Kirim"**.
   - Melihat inspeksi data yang dicegat di jaringan oleh Oscar (Tahap 4).
   - Melihat tabel kalkulasi matematika lengkap per karakter ($m, k, c_1, s, c_2, s^{-1}, m_{\text{dec}}$).

---

## Struktur File Proyek

| Nama File | Peran & Deskripsi |
| :--- | :--- |
| **`crypto_core.py`** | **Otak Matematika Kriptografi murni**: berisi implementasi manual *Square-and-Multiply*, *Extended Euclidean*, *Miller-Rabin Primality*, *Sophie Germain Safe Prime*, *Primitive Root Generator*, *Diffie-Hellman*, dan *ElGamal*. |
| **`server.py`** | Server web lokal menggunakan pustaka standar bawaan Python (`http.server` & `json`) tanpa memerlukan library eksternal. |
| **`index.html`** | Antarmuka pengguna (UI) semantik web: **Tiara (Pengirim)**, **Oscar (Penyadap / Jaringan)**, dan **Diva (Penerima)**. |
| **`style.css`** | Desain visual bertema minimalis dan bersih (Vanilla CSS). |
| **`app.js`** | Logika interaktif frontend (Vanilla JavaScript) untuk inspektor matematis dan komunikasi REST API ke Python. |

---

## Alur 6 Tahapan Kriptografi (Untuk Penjelasan ke Dosen)

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
- Oscar menyadap semua data di jaringan: parameter $(p, g)$, kunci publik DH $(A, B)$, kunci publik ElGamal $y$, dan paket pesan $((c_1, c_2), \text{Tag})$.
- **Mengapa Oscar Gagal Membaca Pesan?**
  Oscar membutuhkan $s = c_1^x \pmod p$, tetapi Oscar tidak memiliki $x$. Untuk mendapatkan $x$ dari $y = g^x \pmod p$ atau mendapatkan $k$ dari $c_1 = g^k \pmod p$, Oscar harus memecahkan **Discrete Logarithm Problem (DLP)**, yang secara komputasi mustahil diselesaikan dalam waktu wajar.

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
  - **Jika Cocok (Valid):** Pesan dijamin asli dari Tiara dan tidak pernah diubah di jaringan.
  - **Jika Berbeda (Tampered):** Pesan telah diubah/dirusak oleh Oscar saat transit di jaringan!
