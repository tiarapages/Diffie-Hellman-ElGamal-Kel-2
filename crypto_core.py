"""
Modul Inti Kriptografi: Diffie-Hellman & ElGamal
Dibuat 100% TANPA library atau framework eksternal kriptografi.
Semua algoritma matematika ditulis secara mandiri dari prinsip dasar:
  - mod_pow: Perpangkatan modular (Square-and-Multiply) O(log e)
  - egcd & mod_inverse: Extended Euclidean Algorithm
  - is_prime: Uji bilangan prima Miller-Rabin deterministik
  - PRNG: Pembangkit bilangan acak xorshift64
  - buat_safe_prime & cari_generator: Safe prime p = 2q + 1 & primitive root g
  - Diffie-Hellman Key Exchange (Alice & Bob)
  - ElGamal Key Generation, Encryption, Decryption (Bob & Alice)
  - Integritas pesan (Checksum bertag Kunci Sesi DH)
"""

MASK64 = (1 << 64) - 1


# ======================================================================
# 1. FUNGSI MATEMATIKA DASAR
# ======================================================================

def mod_pow(basis, eksp, modulus):
    """
    Perpangkatan modular: (basis ^ eksp) mod modulus.
    Menggunakan algoritma Square-and-Multiply (Binary Exponentiation).
    Kompleksitas: O(log eksp).
    """
    if modulus == 1:
        return 0
    hasil = 1
    basis = basis % modulus
    while eksp > 0:
        if eksp & 1:  # Jika bit ganjil / bit terendah adalah 1
            hasil = (hasil * basis) % modulus
        basis = (basis * basis) % modulus  # Kuadratkan basis
        eksp >>= 1                         # Geser 1 bit ke kanan
    return hasil


def egcd(a, b):
    """
    Extended Euclidean Algorithm.
    Mengembalikan tuple (g, x, y) sehingga a*x + b*y = g = gcd(a, b).
    """
    x0, y0, x1, y1 = 1, 0, 0, 1
    while b != 0:
        q = a // b
        a, b = b, a - q * b
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return a, x0, y0


def mod_inverse(a, m):
    """
    Invers perkalian modular: a^(-1) mod m.
    Syarat: gcd(a, m) == 1.
    """
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError(f"Invers modular tidak ada karena gcd({a}, {m}) = {g} != 1")
    return x % m


# Basis prima kecil untuk uji Miller-Rabin deterministik hingga batas besar
KECIL = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]


def is_prime(n):
    """
    Uji bilangan prima Miller-Rabin dengan basis bilangan prima kecil.
    Deterministik untuk bilangan n < 3.3 x 10^24.
    """
    if n < 2:
        return False
    for p in KECIL:
        if n % p == 0:
            return n == p

    # Tulis n - 1 sebagai 2^r * d dengan d ganjil
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1

    # Uji untuk setiap basis saksi (witness)
    for a in KECIL:
        x = mod_pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


class PRNG:
    """
    Pembangkit Bilangan Acak Semu (Pseudo-Random Number Generator) xorshift64.
    Dibuat mandiri untuk simulasi edukasi kriptografi tanpa modul 'random'.
    """

    def __init__(self, seed=20241027):
        self.s = (int(seed) & MASK64) or 88172645463325252

    def _next(self):
        x = self.s
        x ^= (x << 13) & MASK64
        x ^= x >> 7
        x ^= (x << 17) & MASK64
        self.s = x
        return x

    def bits(self, n):
        """Menghasilkan bilangan acak integer tak bertanda berukuran n-bit."""
        hasil = 0
        terkumpul = 0
        while terkumpul < n:
            hasil = (hasil << 64) | self._next()
            terkumpul += 64
        return hasil >> (terkumpul - n)

    def rentang(self, lo, hi):
        """Menghasilkan integer acak dalam rentang inklusif [lo, hi]."""
        if lo > hi:
            lo, hi = hi, lo
        span = hi - lo + 1
        return lo + (self.bits(span.bit_length() + 64) % span)


def buat_safe_prime(bit, rng):
    """
    Menghasilkan bilangan prima aman (safe prime) p = 2*q + 1,
    di mana q juga merupakan bilangan prima (Sophie Germain prime).
    Ukuran bit p adalah 'bit'.
    """
    while True:
        # q adalah ganjil dengan bit tertinggi aktif
        q = rng.bits(bit - 1) | (1 << (bit - 2)) | 1
        if is_prime(q):
            p = 2 * q + 1
            if is_prime(p):
                return p, q


def cari_generator(p, q):
    """
    Mencari generator (primitive root) modulo safe prime p = 2*q + 1.
    Karena pembagi dari phi(p) = p - 1 = 2*q hanyalah 1, 2, q, 2*q,
    maka g adalah generator jika dan hanya jika:
      g^2 mod p != 1  DAN  g^q mod p != 1.
    """
    g = 2
    while True:
        if mod_pow(g, 2, p) != 1 and mod_pow(g, q, p) != 1:
            return g
        g += 1


def hitung_checksum(teks, p):
    """
    Menghitung representasi ringkasan (checksum polinomial berbobot) dari teks modulo p.
    Digunakan untuk demonstrasi otentikasi pesan (Message Authentication Code sederhana).
    """
    total = 0
    for i, ch in enumerate(teks):
        total = (total + (i + 1) * ord(ch)) % p
    return total


# ======================================================================
# 2. DIFFIE-HELLMAN KESEPAKATAN KUNCI (TAHAP 1)
# ======================================================================

def dh_generate_party(p, g, rng):
    """
    Membangkitkan kunci privat rahasia (private_key) dan kunci publik (public_key).
      private in [2, p - 2]
      public = g^private mod p
    """
    priv = rng.rentang(2, p - 2)
    pub = mod_pow(g, priv, p)
    return priv, pub


def dh_compute_shared_secret(public_other, private_self, p):
    """
    Menghitung kunci bersama (shared secret key):
      K = (public_other ^ private_self) mod p
    """
    return mod_pow(public_other, private_self, p)


# ======================================================================
# 3. ELGAMAL ASIMETRIK (TAHAP 2, 3, 5)
# ======================================================================

def elgamal_keygen(p, g, rng):
    """
    Bob membangkitkan pasangan kunci ElGamal:
      Kunci privat Bob: x in [2, p - 2]
      Kunci publik Bob: y = g^x mod p
    Parameter publik Bob yang disebarkan: (p, g, y)
    """
    x = rng.rentang(2, p - 2)
    y = mod_pow(g, x, p)
    return x, y


def elgamal_encrypt_char(m, p, g, y, rng):
    """
    Alice mengenkripsi satu unit karakter (kode angka m) menggunakan kunci publik Bob (p, g, y):
      1. Pilih bilangan acak ephemeral k in [2, p - 2]
      2. Hitung c1 = g^k mod p (kunci ephemeral publik untuk Bob)
      3. Hitung shared secret s = y^k mod p
      4. Hitung c2 = (m * s) mod p (pesan terselubung)
    Kembalikan: (k, c1, s, c2)
    """
    k = rng.rentang(2, p - 2)
    c1 = mod_pow(g, k, p)
    s = mod_pow(y, k, p)
    c2 = (m * s) % p
    return k, c1, s, c2


def elgamal_decrypt_char(c1, c2, x, p):
    """
    Bob mendekripsi blok cipher (c1, c2) menggunakan kunci privat rahasianya x:
      1. Hitung shared secret s = c1^x mod p
         (Secara matematis: c1^x = (g^k)^x = g^(k*x) = (g^x)^k = y^k = s)
      2. Hitung invers modular dari s modulo p: s_inv = s^(-1) mod p
      3. Pulihkan pesan m = (c2 * s_inv) mod p
    Kembalikan: (s, s_inv, m)
    """
    s = mod_pow(c1, x, p)
    s_inv = mod_inverse(s, p)
    m = (c2 * s_inv) % p
    return s, s_inv, m


# ======================================================================
# 4. SIMULASI TRANSAKSI LENGKAP UNTUK DEMO CHAT TIARA - DIVA - OSCAR
# ======================================================================

def proses_transaksi_chat(pesan, p, g, alice_priv_dh, bob_priv_dh, bob_pub_dh, alice_pub_dh,
                          K_session, bob_priv_elgamal, bob_pub_elgamal, rng,
                          tamper=False, tamper_index=0, tamper_type="c2"):
    """
    Menjalankan alur lengkap pertukaran pesan dari Tiara ke Diva melalui jaringan Oscar:
      Tahap 3: Tiara mengenkripsi pesan dan membuat tag verifikasi memakai K
      Tahap 4: Oscar menyadap data di jaringan (dan manipulasi jika tamper=True)
      Tahap 5: Diva mendekripsi ciphertext yang diterimanya
      Tahap 6: Diva memverifikasi tag otentikasi
    """
    # ------------------ TAHAP 3: TIARA ENKRIPSI ------------------
    encrypted_blocks = []
    for idx, ch in enumerate(pesan):
        m = ord(ch)
        k, c1, s, c2 = elgamal_encrypt_char(m, p, g, bob_pub_elgamal, rng)
        encrypted_blocks.append({
            "index": idx + 1,
            "char": ch,
            "m": m,
            "k": k,
            "c1": c1,
            "s_alice": s,
            "c2": c2
        })

    original_checksum = hitung_checksum(pesan, p)
    alice_tag = (original_checksum * K_session) % p

    # ------------------ TAHAP 4: TRANSMISI JARINGAN (OSCAR MENYADAP) ------------------
    # Salin blok untuk transmisi jaringan
    transmitted_blocks = []
    for b in encrypted_blocks:
        transmitted_blocks.append({
            "index": b["index"],
            "c1": b["c1"],
            "c2": b["c2"]
        })
    transmitted_tag = alice_tag
    tamper_applied = False
    tamper_description = "Data transit aman tanpa gangguan pihak ketiga."

    if tamper and len(transmitted_blocks) > 0:
        tamper_idx = max(0, min(tamper_index, len(transmitted_blocks) - 1))
        tamper_applied = True
        if tamper_type == "c2":
            old_val = transmitted_blocks[tamper_idx]["c2"]
            # Ubah nilai c2 dengan menambahkan nilai acak kecil
            new_val = (old_val + 7) % p
            transmitted_blocks[tamper_idx]["c2"] = new_val
            tamper_description = f"Oscar menyabotase blok #{tamper_idx+1}: Nilai c2 diubah dari {old_val} menjadi {new_val}."
        elif tamper_type == "c1":
            old_val = transmitted_blocks[tamper_idx]["c1"]
            new_val = (old_val + 3) % p
            transmitted_blocks[tamper_idx]["c1"] = new_val
            tamper_description = f"Oscar menyabotase blok #{tamper_idx+1}: Nilai c1 diubah dari {old_val} menjadi {new_val}."
        elif tamper_type == "tag":
            old_tag = transmitted_tag
            transmitted_tag = (old_tag + 13) % p
            tamper_description = f"Oscar merusak Tag verifikasi: Dari {old_tag} menjadi {transmitted_tag}."

    # Data yang bisa dilihat oleh Oscar
    eve_intercepted = {
        "public_parameters": {
            "p": str(p),
            "g": str(g),
            "alice_dh_public": str(alice_pub_dh),
            "bob_dh_public": str(bob_pub_dh),
            "bob_elgamal_public": str(bob_pub_elgamal)
        },
        "intercepted_packets": [
            {"block": b["index"], "c1": str(b["c1"]), "c2": str(b["c2"])}
            for b in transmitted_blocks
        ],
        "intercepted_tag": str(transmitted_tag),
        "why_eve_fails": (
            f"Oscar melihat c1 dan c2 untuk setiap karakter, serta y = {bob_pub_elgamal} dan g = {g}.\n"
            f"Untuk mendekripsi, Oscar membutuhkan s = c1^x mod p.\n"
            f"Namun Oscar TIDAK mengetahui kunci privat Diva (x).\n"
            f"Untuk mencari x dari y = g^x mod p, Oscar harus memecahkan Masalah Logaritma Diskrit "
            f"(Discrete Logarithm Problem / DLP) pada modulo prima p sebesar {p.bit_length()}-bit, "
            f"yang secara komputasi tidak praktis (intractable)!"
        ),
        "tamper_applied": tamper_applied,
        "tamper_description": tamper_description
    }

    # ------------------ TAHAP 5: DIVA MENDEKRIPSI ------------------
    decrypted_blocks = []
    decrypted_chars = []
    for b in transmitted_blocks:
        c1 = b["c1"]
        c2 = b["c2"]
        s_bob, s_inv_bob, m_dec = elgamal_decrypt_char(c1, c2, bob_priv_elgamal, p)
        # Konversi angka modulo kembali ke karakter (jika karakter valid)
        try:
            char_dec = chr(m_dec) if 0 <= m_dec <= 0x10ffff else ''
        except Exception:
            char_dec = ''
        decrypted_chars.append(char_dec)
        decrypted_blocks.append({
            "index": b["index"],
            "c1": c1,
            "c2": c2,
            "s_bob": s_bob,
            "s_inv": s_inv_bob,
            "m_decrypted": m_dec,
            "char_decrypted": char_dec
        })

    decrypted_pesan = "".join(decrypted_chars)

    # ------------------ TAHAP 6: DIVA VERIFIKASI ------------------
    bob_calculated_checksum = hitung_checksum(decrypted_pesan, p)
    bob_calculated_tag = (bob_calculated_checksum * K_session) % p

    tag_cocok = (transmitted_tag == bob_calculated_tag)
    pesan_identik = (pesan == decrypted_pesan)
    status_aman = tag_cocok and pesan_identik

    verification_result = {
        "received_tag": str(transmitted_tag),
        "bob_calculated_tag": str(bob_calculated_tag),
        "tag_match": tag_cocok,
        "content_match": pesan_identik,
        "integrity_status": "SECURE_AND_VERIFIED" if status_aman else "TAMPERING_DETECTED",
        "status_message": (
            "SUKSES: Pesan terdekripsi sempurna dan Tag otentikasi cocok 100%! Pesan asli dari Tiara."
            if status_aman else
            "PERINGATAN BAHAYA: Tag verifikasi tidak cocok atau pesan terkorupsi! Sabotase/tampering oleh Oscar terdeteksi."
        )
    }

    return {
        "stage3_encryption": {
            "original_message": pesan,
            "total_chars": len(pesan),
            "original_checksum": str(original_checksum),
            "alice_tag": str(alice_tag),
            "blocks": [
                {
                    "index": b["index"],
                    "char": b["char"],
                    "m": b["m"],
                    "k": str(b["k"]),
                    "c1": str(b["c1"]),
                    "s": str(b["s_alice"]),
                    "c2": str(b["c2"])
                }
                for b in encrypted_blocks
            ]
        },
        "stage4_network": eve_intercepted,
        "stage5_decryption": {
            "decrypted_message": decrypted_pesan,
            "blocks": [
                {
                    "index": b["index"],
                    "c1": str(b["c1"]),
                    "c2": str(b["c2"]),
                    "s_bob": str(b["s_bob"]),
                    "s_inv": str(b["s_inv"]),
                    "m_decrypted": b["m_decrypted"],
                    "char_decrypted": b["char_decrypted"]
                }
                for b in decrypted_blocks
            ]
        },
        "stage6_verification": verification_result
    }
