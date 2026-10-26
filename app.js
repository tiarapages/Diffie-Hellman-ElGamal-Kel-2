/**
 * JAVASCRIPT FRONTEND - MINIMALIS & BERSIH
 * Menghubungkan antarmuka putih minimalis ke Python backend
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements - Parameter Setup
  const inputSeed = document.getElementById("input-seed");
  const inputBit = document.getElementById("input-bit");
  const btnInitParams = document.getElementById("btn-init-params");

  // DOM Elements - Tahap 0, 1, 2
  const valP = document.getElementById("val-p");
  const valQ = document.getElementById("val-q");
  const valG = document.getElementById("val-g");
  const valDhAlice = document.getElementById("val-dh-alice");
  const valDhBob = document.getElementById("val-dh-bob");
  const valDhK = document.getElementById("val-dh-k");
  const valElgamalX = document.getElementById("val-elgamal-x");
  const valElgamalY = document.getElementById("val-elgamal-y");

  // DOM Elements - Input Pesan & List
  const inputPesan = document.getElementById("input-pesan");
  const btnSend = document.getElementById("btn-send");
  const messagesContainer = document.getElementById("messages-container");
  const quickLinks = document.querySelectorAll(".btn-link");

  // ======================================================================
  // 1. INISIALISASI PARAMETER AWAL (TAHAP 0, 1, 2)
  // ======================================================================

  btnInitParams.addEventListener("click", initParameters);

  async function initParameters() {
    const seed = inputSeed.value.trim() || "3";
    const bit = inputBit.value || "16";

    btnInitParams.disabled = true;
    btnInitParams.textContent = "Memproses...";

    try {
      const res = await fetch("/api/init", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: seed, bit_size: bit })
      });
      const json = await res.json();
      if (!json.success) throw new Error("Gagal menginisialisasi");

      const s0 = json.setup.stage0;
      const s1 = json.setup.stage1;
      const s2 = json.setup.stage2;

      // Tahap 0
      valP.textContent = `${s0.p} (${s0.bit}-bit)`;
      valQ.textContent = s0.q;
      valG.textContent = s0.g;

      // Tahap 1
      valDhAlice.textContent = `a: ${s1.a} | A: ${s1.A}`;
      valDhBob.textContent = `b: ${s1.b} | B: ${s1.B}`;
      valDhK.textContent = s1.K_alice;

      // Tahap 2
      valElgamalX.textContent = s2.x;
      valElgamalY.textContent = s2.y;

      // Bersihkan daftar pesan lama jika parameter diganti
      messagesContainer.innerHTML = "";
      inputPesan.value = "";
      inputPesan.focus();

    } catch (err) {
      alert("Terjadi kesalahan: " + err.message);
    } finally {
      btnInitParams.disabled = false;
      btnInitParams.textContent = "Terapkan Parameter";
    }
  }

  // Quick preset links
  quickLinks.forEach(link => {
    link.addEventListener("click", () => {
      inputPesan.value = link.getAttribute("data-msg");
      inputPesan.focus();
    });
  });

  // ======================================================================
  // 2. KIRIM PESAN & TAMPILKAN TAHAP 3, 4, 5, 6
  // ======================================================================

  btnSend.addEventListener("click", handleSendMessage);
  inputPesan.addEventListener("keydown", (e) => {
    if (e.key === "Enter") handleSendMessage();
  });

  async function handleSendMessage() {
    const pesan = inputPesan.value.trim();
    if (!pesan) {
      inputPesan.focus();
      return;
    }

    btnSend.disabled = true;
    btnSend.textContent = "Memproses...";

    try {
      const res = await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: pesan, tamper: false })
      });
      const json = await res.json();
      if (!json.success) throw new Error(json.error || "Gagal memproses");

      appendMessageCard(json.data);

      inputPesan.value = "";
      inputPesan.focus();

      // Scroll halus ke pesan baru
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });

    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      btnSend.disabled = false;
      btnSend.textContent = "Enkripsi & Kirim";
    }
  }

  function appendMessageCard(data) {
    const s3 = data.stage3;
    const s4 = data.stage4;
    const s5 = data.stage5;
    const s6 = data.stage6;

    // Baris tabel karakter untuk Tahap 3
    let s3Rows = "";
    s3.blocks.forEach(b => {
      s3Rows += `
        <tr>
          <td>'${escapeHtml(b.char)}'</td>
          <td>${b.m}</td>
          <td>${b.k}</td>
          <td>${b.c1}</td>
          <td>${b.s}</td>
          <td>${b.c2}</td>
        </tr>
      `;
    });

    // Baris tabel karakter untuk Tahap 5
    let s5Rows = "";
    s5.blocks.forEach((b, idx) => {
      s5Rows += `
        <tr>
          <td>#${idx + 1}</td>
          <td>${b.s}</td>
          <td>${b.s_inv}</td>
          <td>${b.m}</td>
          <td>'${escapeHtml(b.char)}'</td>
        </tr>
      `;
    });

    // List paket jaringan Tahap 4
    let s4Rows = "";
    s4.network_blocks.forEach(nb => {
      s4Rows += `
        <tr>
          <td>Blok #${nb.index}</td>
          <td>${nb.c1}</td>
          <td>${nb.c2}</td>
        </tr>
      `;
    });

    const card = document.createElement("div");
    card.className = "message-block";

    card.innerHTML = `
      <div class="msg-summary-header">
        <div>
          <strong>Pesan #${data.message_number}:</strong> "${escapeHtml(data.original_pesan)}"
        </div>
        <div style="font-size:12px; color:var(--text-muted);">
          Pengirim: Tiara &bull; Penerima: Diva
        </div>
      </div>

      <div class="msg-stages-content">

        <!-- TAHAP 3: TIARA ENKRIPSI -->
        <div class="stage-box">
          <div class="stage-box-title">Tahap 3 - Tiara Mengenkripsi Pesan (ElGamal)</div>
          <div class="stage-desc">
            Setiap karakter diubah menjadi kode angka (ASCII m) lalu dienkripsi dengan k acak: c1 = g^k mod p, c2 = m * y^k mod p.
          </div>
          <table class="table-simple">
            <thead>
              <tr>
                <th>Karakter</th>
                <th>ASCII (m)</th>
                <th>k Acak</th>
                <th>c1 = g^k mod p</th>
                <th>s = y^k mod p</th>
                <th>c2 = m * s mod p</th>
              </tr>
            </thead>
            <tbody>
              ${s3Rows}
            </tbody>
          </table>
          <div class="info-row" style="margin-top:12px; padding-top:8px; border-top:1px dashed var(--border-color);">
            <span class="data-label">Tag Verifikasi Integritas Tiara:</span>
            <span class="tag-highlight">${s3.tag}</span>
          </div>
        </div>

        <!-- TAHAP 4: JARINGAN (OSCAR MENYADAP) -->
        <div class="stage-box">
          <div class="stage-box-title">Tahap 4 - Data yang Lewat di Jaringan (Disadap Oscar)</div>
          <div class="stage-desc">
            Oscar melihat ciphertext (c1, c2) dan tag berikut di jaringan publik:
          </div>
          <table class="table-simple">
            <thead>
              <tr>
                <th>Blok</th>
                <th>c1</th>
                <th>c2</th>
              </tr>
            </thead>
            <tbody>
              ${s4Rows}
            </tbody>
          </table>
          <div class="info-row" style="margin-top:10px;">
            <span class="data-label">Transmitted Tag:</span>
            <span class="mono">${s4.tag}</span>
          </div>
          <div class="card-note" style="margin-top:8px;">
            Oscar tidak memiliki kunci privat Diva (x) maupun k acak, sehingga tidak dapat menghitung c1^x untuk membuka pesan (Masalah Logaritma Diskrit).
          </div>
        </div>

        <!-- TAHAP 5: DIVA MENDEKRIPSI -->
        <div class="stage-box">
          <div class="stage-box-title">Tahap 5 - Diva Mendekripsi Pesan (ElGamal)</div>
          <div class="stage-desc">
            Diva menghitung shared secret s = c1^x mod p, invers modular s^-1, dan memulihkan karakter m = c2 * s^-1 mod p:
          </div>
          <table class="table-simple">
            <thead>
              <tr>
                <th>Blok</th>
                <th>s = c1^x mod p</th>
                <th>Invers s^-1 mod p</th>
                <th>m Pulih</th>
                <th>Karakter</th>
              </tr>
            </thead>
            <tbody>
              ${s5Rows}
            </tbody>
          </table>
          <div class="info-row" style="margin-top:12px; padding-top:8px; border-top:1px dashed var(--border-color);">
            <span class="data-label">Hasil Dekripsi Diva:</span>
            <strong style="font-size:14px; color:var(--text-main);">"${escapeHtml(s5.decrypted_pesan)}"</strong>
          </div>
        </div>

        <!-- TAHAP 6: DIVA VERIFIKASI DENGAN KUNCI SESI DH -->
        <div class="stage-box">
          <div class="stage-box-title">Tahap 6 - Verifikasi Integritas dengan Kunci Sesi Diffie-Hellman</div>
          <div class="info-row">
            <span class="data-label">Tag dari Tiara:</span>
            <span class="mono">${s6.tag_alice}</span>
          </div>
          <div class="info-row">
            <span class="data-label">Tag Hitungan Diva:</span>
            <span class="mono">${s6.tag_bob}</span>
          </div>
          <div class="info-row" style="margin-top:4px;">
            <span class="data-label">Pesan Dekripsi = Pesan Asli:</span>
            <span class="mono font-bold">${s6.ok_pesan ? "YA" : "TIDAK"}</span>
          </div>
          <div class="info-row">
            <span class="data-label">Tag Otentikasi Cocok:</span>
            <span class="mono font-bold">${s6.ok_tag ? "YA" : "TIDAK"}</span>
          </div>
          <div class="status-badge-ok">
            Pesan Tiara sampai ke Diva dengan aman, utuh, dan terverifikasi.
          </div>
        </div>

      </div>
    `;

    messagesContainer.appendChild(card);
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Inisialisasi awal saat pertama kali buka
  initParameters();
});
