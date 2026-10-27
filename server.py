"""
Server Web Localhost untuk Studi Kasus Chat Aman Tiara & Diva
Diffie-Hellman + ElGamal (100% Native Python - TANPA LIBRARY/FRAMEWORK LUAR)
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse
from crypto_core import (
    PRNG,
    buat_safe_prime,
    cari_generator,
    dh_generate_party,
    dh_compute_shared_secret,
    elgamal_keygen,
    elgamal_encrypt_char,
    elgamal_decrypt_char,
    hitung_checksum
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PORT = 8000


class CryptoSession:
    def __init__(self, seed=3, bit_size=32):
        self.message_counter = 0
        self.history = []
        self.init_parameters(seed, bit_size)

    def init_parameters(self, seed=3, bit_size=32):
        self.seed = int(seed) if str(seed).isdigit() else 3
        # Minimum 16 bit agar prima p > 256 dan memuat seluruh ASCII karakter (0-127/255)
        self.bit_size = int(bit_size) if str(bit_size).isdigit() and 16 <= int(bit_size) <= 64 else 16
        self.rng = PRNG(self.seed)
        self.message_counter = 0
        self.history = []

        # TAHAP 0: Parameter Publik p dan g
        self.p, self.q = buat_safe_prime(self.bit_size, self.rng)
        self.g = cari_generator(self.p, self.q)

        # TAHAP 1: Diffie-Hellman Key Exchange
        self.a, self.A = dh_generate_party(self.p, self.g, self.rng)
        self.b, self.B = dh_generate_party(self.p, self.g, self.rng)
        self.K_alice = dh_compute_shared_secret(self.B, self.a, self.p)
        self.K_bob = dh_compute_shared_secret(self.A, self.b, self.p)
        self.K = self.K_alice

        # TAHAP 2: ElGamal Diva Keygen
        self.x, self.y = elgamal_keygen(self.p, self.g, self.rng)

    def get_stages_0_1_2(self):
        return {
            "seed": self.seed,
            "bit_size": self.bit_size,
            "stage0": {
                "bit": self.p.bit_length(),
                "p": str(self.p),
                "q": str(self.q),
                "g": str(self.g)
            },
            "stage1": {
                "a": str(self.a),
                "A": str(self.A),
                "b": str(self.b),
                "B": str(self.B),
                "K_alice": str(self.K_alice),
                "K_bob": str(self.K_bob),
                "success": (self.K_alice == self.K_bob)
            },
            "stage2": {
                "x": str(self.x),
                "y": str(self.y)
            }
        }

    def process_message(self, pesan, tamper=False):
        self.message_counter += 1
        num = self.message_counter

        # TAHAP 3: Tiara Enkripsi
        cipher_blocks = []
        for ch in pesan:
            m = ord(ch)
            k, c1, s, c2 = elgamal_encrypt_char(m, self.p, self.g, self.y, self.rng)
            cipher_blocks.append({
                "char": ch,
                "m": m,
                "k": str(k),
                "c1": str(c1),
                "s": str(s),
                "c2": str(c2)
            })

        chk = hitung_checksum(pesan, self.p)
        tag_alice = (chk * self.K) % self.p

        # TAHAP 4: Oscar Sniffing / Jaringan (dengan opsi sabotase jika diminta)
        transmitted_blocks = []
        for b in cipher_blocks:
            transmitted_blocks.append({
                "c1": int(b["c1"]),
                "c2": int(b["c2"])
            })
        transmitted_tag = tag_alice
        tamper_info = None

        if tamper and len(transmitted_blocks) > 0:
            # Oscar memanipulasi blok pertama c2
            old_c2 = transmitted_blocks[0]["c2"]
            transmitted_blocks[0]["c2"] = (old_c2 + 1) % self.p
            tamper_info = f"Oscar menyabotase blok 1: nilai c2 diubah dari {old_c2} menjadi {transmitted_blocks[0]['c2']}"

        # TAHAP 5: Diva Dekripsi
        decrypted_blocks = []
        decrypted_chars = []
        for b in transmitted_blocks:
            c1_val = b["c1"]
            c2_val = b["c2"]
            s, s_inv, m_dec = elgamal_decrypt_char(c1_val, c2_val, self.x, self.p)
            try:
                ch_dec = chr(m_dec) if 0 <= m_dec <= 0x10ffff else '?'
            except Exception:
                ch_dec = '?'
            decrypted_chars.append(ch_dec)
            decrypted_blocks.append({
                "s": str(s),
                "s_inv": str(s_inv),
                "m": m_dec,
                "char": ch_dec
            })

        decrypted_pesan = "".join(decrypted_chars)

        # TAHAP 6: Verifikasi Diva
        chk_bob = hitung_checksum(decrypted_pesan, self.p)
        tag_bob = (chk_bob * self.K) % self.p

        ok_pesan = (decrypted_pesan == pesan)
        ok_tag = (tag_alice == tag_bob) if not tamper else (transmitted_tag == tag_bob)
        is_safe = ok_pesan and ok_tag

        result = {
            "message_number": num,
            "original_pesan": pesan,
            "stage3": {
                "blocks": cipher_blocks,
                "tag": str(tag_alice)
            },
            "stage4": {
                "network_blocks": [
                    {"index": i + 1, "c1": str(b["c1"]), "c2": str(b["c2"])}
                    for i, b in enumerate(transmitted_blocks)
                ],
                "tag": str(transmitted_tag),
                "tampered": tamper,
                "tamper_info": tamper_info
            },
            "stage5": {
                "blocks": decrypted_blocks,
                "decrypted_pesan": decrypted_pesan
            },
            "stage6": {
                "tag_alice": str(transmitted_tag),
                "tag_bob": str(tag_bob),
                "ok_pesan": ok_pesan,
                "ok_tag": ok_tag,
                "is_safe": is_safe
            }
        }

        self.history.append(result)
        return result


SESSION = CryptoSession(seed=3, bit_size=32)


class TerminalServerHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        # Format log terminal ringkas
        sys.stderr.write(f"[HTTP] {format % args}\n")

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filename, content_type):
        path = os.path.join(BASE_DIR, filename)
        if not os.path.exists(path):
            self.send_error(404, "File tidak ditemukan")
            return
        with open(path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self.send_file("index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self.send_file("style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self.send_file("app.js", "application/javascript; charset=utf-8")
        elif path == "/api/status":
            self.send_json({
                "setup": SESSION.get_stages_0_1_2(),
                "history": SESSION.history,
                "counter": SESSION.message_counter
            })
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b'{}'
        try:
            req_data = json.loads(post_data.decode('utf-8'))
        except Exception:
            req_data = {}

        if path == "/api/init":
            seed = req_data.get("seed", 3)
            bit_size = req_data.get("bit_size", 16)
            SESSION.init_parameters(seed, bit_size)
            self.send_json({
                "success": True,
                "setup": SESSION.get_stages_0_1_2()
            })

        elif path == "/api/send":
            pesan = req_data.get("message", "").strip()
            tamper = bool(req_data.get("tamper", False))
            if not pesan:
                self.send_json({"success": False, "error": "Pesan tidak boleh kosong!"}, status_code=400)
                return

            result = SESSION.process_message(pesan, tamper=tamper)
            self.send_json({
                "success": True,
                "data": result,
                "counter": SESSION.message_counter
            })

        else:
            self.send_error(404, "API tidak ditemukan")


def run(port=PORT):
    server_address = ('127.0.0.1', port)
    try:
        httpd = HTTPServer(server_address, TerminalServerHandler)
    except OSError:
        port = 8080
        server_address = ('127.0.0.1', port)
        httpd = HTTPServer(server_address, TerminalServerHandler)

    print("=" * 65)
    print("  STUDI KASUS: CHAT AMAN TIARA & DIVA (Diffie-Hellman + ElGamal)")
    print("  Server Localhost Aktif di: http://localhost:%d" % port)
    print("=" * 65)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer berhenti.")
        httpd.server_close()


if __name__ == "__main__":
    run()
