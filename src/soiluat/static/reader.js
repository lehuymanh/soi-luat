/* Trình đọc (R2a, R3): sao chép trích dẫn, đi tới Điều, cuộn tới đoạn chọn, tab Văn bản | Bản gốc.
   R2b chèn mảnh _reader.html vào <aside class="reader"> rồi gọi lại initReader. */
(function () {
  "use strict";
  let toastT = 0;
  function toast(msg) {
    let t = document.getElementById("toast");
    if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; t.setAttribute("role", "status"); document.body.appendChild(t); }
    t.textContent = msg; t.hidden = false;
    clearTimeout(toastT); toastT = setTimeout(() => { t.hidden = true; }, 3400);
  }
  function copy(text) {
    const ok = () => toast("Đã sao chép: " + text);
    const fallback = () => {
      const ta = document.createElement("textarea");
      ta.value = text; ta.setAttribute("readonly", ""); ta.style.cssText = "position:fixed;left:-9999px;top:0";
      document.body.appendChild(ta); ta.select();
      let done = false;
      try { done = document.execCommand("copy"); } catch (e) { done = false; }
      document.body.removeChild(ta);
      if (done) ok(); else toast("Không sao chép được. Hãy chọn dòng trích dẫn trong trình đọc rồi bấm Ctrl+C.");
    };
    try { navigator.clipboard.writeText(text).then(ok, fallback); } catch (e) { fallback(); }
  }
  function goTo(root, el, block) {
    if (!el) return;
    // đơn vị cao hơn khung nhìn thì cuộn tới chữ được tô đầu tiên
    const body = el.closest(".rd-body");
    const mark = body && el.offsetHeight > body.clientHeight ? el.querySelector("mark") : null;
    (mark || el).scrollIntoView({ block: mark ? "center" : block });
  }
  function showTab(root, tab, focus) {
    root.querySelectorAll('[role="tab"]').forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", on); t.tabIndex = on ? 0 : -1;
      root.querySelector("#" + t.getAttribute("aria-controls")).hidden = !on;
    });
    if (focus) tab.focus();
    const orig = tab.id === "tab-orig" && root.querySelector(".orig");
    if (orig && !orig.dataset.shown) { orig.dataset.shown = "1"; goTo(root, root.querySelector("#p" + orig.dataset.start), "start"); }
  }
  function gone(root) {
    root.querySelectorAll(".orig .pg").forEach((f) => f.remove());
    const n = root.querySelector(".orig .none"); if (n) n.hidden = false;
  }
  async function retry(root) {
    const top = root.querySelector(".rd-top");
    let html = "";
    try { html = await (await fetch(top.dataset.url, { headers: { "HX-Request": "true" } })).text(); } catch (e) { html = ""; }
    if (!html.includes('class="pg"')) { toast("Vẫn chưa thấy tệp. Nếu đã chuyển chỗ, hãy nạp lại tệp từ chỗ mới."); return; }
    if (top.dataset.full) { location.reload(); return; }
    root.innerHTML = html; initReader(root);
    showTab(root, root.querySelector("#tab-orig"), true);
  }
  function bind(root) {
    root.addEventListener("click", (e) => {
      const b = e.target.closest("[data-copy]");
      if (b) { copy(b.dataset.copy); return; }
      const t = e.target.closest('[role="tab"]');
      if (t) { showTab(root, t, false); return; }
      const g = e.target.closest("[data-goto-tab]");
      if (g) { showTab(root, root.querySelector("#" + g.dataset.gotoTab), true); return; }
      if (e.target.closest("[data-retry]")) { retry(root); return; }
      const a = e.target.closest('.toc a[href^="#u"]');
      if (a) { e.preventDefault(); goTo(root, root.querySelector(a.getAttribute("href")), "start"); }
    });
    root.addEventListener("keydown", (e) => {
      const t = e.target.closest('[role="tab"]');
      if (!t) return;
      const tabs = [...root.querySelectorAll('[role="tab"]')], i = tabs.indexOf(t);
      const j = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: tabs.length - 1 }[e.key];
      if (j === undefined) return;
      e.preventDefault(); showTab(root, tabs[(j + tabs.length) % tabs.length], true);
    });
    // ảnh trang không tải được sau khi mở (tệp bị dời, trang hỏng): thay bằng khối báo lỗi
    root.addEventListener("error", (e) => { if (e.target.matches && e.target.matches(".pg img")) gone(root); }, true);
  }
  function initReader(root) {
    if (!root._bound) { bind(root); root._bound = true; }
    const sel = root.querySelector(".rd-top").dataset.sel;
    const goto = root.querySelector("#goto");
    const cur = sel && root.querySelector("#u" + sel);
    if (goto) {
      // mục lục chọn sẵn Điều chứa đoạn đang mở: Điều gần nhất phía trên
      if (cur) for (const o of goto.options) { const h = root.querySelector("#" + o.value); if (h && (h === cur || h.compareDocumentPosition(cur) & Node.DOCUMENT_POSITION_FOLLOWING)) goto.value = o.value; }
      goto.addEventListener("change", () => goTo(root, root.querySelector("#" + goto.value), "start"));
    }
    if (cur) requestAnimationFrame(() => goTo(root, cur, "center"));
  }
  window.initReader = initReader;
  // nút "Sao chép trích dẫn" của từng mục kết quả (nằm ngoài trình đọc, nên không qua bind)
  document.addEventListener("click", (e) => { const b = e.target.closest("#thread [data-copy]"); if (b) copy(b.dataset.copy); });
  const r = document.getElementById("reader");
  if (r && r.querySelector(".rd-top")) initReader(r);
})();
