/* Trình đọc (R2a): sao chép trích dẫn, đi tới Điều, cuộn tới đoạn chọn. R2b gọi lại initReader sau khi chèn mảnh. */
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
    const body = root.querySelector(".rd-body");
    const mark = body && el.offsetHeight > body.clientHeight ? el.querySelector("mark") : null;
    (mark || el).scrollIntoView({ block: mark ? "center" : block });
  }
  function initReader(root) {
    const sel = root.querySelector(".rd-top").dataset.sel;
    const goto = root.querySelector("#goto");
    if (goto) {
      const cur = sel && root.querySelector("#u" + sel);
      if (cur) {
        // chọn trong mục lục Điều chứa đoạn đang mở: Điều gần nhất phía trên
        const opts = [...goto.options];
        for (const o of opts) { const h = root.querySelector("#" + o.value); if (h && (h === cur || h.compareDocumentPosition(cur) & Node.DOCUMENT_POSITION_FOLLOWING)) goto.value = o.value; }
      }
      goto.addEventListener("change", () => goTo(root, root.querySelector("#" + goto.value), "start"));
    }
    root.addEventListener("click", (e) => {
      const b = e.target.closest("[data-copy]");
      if (b) { copy(b.dataset.copy); return; }
      const a = e.target.closest('.toc a[href^="#u"]');
      if (a) { e.preventDefault(); goTo(root, root.querySelector(a.getAttribute("href")), "start"); }
    });
    if (sel) requestAnimationFrame(() => goTo(root, root.querySelector("#u" + sel), "center"));
  }
  window.initReader = initReader;
  const r = document.getElementById("reader");
  if (r && r.querySelector(".rd-top")) initReader(r);
})();
