document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("message-form");
  const input = document.getElementById("input-pesan");
  const senderInput = document.getElementById("input-from");
  const recipientInput = document.getElementById("input-to");
  const sendButton = document.getElementById("btn-send");
  const resetSessionButton = document.getElementById("btn-reset-session");
  const messagesContainer = document.getElementById("messages-container");
  const status = document.getElementById("session-status");
  let sessionReady = false;
  let cryptoSetup = null;

  form.addEventListener("submit", handleSendMessage);
  resetSessionButton.addEventListener("click", startNewSession);

  async function startNewSession() {
    sessionReady = false;
    cryptoSetup = null;
    setComposerEnabled(false);
    resetSessionButton.disabled = true;
    status.textContent = "Menyiapkan sesi enkripsi...";
    status.classList.remove("status-error");
    messagesContainer.innerHTML = `
      <div id="empty-state" class="empty-state">
        <div class="empty-icon" aria-hidden="true">✉</div>
        <h3>Belum ada pesan terkirim</h3>
        <p>Tulis pesan di bawah. Enkripsi dan verifikasi berjalan otomatis.</p>
      </div>
    `;

    try {
      const result = await requestJson("/api/init", {
        method: "POST",
        body: JSON.stringify({ seed: "3", bit_size: "32" })
      });
      cryptoSetup = result.setup;
      sessionReady = true;
      status.textContent = "Sesi enkripsi siap";
      status.classList.remove("status-error");
      senderInput.focus();
    } catch (error) {
      status.textContent = "Tidak dapat memulai sesi enkripsi";
      showError(error);
    } finally {
      resetSessionButton.disabled = false;
      setComposerEnabled(sessionReady);
    }
  }

  async function handleSendMessage(event) {
    event.preventDefault();
    const message = input.value.trim();
    const sender = senderInput.value.trim();
    const recipient = recipientInput.value.trim();
    if (!sessionReady) return;
    if (!sender || !recipient || !message) {
      status.textContent = "Lengkapi nama pengirim, penerima, dan isi pesan.";
      form.reportValidity();
      return;
    }

    setComposerEnabled(false);
    sendButton.querySelector("span").textContent = "Mengirim...";

    try {
      const result = await requestJson("/api/send", {
        method: "POST",
        body: JSON.stringify({ message, tamper: false })
      });
      appendMessage(result.data, sender, recipient, cryptoSetup);
      input.value = "";
      status.textContent = "Pesan berhasil diproses dan dikirim ke simulasi.";
      status.classList.remove("status-error");
      input.focus();
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } catch (error) {
      showError(error);
    } finally {
      sendButton.querySelector("span").textContent = "Kirim pesan";
      setComposerEnabled(sessionReady);
    }
  }

  async function requestJson(url, options) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
    const result = await response.json();
    if (!response.ok || result.success === false) {
      throw new Error(result.error || "Terjadi kesalahan saat memproses permintaan.");
    }
    return result;
  }

  function appendMessage(data, sender, recipient, setup) {
    const emptyState = document.getElementById("empty-state");
    if (emptyState) emptyState.remove();

    const isSafe = data.stage6.is_safe;
    const stage0 = setup.stage0;
    const stage1 = setup.stage1;
    const stage2 = setup.stage2;
    const messageElement = document.createElement("article");
    messageElement.className = "message-row email-card";
    messageElement.innerHTML = `
      <div class="message-bubble">
        <div class="email-heading">
          <div class="email-addresses">
            <p><strong>Dari:</strong> ${escapeHtml(sender)}</p>
            <p><strong>Kepada:</strong> ${escapeHtml(recipient)}</p>
          </div>
          <span class="email-time">${new Date().toLocaleString("id-ID", {
            dateStyle: "short",
            timeStyle: "short"
          })}</span>
        </div>
        <div class="recipient-message">
          <div class="recipient-message-heading">
            <span>Dibuka oleh <strong>${escapeHtml(recipient)}</strong></span>
            <span class="view-badge ${isSafe ? "is-verified" : "is-warning"}">${isSafe ? "Terverifikasi" : "Perlu diperiksa"}</span>
          </div>
          <p class="message-text">${escapeHtml(data.stage5.decrypted_pesan)}</p>
          <p class="delivery-status ${isSafe ? "is-verified" : "is-warning"}">
            ${isSafe ? "Pesan utuh · Tag cocok" : "Pesan berubah atau tag tidak cocok"}
          </p>
        </div>

        <div class="security-view oscar-view" aria-label="Data yang terlihat oleh Oscar">
          <div class="security-view-heading">
            <h3>Oscar menyadap jaringan</h3>
            <span class="view-badge">Ciphertext saja</span>
          </div>
          <p class="security-view-description">Oscar melihat pasangan ciphertext ElGamal (c1, c2), bukan isi pesan.</p>
          <div class="intercepted-packets">
            ${data.stage4.network_blocks.map(block => `
              <div class="intercepted-packet">
                <span>Blok ${escapeHtml(block.index)}</span>
                <code>(c1: ${escapeHtml(block.c1)}, c2: ${escapeHtml(block.c2)})</code>
              </div>
            `).join("")}
          </div>
          <p class="intercepted-tag">Tag integritas (bukan ciphertext): <code>${escapeHtml(data.stage4.tag)}</code></p>
          <button class="try-oscar-button" type="button">Coba baca sebagai Oscar</button>
          <p class="oscar-result" aria-live="polite">Oscar belum mencoba membaca paket ini.</p>
        </div>
        <details class="crypto-details">
          <summary>Lihat rincian tahapan Diffie–Hellman &amp; ElGamal</summary>
          <div class="crypto-details-content">
            <section class="crypto-stage">
              <h4>Tahap 0 — Parameter publik</h4>
              <p>Prima aman p = 2q + 1 dan generator g menjadi dasar pertukaran kunci dan enkripsi (${escapeHtml(stage0.bit)}-bit).</p>
              <div class="stage-values">
                <span>p = <code>${escapeHtml(stage0.p)}</code></span>
                <span>q = <code>${escapeHtml(stage0.q)}</code></span>
                <span>g = <code>${escapeHtml(stage0.g)}</code></span>
              </div>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 1 — Pertukaran kunci Diffie–Hellman</h4>
              <p>${escapeHtml(sender)} dan ${escapeHtml(recipient)} bertukar nilai publik lalu masing-masing menghitung kunci sesi yang sama.</p>
              <div class="stage-values">
                <span>${escapeHtml(sender)}: rahasia a = <code>${escapeHtml(stage1.a)}</code>, publik A = <code>${escapeHtml(stage1.A)}</code></span>
                <span>${escapeHtml(recipient)}: rahasia b = <code>${escapeHtml(stage1.b)}</code>, publik B = <code>${escapeHtml(stage1.B)}</code></span>
                <span>K ${escapeHtml(sender)} = B<sup>a</sup> mod p = <code>${escapeHtml(stage1.K_alice)}</code></span>
                <span>K ${escapeHtml(recipient)} = A<sup>b</sup> mod p = <code>${escapeHtml(stage1.K_bob)}</code></span>
                <strong class="${stage1.success ? "is-verified" : "is-warning"}">
                  ${stage1.success ? "Kunci sesi cocok" : "Kunci sesi tidak cocok"}
                </strong>
              </div>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 2 — Kunci ElGamal ${escapeHtml(recipient)}</h4>
              <p>${escapeHtml(recipient)} merahasiakan x dan membagikan y sebagai kunci publik untuk mengenkripsi pesan kepadanya.</p>
              <div class="stage-values">
                <span>Privat x = <code>${escapeHtml(stage2.x)}</code> (rahasia penerima dalam simulasi)</span>
                <span>Publik y = g<sup>x</sup> mod p = <code>${escapeHtml(stage2.y)}</code></span>
              </div>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 3 — Enkripsi pesan</h4>
              <p>Setiap karakter m dienkripsi memakai k acak: c1 = g<sup>k</sup> mod p dan c2 = m × y<sup>k</sup> mod p.</p>
              <div class="stage-table-wrap">
                <table class="stage-table">
                  <thead><tr><th>Karakter</th><th>m</th><th>k</th><th>c1</th><th>s = y<sup>k</sup></th><th>c2</th></tr></thead>
                  <tbody>
                    ${data.stage3.blocks.map(block => `
                      <tr>
                        <td>${escapeHtml(block.char)}</td>
                        <td>${escapeHtml(block.m)}</td>
                        <td>${escapeHtml(block.k)}</td>
                        <td>${escapeHtml(block.c1)}</td>
                        <td>${escapeHtml(block.s)}</td>
                        <td>${escapeHtml(block.c2)}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
              <p>Tag integritas dari ${escapeHtml(sender)}: <code>${escapeHtml(data.stage3.tag)}</code></p>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 4 — Data yang terlihat di jaringan</h4>
              <p>Oscar melihat ciphertext (c1, c2) dan tag integritas. Ia tidak memiliki kunci privat x milik ${escapeHtml(recipient)} atau k acak untuk menghitung rahasia s.</p>
              <div class="stage-table-wrap">
                <table class="stage-table">
                  <thead><tr><th>Blok</th><th>c1</th><th>c2</th></tr></thead>
                  <tbody>
                    ${data.stage4.network_blocks.map(block => `
                      <tr>
                        <td>${escapeHtml(block.index)}</td>
                        <td>${escapeHtml(block.c1)}</td>
                        <td>${escapeHtml(block.c2)}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
              <p>Tag yang dikirim: <code>${escapeHtml(data.stage4.tag)}</code></p>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 5 — Dekripsi oleh ${escapeHtml(recipient)}</h4>
              <p>${escapeHtml(recipient)} menghitung s = c1<sup>x</sup> mod p, lalu memulihkan m = c2 × s<sup>-1</sup> mod p.</p>
              <div class="stage-table-wrap">
                <table class="stage-table">
                  <thead><tr><th>Blok</th><th>s</th><th>s<sup>-1</sup></th><th>m pulih</th><th>Karakter</th></tr></thead>
                  <tbody>
                    ${data.stage5.blocks.map((block, index) => `
                      <tr>
                        <td>${index + 1}</td>
                        <td>${escapeHtml(block.s)}</td>
                        <td>${escapeHtml(block.s_inv)}</td>
                        <td>${escapeHtml(block.m)}</td>
                        <td>${escapeHtml(block.char)}</td>
                      </tr>
                    `).join("")}
                  </tbody>
                </table>
              </div>
              <p>Hasil dekripsi: <strong>${escapeHtml(data.stage5.decrypted_pesan)}</strong></p>
            </section>

            <section class="crypto-stage">
              <h4>Tahap 6 — Verifikasi integritas oleh ${escapeHtml(recipient)}</h4>
              <p>Tag = checksum(pesan) × K mod p. ${escapeHtml(recipient)} menghitung ulang tag dari pesan hasil dekripsi lalu membandingkannya dengan tag yang diterima.</p>
              <div class="stage-values">
                <span>Tag diterima = <code>${escapeHtml(data.stage6.tag_alice)}</code></span>
                <span>Tag hitungan ${escapeHtml(recipient)} = <code>${escapeHtml(data.stage6.tag_bob)}</code></span>
                <strong class="${isSafe ? "is-verified" : "is-warning"}">
                  ${isSafe ? "Pesan utuh dan tag cocok" : "Pesan berubah atau tag tidak cocok"}
                </strong>
              </div>
            </section>
          </div>
        </details>
      </div>
    `;
    messageElement.querySelector(".try-oscar-button").addEventListener("click", event => {
      const result = event.currentTarget.parentElement.querySelector(".oscar-result");
      result.textContent = `Oscar gagal membaca pesan: ia hanya memiliki ciphertext, bukan kunci privat x milik ${recipient}.`;
      event.currentTarget.disabled = true;
      event.currentTarget.textContent = "Oscar tidak dapat membaca pesan";
    });
    messagesContainer.appendChild(messageElement);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function setComposerEnabled(enabled) {
    input.disabled = !enabled;
    senderInput.disabled = !enabled;
    recipientInput.disabled = !enabled;
    sendButton.disabled = !enabled;
  }

  function showError(error) {
    status.textContent = error.message;
    status.classList.add("status-error");
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  startNewSession();
});
