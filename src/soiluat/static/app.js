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

  /* ---- toast và hộp thoại xác nhận dùng chung (như mẫu; không dùng hộp thoại có sẵn của trình duyệt) ---- */
  let toastT = 0;
  function toast(msg) {  // vùng role="status" luôn có trong trang (rỗng thì mờ hẳn): đổi chữ trong vùng có sẵn thì trình đọc màn hình mới đọc
    $("#toast").textContent = msg;
    clearTimeout(toastT); toastT = setTimeout(() => { $("#toast").textContent = ""; }, 3400);
  }
  /* Trả Promise<boolean>. Nền (#app) inert khi mở; Esc, "Huỷ" và bấm ra ngoài đóng và trả focus về nút đã mở; "đồng ý" thì nơi gọi đặt focus.
     Phím nghe ở document (pha bắt) chứ không ở scrim: bấm vào chữ của hộp thoại đưa focus ra BODY, khi đó Esc, Tab và Alt+N không tới scrim. */
  function dialog(title, text, okLabel) {
    const opener = document.activeElement, app = $("#app");
    const scrim = document.createElement("div"); scrim.className = "scrim";
    scrim.innerHTML = '<div class="dialog" role="dialog" aria-modal="true" aria-labelledby="dlg-t" aria-describedby="dlg-d"><h2 id="dlg-t"></h2><p id="dlg-d"></p>' +
      '<div class="row"><button type="button" class="btn" data-v="0">Huỷ</button><button type="button" class="btn danger" data-v="1"></button></div></div>';
    $("h2", scrim).textContent = title; $("p", scrim).textContent = text; $('[data-v="1"]', scrim).textContent = okLabel;
    return new Promise(done => {
      const keys = e => {
        e.stopPropagation();  // chặn cả Alt+N và Esc của trình đọc: không rời trang khi đang hỏi xoá
        if (e.key === "Escape") close(false);
        else if (e.key === "Tab") {  // vòng giữa hai nút; focus ở BODY thì vào nút đầu (Shift+Tab: nút cuối)
          e.preventDefault();
          const bs = scrim.querySelectorAll("button"), i = [...bs].indexOf(document.activeElement);
          bs[e.shiftKey ? (i < 1 ? bs.length - 1 : i - 1) : (i + 1) % bs.length].focus();
        }
      };
      const close = ok => { document.removeEventListener("keydown", keys, true); scrim.remove(); app.inert = false; if (!ok && document.contains(opener)) opener.focus(); done(ok); };
      scrim.addEventListener("click", e => { const b = e.target.closest("[data-v]"); if (b) close(b.dataset.v === "1"); else if (e.target === scrim) close(false); });
      document.addEventListener("keydown", keys, true);
      document.body.append(scrim); app.inert = true;
      $('[data-v="0"]', scrim).focus();  // nút an toàn lấy focus đầu tiên
    });
  }

  const setTitle = t => { $("#thread h1").textContent = t; document.title = t + " · Soi Luật"; };

  /* ---- hỏi đáp ---- */
  qbox.addEventListener("input", () => { qbox.style.height = "auto"; qbox.style.height = Math.min(qbox.scrollHeight, 140) + "px"; });
  qbox.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); composer.requestSubmit(); }
  });
  composer.addEventListener("submit", e => { e.preventDefault(); const q = qbox.value; qbox.value = ""; qbox.style.height = "auto"; ask(q); });
  document.addEventListener("click", e => {
    const c = e.target.closest("[data-ask]");
    if (c) ask(c.dataset.ask, c.dataset.filters && JSON.parse(c.dataset.filters));  // "Hỏi lại" mang theo bộ lọc của tin đó
  });

  /* Các lần hỏi xếp thành một chuỗi: cuộc mới chưa có id tới khi có câu trả lời đầu, hai lần Enter nhanh sẽ tạo hai cuộc. */
  let cid = thread.dataset.cid || "", queue = Promise.resolve();  // cuộc mở lại từ /c/{id} có sẵn id: câu mới ghi tiếp vào đó
  const turns = thread.querySelectorAll(".msg.user");
  if (turns.length > 1) turns[turns.length - 1].scrollIntoView({ block: "start" });  // cuộc nhiều câu mở ra ở câu cuối (như sau khi hỏi), không ở đầu trang
  function ask(q, filters) {
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
    const fd = new FormData(); fd.set("q", q);
    for (const n of ["loai", "co_quan", "hieu_luc"]) { const v = (filters ? filters[n] || "" : composer.elements[n].value).trim(); if (v) fd.set(n, v); }
    queue = queue.then(async () => {  // không bao giờ từ chối: lỗi hiện trong khung trả lời, chuỗi vẫn chạy tiếp
      if (cid) fd.set("conversation_id", cid);
      try {
        const r = await post("/ask", fd, {});
        if (!r.ok) throw new Error("HTTP " + r.status);
        b.innerHTML = await r.text();
        const id = r.headers.get("X-Conversation-Id");  // không có khi chưa lưu được (đang nạp file): giữ id cũ
        if (id) {
          cid = id; history.replaceState(null, "", "/c/" + id);
          refreshHist().then(() => { const a = hist.querySelector(`.hrow[data-id="${id}"] a`); if (a) setTitle(a.textContent); });  // cuộc mới hiện trong danh sách, cuộc cũ lên đầu; h1 và tên trang theo tên thanh bên (đã cắt)
          const sub = $(".sub"); if (sub) sub.textContent = sub.textContent.replace(/\d+ câu hỏi/, n => `${parseInt(n) + 1} câu hỏi`);  // chỉ cuộc mở lại có dòng này
        }
      } catch (err) {
        b.innerHTML = '<p class="err"></p>'; b.firstChild.textContent = "Không tìm được: " + err.message;
      }
      u.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  /* Cuộc mở lại: chỉ 3 tin cuối dựng sẵn (dựng một tin ~0,2 s); tin cũ hơn dựng khi bấm "Xem lại". */
  async function replay(btn) {
    const box = btn.closest(".msg.bot");
    btn.disabled = true; btn.textContent = "Đang dựng…";
    try {
      const r = await fetch(`/c/${cid}/m/${btn.dataset.mid}`);
      if (!r.ok) throw new Error("HTTP " + r.status);
      box.innerHTML = await r.text();
      box.tabIndex = -1; box.focus({ preventScroll: true });  // nút đã biến mất: giữ focus ở khung kết quả vừa hiện
    } catch (err) { btn.disabled = false; btn.textContent = "Không dựng được, bấm để thử lại"; }
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
      const shown = res.querySelector(".more[hidden]");
      shown.hidden = false;
      const next = res.querySelector(".more[hidden]");
      res.querySelector("[data-shown]").textContent = [...res.querySelectorAll("article.card")].filter(a => !a.closest("[hidden]")).length;
      if (next) more.textContent = `Xem thêm ${next.dataset.n} kết quả`;
      else { more.hidden = true; shown.querySelector("a.addr")?.focus(); }  // nút ẩn thì focus về BODY: đưa tới mục mới hiện
      return;
    }
    const later = e.target.closest("[data-mid]");
    if (later) { replay(later); return; }
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

  /* ---- thanh bên: lịch sử (H4). Mỗi dòng là liên kết /c/{id} thật (tải lại cả trang); ô tìm, menu ⋯, đổi tên tại chỗ và xoá do JS làm ---- */
  const hist = $("#hist"), hq = $("#hq");
  let hseq = 0, ht = 0;  // lần gọi cuối thắng: gõ nhanh thì mảnh về không theo thứ tự bấm
  /* Mỗi dòng là liên kết tải lại cả trang nên #hist luôn về đầu: đưa dòng đang chọn vào tầm nhìn sau khi dựng và sau mỗi lần vẽ lại. */
  const showOn = () => hist.querySelector(".hrow.on")?.scrollIntoView({ block: "nearest" });
  showOn();
  async function refreshHist() {
    if (hist.querySelector("input")) return;  // đang đổi tên: không vẽ đè ô nhập
    const my = ++hseq, q = hq.value.trim();
    try {
      const r = await fetch(`/history?q=${encodeURIComponent(q)}&cid=${cid || 0}`);
      if (!r.ok) return;
      const html = await r.text();
      if (my !== hseq || hist.querySelector("input")) return;
      hist.innerHTML = html; showOn();
      $("#hist-status").textContent = q ? `${hist.querySelectorAll(".hrow").length} cuộc trò chuyện khớp` : "";
    } catch (_) { /* app đang tắt */ }
  }
  hq.addEventListener("input", () => { clearTimeout(ht); ht = setTimeout(refreshHist, 250); });  // gõ liền: chỉ gọi sau khi ngừng 250 ms

  const menuOf = () => hist.querySelector(".menu");
  function closeMenu(refocus) {
    const m = menuOf(); if (!m) return;
    const b = m.previousElementSibling;  // nút ⋯ của dòng
    m.remove(); b.setAttribute("aria-expanded", "false");
    if (refocus) b.focus();
  }
  function openMenu(b) {
    const was = b.getAttribute("aria-expanded") === "true";
    closeMenu(false);
    if (was) return;  // bấm lại ⋯ thì đóng
    const m = document.createElement("div"); m.className = "menu"; m.setAttribute("role", "menu");
    m.innerHTML = '<button type="button" role="menuitem" data-act="rename">Đổi tên</button><button type="button" role="menuitem" class="del" data-act="delete">Xoá</button>';
    b.after(m); b.setAttribute("aria-expanded", "true");
    m.firstChild.focus(); m.scrollIntoView({ block: "nearest" });
  }
  hist.addEventListener("click", e => {
    const more = e.target.closest(".more");
    if (more) { openMenu(more); return; }
    const act = e.target.closest("[data-act]");
    if (!act) return;
    const row = act.closest(".hrow"); closeMenu(false);
    if (act.dataset.act === "rename") renameRow(row); else deleteRow(row);
  });
  hist.addEventListener("keydown", e => {  // menu: Esc đóng và trả focus về ⋯, mũi tên đổi mục
    const m = e.target.closest(".menu");
    if (!m) return;
    if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); closeMenu(true); }
    else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      const items = [...m.children], i = items.indexOf(e.target);
      items[(i + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length].focus();
    }
  });
  hist.addEventListener("focusout", () => setTimeout(() => {  // Tab ra khỏi menu hoặc bấm ra ngoài: đóng (hoãn một nhịp: gỡ nút đang giữ focus cũng gây focusout)
    const m = menuOf(), on = document.activeElement;
    if (m && !m.contains(on) && on !== m.previousElementSibling) closeMenu(false);
  }));

  function renameRow(row) {
    const a = $("a", row), old = a.textContent, id = row.dataset.id;
    const inp = document.createElement("input"); inp.maxLength = 80; inp.value = old; inp.setAttribute("aria-label", "Tên mới cho cuộc trò chuyện");
    a.replaceWith(inp); inp.focus(); inp.select();
    let done = false;
    const finish = async (save, refocus) => {  // Enter lưu, Esc huỷ, rời ô thì lưu (như mẫu)
      if (done) return; done = true;
      const t = inp.value.trim();
      inp.replaceWith(a);
      if (refocus) a.focus();
      if (!save || t === old) return;
      if (!t) { toast("Tên không được để trống. Giữ tên cũ."); return; }
      try {
        const fd = new FormData(); fd.set("title", t);
        const r = await post(`/c/${id}/rename`, fd, {});
        if (!r.ok) throw new Error("HTTP " + r.status);
        if (id === cid) setTitle((await r.json()).title);
        await refreshHist();
        if (refocus) hist.querySelector(`.hrow[data-id="${id}"] a`)?.focus();  // danh sách vừa vẽ lại: giữ focus ở dòng vừa đổi tên
        toast("Đã đổi tên.");
      } catch (err) { toast("Không đổi được tên (đang nạp file?). Thử lại sau ít phút."); }
    };
    inp.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.isComposing) { e.preventDefault(); finish(true, true); }  // Enter chốt dấu của bộ gõ Telex/VNI không lưu tên dở
      else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); finish(false, true); }
    });
    inp.addEventListener("blur", () => finish(true, false));
  }

  async function deleteRow(row) {
    const id = row.dataset.id, name = $("a", row).textContent, opener = $(".more", row);
    opener.focus();  // menu vừa đóng: hộp thoại trả focus về ⋯ khi huỷ
    const ok = await dialog(`Xoá “${name}”?`, "Cuộc trò chuyện và các kết quả đã lưu sẽ mất. Câu hỏi vẫn còn trong nhật ký truy vấn (dùng cho trang Truy vấn bỏ sót).", "Xoá cuộc trò chuyện");
    if (!ok) return;
    try {
      const r = await post(`/c/${id}/delete`, new FormData(), {});
      if (!r.ok && r.status !== 404) throw new Error("HTTP " + r.status);  // 404: tab khác đã xoá trước, coi như xong
    } catch (err) { toast("Không xoá được (đang nạp file?). Thử lại sau ít phút."); opener.focus(); return; }
    if (id === cid) {  // đang xem cuộc này: về màn cuộc mới, toast hiện ở trang sau
      try { sessionStorage.setItem("toast", `Đã xoá “${name}”.`); } catch (_) { /* không có sessionStorage: bỏ toast */ }
      location.href = "/"; return;
    }
    await refreshHist();
    $(".newchat").focus();
    toast(`Đã xoá “${name}”.`);
  }

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
    const mg = j.migrate;  // nâng cấp dữ liệu kho cũ: tiến độ nằm trong chip (không đẩy bố cục), lỗi mới có dòng riêng
    busy.hidden = !(n_busy || e.running || mg.running);
    busy.textContent = n_busy ? `Nạp ${j.done}/${j.total}` : (e.running ? `Nhúng ${Math.round(100 * e.done / Math.max(e.total, 1))}%` : (mg.running ? "Nâng cấp" : ""));  // chữ ngắn: "Nâng cấp 38%" làm nhãn "Nạp văn bản" xuống dòng
    busy.title = mg.running && !n_busy && !e.running ? `Nâng cấp dữ liệu ${mg.done}/${mg.total}` : "";
    const ml = $("#migrate-line"), bad = !mg.running && mg.error;
    ml.hidden = !bad;
    if (bad && ml.title !== mg.error) {  // chỉ ghi khi đổi: trình đọc màn hình không đọc lại mỗi giây
      ml.textContent = `Nâng cấp dữ liệu chưa xong${mg.failed ? ` (${mg.failed} văn bản)` : ""}; app thử lại khi mở lần sau.`;
      ml.title = mg.error;
    }
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
    $(".topbar").inert = on || (narrow.matches && side.classList.contains("open"));  // ngăn kéo phủ lên topbar
  }
  let rdSeq = 0;  // /doc về không theo thứ tự bấm (văn bản lớn chậm hơn): chỉ lần bấm cuối được vẽ
  async function openDoc(a) {
    const my = ++rdSeq;
    let html;
    try { const r = await fetch(a.href, { headers: { "HX-Request": "true" } }); if (!r.ok) throw r.status; html = await r.text(); }
    catch (e) { if (my === rdSeq) location.href = a.href; return; }  // lỗi thì mở trang đầy đủ
    if (my !== rdSeq) return;
    opener = a;
    reader.classList.remove("wide"); reader.innerHTML = html; reader.hidden = false;
    $("#app").classList.add("reading"); setModal();
    window.initReader(reader);
    reader.querySelector("#rd-title").focus({ preventScroll: true });
  }
  function closeDoc() {
    const a = document.activeElement, away = a !== document.body && !reader.contains(a);  // màn rộng: đang gõ ở ô hỏi thì để yên focus
    reader.hidden = true; reader.classList.remove("wide"); reader.innerHTML = "";
    $("#app").classList.remove("reading"); setModal();
    if (!away && opener && document.contains(opener)) opener.focus();
  }
  document.addEventListener("click", e => {
    const a = e.target.closest("a[data-doc]");
    if (a && e.button === 0 && !e.ctrlKey && !e.metaKey && !e.shiftKey) { e.preventDefault(); openDoc(a); return; }
    if (e.target.closest("#rd-close")) { closeDoc(); return; }
    const w = e.target.closest("#rd-wide");
    if (w) {
      const on = reader.classList.toggle("wide");
      w.setAttribute("aria-label", on ? "Thu nhỏ trình đọc" : "Mở rộng trình đọc");  // nút bật tắt: đổi nhãn hoặc aria-pressed, không cả hai
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
    if (e.altKey && (e.key === "n" || e.key === "N")) {
      e.preventDefault();
      if (document.querySelector("dialog[open], .scrim, .hrow input")) return;  // đang xem tiến độ nạp, hỏi xoá hay gõ tên mới: không bỏ ngang
      if (location.pathname === "/" && !location.search && !thread.querySelector(".msg")) { setSide(false); qbox.focus(); }  // đã ở màn mới: giữ nháp
      else location.href = "/";
    }
    else if (e.key === "Escape" && document.querySelector("dialog[open]")) return;  // hộp thoại gốc tự đóng
    else if (e.key === "Escape" && !reader.hidden) closeDoc();
    else if (e.key === "Escape" && side.classList.contains("open")) setSide(false, true);
  });

  try { const t = sessionStorage.getItem("toast"); if (t) { sessionStorage.removeItem("toast"); toast(t); } } catch (_) { /* không có sessionStorage */ }
  refresh(false);
})();
