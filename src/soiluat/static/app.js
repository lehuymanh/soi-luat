(() => {
  let CSRF = document.body.dataset.csrf;
  const SUFF = new Set(document.body.dataset.suffixes.split(","));
  const $ = (s, r = document) => r.querySelector(s);
  const thread = $("#thread"), composer = $("#composer"), qbox = $("#q");
  /* Token CSRF đổi mỗi lần app khởi động lại; phản hồi 403 mang cookie mới, nên đọc lại cookie và gửi lại đúng một lần. */
  const cookieToken = () => (document.cookie.match(/(?:^|;\s*)soiluat_csrf=([^;]*)/) || [])[1];
  async function post(url, body, extra = { redirect: "manual" }) {
    const send = () => fetch(url, { method: "POST", body, headers: { "X-CSRF-Token": CSRF }, ...extra });
    let r = await send();
    const t = r.status === 403 && cookieToken();
    if (t && t !== CSRF) { CSRF = t; r = await send(); }
    return r;
  }
  let last = null, ocrInfo = null, timer = null;

  /* ---- hỏi đáp ---- */
  qbox.addEventListener("input", () => { qbox.style.height = "auto"; qbox.style.height = Math.min(qbox.scrollHeight, 140) + "px"; });
  qbox.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); composer.requestSubmit(); }
  });
  composer.addEventListener("submit", e => { e.preventDefault(); const q = qbox.value; qbox.value = ""; qbox.style.height = "auto"; ask(q); });
  document.addEventListener("click", e => { const c = e.target.closest("[data-ask]"); if (c) ask(c.dataset.ask); });

  async function ask(q) {
    q = q.trim();
    if (!q) return;
    $("#hello")?.remove();
    if (!thread.querySelector("h1")) {  // trang luôn có một h1: câu hỏi đầu làm tiêu đề, như mẫu
      const t = document.createElement("header"); t.className = "title-row";
      const h = document.createElement("h1"); h.textContent = q; t.append(h); thread.prepend(t);
    }
    const u = document.createElement("div"); u.className = "msg user";
    const bub = document.createElement("div"); bub.className = "bubble"; bub.textContent = q; u.append(bub);
    const b = document.createElement("div"); b.className = "msg bot";
    b.innerHTML = '<div class="typing" role="status" aria-label="Đang tìm"><i></i><i></i><i></i></div>';
    thread.append(u, b);
    u.scrollIntoView({ behavior: "smooth", block: "start" });
    const p = new URLSearchParams({ q });
    for (const n of ["loai", "co_quan", "hieu_luc"]) { const v = composer.elements[n].value.trim(); if (v) p.set(n, v); }
    try {
      const r = await fetch("/?" + p, { headers: { "HX-Request": "true" } });
      if (!r.ok) throw new Error("HTTP " + r.status);
      b.innerHTML = await r.text();
    } catch (err) {
      b.innerHTML = '<p class="err"></p>'; b.firstChild.textContent = "Không tìm được: " + err.message;
    }
    u.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  const fbtn = $("#btn-filters"), fbox = $("#filters");
  const filtersOn = () => ["loai", "co_quan", "hieu_luc"].some(n => composer.elements[n].value.trim());
  const syncDot = () => { $("#filters-dot").hidden = !filtersOn(); };
  fbtn.addEventListener("click", () => { const open = fbox.hidden; fbox.hidden = !open; fbtn.setAttribute("aria-expanded", open); });
  fbox.addEventListener("input", syncDot);
  if (filtersOn()) { fbox.hidden = false; fbtn.setAttribute("aria-expanded", "true"); }
  syncDot();

  /* ---- kết quả: "Xem thêm 10", đếm ô "Chọn để xuất", chú giải loại đoạn, "Bỏ lọc" ---- */
  document.addEventListener("click", e => {
    const more = e.target.closest("[data-more]");
    if (more) {
      const res = more.closest(".res");
      res.querySelector(".more[hidden]").hidden = false;
      const next = res.querySelector(".more[hidden]");
      res.querySelector("[data-shown]").textContent = [...res.querySelectorAll("article.card")].filter(a => !a.closest("[hidden]")).length;
      if (next) more.textContent = `Xem thêm ${next.dataset.n} kết quả`; else more.hidden = true;
      return;
    }
    const lg = e.target.closest("[data-legend]");
    if (lg) { const dl = lg.closest(".risk").nextElementSibling; dl.hidden = !dl.hidden; lg.setAttribute("aria-expanded", String(!dl.hidden)); return; }
    const uf = e.target.closest("[data-unfilter]");
    if (uf) { for (const n of ["loai", "co_quan", "hieu_luc"]) composer.elements[n].value = ""; syncDot(); ask(uf.dataset.unfilter); }
  });
  document.addEventListener("change", e => {
    if (!e.target.matches('input[name="uid"]')) return;
    const res = e.target.closest(".res"), k = res.querySelectorAll('input[name="uid"]:checked').length, btn = res.querySelector("[data-export]");
    btn.disabled = !k; btn.textContent = k ? `Xuất Word (${k} đoạn)` : "Xuất Word";
  });

  /* ---- cửa sổ Nạp file / Cài đặt ---- */
  function openPanel(name) { const d = $("#dlg-" + name); if (!d.open) d.showModal(); refresh(name === "settings" || !ocrInfo); }
  document.addEventListener("click", e => {
    const o = e.target.closest("[data-open]"); if (o) { openPanel(o.dataset.open); return; }
    const c = e.target.closest("[data-close]"); if (c) c.closest("dialog").close();
  });
  for (const d of document.querySelectorAll("dialog.panel")) {
    d.addEventListener("click", e => { if (e.target === d) d.close(); });
    d.addEventListener("close", schedule);
  }
  if (location.hash === "#import") openPanel("import");

  /* ---- trạng thái (nạp file, nhúng, OCR, chế độ) ---- */
  async function refresh(withOcr = false) {
    try {
      const r = await fetch("/api/status" + (withOcr ? "?ocr=1" : ""));
      last = await r.json();
      if (last.ocr) ocrInfo = last.ocr;
      render();
    } catch (_) { /* app đang tắt */ }
    schedule();
  }
  function schedule() {
    clearTimeout(timer);
    const open = $("#dlg-import").open || $("#dlg-settings").open;
    const active = last && last.jobs.active;
    if (open || active) timer = setTimeout(() => refresh(false), active ? 1000 : 5000);
  }
  const noteFor = m => {
    if (m.mode === "advance" && !m.installed) return ["Chưa cài mô hình tìm theo nghĩa — đang tìm như Normal (xem README).", true];
    if (m.mode === "advance" && m.pending) return [`Còn ${m.pending} Điều chưa nhúng (vẫn tìm được); app tự nhúng nền khi rảnh.`, false];
    if (m.mode === "advance") return ["BM25 + vector + reranker. Mỗi câu ~9 giây; câu đầu sau khi mở app có thể chậm hơn (nạp mô hình).", false];
    return ["BM25 thuần: nhẹ, chạy mọi máy.", false];
  };
  function render() {
    const j = last.jobs, m = last.mode;
    $("#kho-count").textContent = $("#kho-line").textContent = last.docs + " văn bản";
    $("#empty-kho")?.toggleAttribute("hidden", last.docs > 0);
    const busy = $("#busy"), e = j.embed;
    const n_busy = j.total - j.done;
    busy.hidden = !j.active;
    busy.textContent = n_busy ? `Nạp ${j.done}/${j.total}` : (e.running ? `Nhúng ${Math.round(100 * e.done / Math.max(e.total, 1))}%` : "");
    $("#q-sum").textContent = j.total ? `Đã xử lý ${j.done}/${j.total} file` : "Chưa nạp file nào";
    $("#q-clear").hidden = !j.total;
    const ul = $("#q-list"); ul.replaceChildren();
    for (const it of [...j.items].reverse()) {
      const li = document.createElement("li"); li.className = "s-" + it.state;
      const nm = document.createElement("span"); nm.className = "nm"; nm.textContent = it.name; nm.title = it.path;
      const st = document.createElement("span"); st.className = "st";
      st.textContent = it.label + (it.pages ? ` ${it.pages[0]}/${it.pages[1]} trang` : "");
      li.append(nm, st);
      if (it.note) { const nt = document.createElement("span"); nt.className = "nt"; nt.textContent = it.note; li.append(nt); }
      ul.append(li);
    }
    const el = $("#embed-line");
    el.hidden = !e.running;
    el.textContent = e.running ? `Đang nhúng vector cho chế độ Advance: ${e.done}/${e.total} Điều (nền, không cần chờ).` : "";
    for (const b of document.querySelectorAll("#mode-form .seg button")) b.setAttribute("aria-pressed", b.value === m.mode);
    const [txt, warn] = noteFor(m); const mn = $("#mode-note");
    mn.textContent = txt; mn.className = warn ? "note warn" : "note";
    $("#mode-chip").textContent = m.mode === "advance" ? "Advance" : "Normal";
    if (ocrInfo) {
      const ok = ocrInfo.ok === true;
      $("#ocr-line").textContent = ok ? `Sẵn sàng (${(ocrInfo.langs || []).join(", ")}).` : (ocrInfo.message || "OCR chưa dùng được.");
      $("#ocr-line").className = ok ? "note ok" : "note warn";
      const cb = $("#opt-ocr");
      if (cb.dataset.init !== "1") { cb.checked = ok; cb.dataset.init = "1"; }
      cb.disabled = !ok;
      $("#ocr-note").textContent = ok ? "" : "(chưa dùng được — xem Cài đặt)";
    }
  }
  $("#ocr-recheck").addEventListener("click", async () => {
    $("#ocr-line").textContent = "Đang kiểm tra…";
    const r = await fetch("/api/status?ocr=lai"); last = await r.json(); ocrInfo = last.ocr; render();
  });
  $("#mode-form").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target); fd.set("mode", e.submitter.value);
    await post("/settings/mode", fd);
    refresh();
  });
  $("#btn-backup").addEventListener("click", async () => {
    const msg = $("#backup-msg"); msg.textContent = "Đang sao lưu…";
    try { const r = await post("/backup", undefined, {}); msg.textContent = "Đã lưu: " + (await r.json()).path; }
    catch (err) { msg.textContent = "Lỗi: " + err.message; }
  });
  $("#q-clear").addEventListener("click", async () => { await post("/import/clear", new FormData()); refresh(); });

  /* ---- nạp file: chọn, kéo thả, đường dẫn ---- */
  const say = t => { $("#import-msg").textContent = t; };
  const opts = fd => { if ($("#opt-ocr").checked) fd.append("ocr", "on"); if ($("#opt-doan").checked) fd.append("doan", "on"); return fd; };
  async function sendFiles(files) {
    const ext = f => (f.name.match(/\.[^.]+$/) || [""])[0].toLowerCase();
    const ok = files.filter(f => SUFF.has(ext(f))), skipped = files.length - ok.length;
    openPanel("import");
    if (!ok.length) { say(files.length ? `Không có file nào đúng định dạng hỗ trợ (bỏ qua ${skipped}).` : "Không có file nào."); return; }
    const BATCH = 8;
    for (let i = 0; i < ok.length; i += BATCH) {
      const fd = opts(new FormData());
      ok.slice(i, i + BATCH).forEach(f => fd.append("files", f, f.name));
      say(`Đang gửi ${Math.min(i + BATCH, ok.length)}/${ok.length} file…`);
      const r = await post("/import/files", fd, {});
      if (!r.ok) { say("Lỗi khi gửi file: HTTP " + r.status); return; }
      refresh();
    }
    say(skipped ? `Đã xếp hàng ${ok.length} file; bỏ qua ${skipped} file không hỗ trợ.` : `Đã xếp hàng ${ok.length} file.`);
  }
  const pick = (btn, inp) => { $(btn).addEventListener("click", () => inp.click()); inp.addEventListener("change", () => { sendFiles([...inp.files]); inp.value = ""; }); };
  pick("#pick-files", $("#in-files")); pick("#pick-dir", $("#in-dir"));
  $("#path-form").addEventListener("submit", async e => {
    e.preventDefault();
    const r = await post("/import/path", opts(new FormData(e.target)), {});
    const j = await r.json();
    say(j.ok ? `Đã xếp hàng ${j.queued} file${j.skipped ? `, bỏ qua ${j.skipped} file không hỗ trợ` : ""}.` : j.error);
    if (j.ok) { e.target.reset(); refresh(); }
  });
  const hasFiles = e => e.dataTransfer && [...e.dataTransfer.types].includes("Files");
  let depth = 0;
  window.addEventListener("dragenter", e => { if (hasFiles(e)) { depth++; document.body.classList.add("dragging"); openPanel("import"); } });
  window.addEventListener("dragleave", e => { if (hasFiles(e) && --depth <= 0) { depth = 0; document.body.classList.remove("dragging"); } });
  window.addEventListener("dragover", e => { if (hasFiles(e)) e.preventDefault(); });
  window.addEventListener("drop", async e => {
    if (!hasFiles(e)) return;
    e.preventDefault(); depth = 0; document.body.classList.remove("dragging");
    sendFiles(await filesFromDrop(e.dataTransfer));
  });
  async function filesFromDrop(dt) {
    const entries = [...dt.items].map(i => i.webkitGetAsEntry && i.webkitGetAsEntry()).filter(Boolean);
    if (!entries.length) return [...dt.files];
    const out = [];
    const walk = async en => {
      if (en.isFile) out.push(await new Promise(res => en.file(res)));
      else { const rd = en.createReader(); let part; do { part = await new Promise(res => rd.readEntries(res)); for (const c of part) await walk(c); } while (part.length); }
    };
    for (const en of entries) await walk(en);
    return out;
  }

  /* ---- trình đọc (R2b): cột thứ ba ở màn rộng; tấm phủ (≤ 1240px) và chế độ mở rộng là hộp thoại ---- */
  const reader = $("#reader"), rdScrim = $("#rd-scrim"), mid = matchMedia("(max-width: 1240px)");
  let opener = null;
  function setModal() {  // nền ra khỏi thứ tự Tab khi trình đọc phủ lên, hoặc khi ngăn kéo mở
    const open = !reader.hidden, wide = reader.classList.contains("wide"), on = open && (mid.matches || wide);
    rdScrim.classList.toggle("on", open && mid.matches && !wide);
    if (on) { reader.setAttribute("role", "dialog"); reader.setAttribute("aria-modal", "true"); }
    else { reader.removeAttribute("role"); reader.removeAttribute("aria-modal"); }
    $("#main").inert = on || (narrow.matches && side.classList.contains("open"));
    side.inert = on || (narrow.matches && !side.classList.contains("open"));
    $(".topbar").inert = on;
  }
  async function openDoc(a) {
    let html;
    try { const r = await fetch(a.href, { headers: { "HX-Request": "true" } }); if (!r.ok) throw r.status; html = await r.text(); }
    catch (e) { location.href = a.href; return; }  // lỗi thì mở trang đầy đủ
    opener = a;
    reader.classList.remove("wide"); reader.innerHTML = html; reader.hidden = false;
    $("#app").classList.add("reading"); setModal();
    window.initReader(reader);
    reader.querySelector("#rd-title").focus({ preventScroll: true });
  }
  function closeDoc() {
    reader.hidden = true; reader.classList.remove("wide"); reader.innerHTML = "";
    $("#app").classList.remove("reading"); setModal();
    if (opener && document.contains(opener)) opener.focus();
  }
  document.addEventListener("click", e => {
    const a = e.target.closest("a[data-doc]");
    if (a && e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey) { e.preventDefault(); openDoc(a); return; }
    if (e.target.closest("#rd-close")) { closeDoc(); return; }
    const w = e.target.closest("#rd-wide");
    if (w) {
      const on = reader.classList.toggle("wide");
      w.setAttribute("aria-pressed", String(on)); w.setAttribute("aria-label", on ? "Thu nhỏ trình đọc" : "Mở rộng trình đọc");
      setModal();
    }
  });
  rdScrim.addEventListener("click", closeDoc);
  mid.addEventListener("change", setModal);

  /* ---- khung: thanh bên thành ngăn kéo ở màn hẹp; Alt+N mở cuộc mới ---- */
  const side = $("#side"), sideScrim = $("#side-scrim"), openSide = $("#open-side");
  const narrow = matchMedia("(max-width: 900px)");
  function setSide(open, focusBack) {
    side.classList.toggle("open", open); sideScrim.classList.toggle("open", open);
    openSide.setAttribute("aria-expanded", String(open));
    setModal();  // ngăn kéo đóng: ra khỏi thứ tự Tab
    if (open) side.querySelector("a, button")?.focus(); else if (focusBack) openSide.focus();
  }
  openSide.addEventListener("click", () => setSide(true));
  sideScrim.addEventListener("click", () => setSide(false, true));
  narrow.addEventListener("change", () => setSide(false));
  setSide(false);
  document.addEventListener("keydown", e => {
    if (e.altKey && (e.key === "n" || e.key === "N")) { e.preventDefault(); location.href = "/"; }
    else if (e.key === "Escape" && document.querySelector("dialog[open]")) return;  // hộp thoại gốc tự đóng
    else if (e.key === "Escape" && !reader.hidden) closeDoc();
    else if (e.key === "Escape" && side.classList.contains("open")) setSide(false, true);
  });

  refresh(false);
})();
