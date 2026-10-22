/* wlachtype — Wallachian Cyrillic on-screen keyboard */
(() => {
  // ---- keys come from data/keys.csv (columns: row, char, capital, name, shortcut) ----
  const KEYS_URL = "data/keys.csv";
  let SUP = [], DIA = [], LET = [];
  const ALT_SUP = {}, DIGIT = {};
  // physical key -> Russian ЙЦУКЕН letter, for systems where Alt changes e.key (macOS Option)
  const RU = { KeyQ:"й",KeyW:"ц",KeyE:"у",KeyR:"к",KeyT:"е",KeyY:"н",KeyU:"г",KeyI:"ш",KeyO:"щ",KeyP:"з",
    BracketLeft:"х",BracketRight:"ъ",KeyA:"ф",KeyS:"ы",KeyD:"в",KeyF:"а",KeyG:"п",KeyH:"р",KeyJ:"о",KeyK:"л",
    KeyL:"д",Semicolon:"ж",Quote:"э",KeyZ:"я",KeyX:"ч",KeyC:"с",KeyV:"м",KeyB:"и",KeyN:"т",KeyM:"ь",
    Comma:"б",Period:"ю",Backquote:"ё" };

  // RFC 4180 CSV: quoted fields, "" escapes, BOM, CRLF and blank lines tolerated
  function parseCSV(text) {
    text = text.replace(/^﻿/, "");
    const rows = []; let row = [], f = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) { if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; } else f += c; }
      else if (c === '"') q = true;
      else if (c === ",") { row.push(f); f = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(f); f = ""; if (row.some(x => x.trim())) rows.push(row); row = [];
      } else f += c;
    }
    row.push(f); if (row.some(x => x.trim())) rows.push(row);
    return rows;
  }
  // a cell may hold the character itself or code points: "U+2DE0", or "U+0430 U+0301" for a sequence
  const toChar = s => {
    s = (s || "").trim();
    return /^(U\+[0-9A-F]{4,6}\s*)+$/i.test(s)
      ? s.split(/\s+/).map(u => String.fromCodePoint(parseInt(u.slice(2), 16))).join("")
      : s.normalize("NFC");
  };
  const isMark = c => /^\p{M}/u.test(c);
  function loadKeys(text) {
    const rows = parseCSV(text);
    const KINDS = ["sup", "dia", "let"], ORDER = ["row", "char", "capital", "name", "shortcut"];
    // header line: expected "row,char,capital,name,shortcut". If a name is missing or was
    // overwritten (e.g. "dia" instead of "row"), fall back to that column's usual position.
    const head = rows.shift().map(h => h.trim().toLowerCase());
    const col = (n, i) => { const k = head.indexOf(n); return k >= 0 ? k : i; };
    const [R, C, U, N, S] = ORDER.map((n, i) => col(n, i));
    const problems = [];
    rows.forEach((r, i) => {
      const kind = (r[R] || "").trim().toLowerCase(), c = toChar(r[C]);
      if (!c) return;
      if (!KINDS.includes(kind)) { problems.push("line " + (i + 2) + ": row \"" + kind + "\" is not sup, dia or let"); return; }
      const name = N < 0 ? "" : (r[N] || "").trim(), sc = S < 0 ? "" : (r[S] || "").trim();
      const k = { c, name, comb: isMark(c) };
      if (kind === "sup") { if (sc) { k.alt = sc.toLowerCase(); ALT_SUP[k.alt] = k; } SUP.push(k); }
      else if (kind === "dia") { if (/^[0-9]$/.test(sc)) { k.digit = sc; DIGIT[sc] = k; } DIA.push(k); }
      else if (kind === "let") { k.hi = toChar(U < 0 ? "" : r[U]) || c; LET.push(k); }
    });
    if (problems.length) console.warn("keys.csv: " + problems.join("; "));
    return problems;
  }

  const $ = id => document.getElementById(id);
  const ta = $("text"), statusEl = $("status"), toastEl = $("toast"), countEl = $("count");
  const cp = ch => "U+" + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, "0");

  // ---- persistence (per-browser draft only) ----
  const KEY = "wlachtype:draft";
  try { const s = localStorage.getItem(KEY); if (s) ta.value = s; } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, ta.value); } catch (e) {} };
  const updateCount = () => {
    const n = [...ta.value].length;
    countEl.textContent = n + (n === 1 ? " character" : " characters");
  };

  // ---- insertion ----
  function insert(str) {
    const s = ta.selectionStart ?? ta.value.length, e = ta.selectionEnd ?? s;
    ta.setRangeText(str, s, e, "end");
    ta.dispatchEvent(new Event("input"));
  }
  function backspace() {
    const s = ta.selectionStart, e = ta.selectionEnd;
    if (s !== e) ta.setRangeText("", s, e, "end");
    else if (s > 0) ta.setRangeText("", s - 1, s, "end");
    ta.dispatchEvent(new Event("input"));
  }

  // ---- shift state: off | once | lock ----
  let shift = "off", physShift = false, lastShiftTap = 0;
  const letterKeys = [];
  function upper() { return shift !== "off" || physShift; }
  function renderShift() {
    if (!shiftKey) return;
    shiftKey.dataset.state = shift;
    shiftKey.setAttribute("aria-pressed", shift !== "off");
    const up = upper();
    letterKeys.forEach(({ el, lo, hi }) => { el.textContent = up ? hi : lo; });
  }

  // ---- key factory ----
  function makeKey(label, title, onPress, cls) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "k" + (cls ? " " + cls : "");
    if (typeof label === "string") b.textContent = label; else b.append(label);
    b.addEventListener("pointerdown", e => { e.preventDefault(); b.classList.add("down"); });
    ["pointerup","pointerleave","pointercancel"].forEach(t => b.addEventListener(t, () => b.classList.remove("down")));
    b.addEventListener("click", () => { onPress(); });
    const show = () => { if (title) statusEl.innerHTML = title(); };
    const hide = () => { statusEl.textContent = ""; };
    b.addEventListener("pointerenter", show); b.addEventListener("focus", show);
    b.addEventListener("pointerleave", hide); b.addEventListener("blur", hide);
    return b;
  }
  const glyphLabel = (c, comb) => {
    const f = document.createDocumentFragment();
    if (comb) { const s = document.createElement("span"); s.className = "base"; s.textContent = "◌"; f.append(s); f.append(c); }
    else f.append(c);
    return f;
  };
  const describe = (c, name, shortcut, comb) => () => `<span class="cp">${cp(c)}</span><span>${comb ? "◌" + c : c}</span><span>${name.toUpperCase()}</span>${shortcut ? `<span class="sc">${shortcut}</span>` : ""}`;

  // ---- physical shortcuts: 1–8 type diacritics, Alt + letter types its superscript ----
  ta.addEventListener("keydown", e => {
    if (e.isComposing || e.ctrlKey || e.metaKey) return; // leaves Ctrl+C, AltGr (Ctrl+Alt) etc. alone
    const d = /^Digit([0-9])$/.exec(e.code);
    if (d && !e.shiftKey && DIGIT[d[1]]) {
      e.preventDefault();
      insert(e.altKey ? d[1] : DIGIT[d[1]].c); // Alt + digit still types the digit itself
      return;
    }
    if (e.altKey) {
      const k = (e.key || "").toLowerCase();
      const hit = ALT_SUP[k] || ALT_SUP[RU[e.code]];
      if (hit) { e.preventDefault(); insert(hit.c); }
    }
  });
  // stop a lone Alt press from opening the browser menu while typing
  ta.addEventListener("keyup", e => { if (e.key === "Alt") e.preventDefault(); });

  // ---- build the three rows from the loaded keys ----
  let shiftKey = null;
  function buildDeck() {
  SUP.forEach(({ c, name, comb, alt }) => $("row-sup").append(makeKey(glyphLabel(c, comb), describe(c, name, alt ? "Alt + " + alt : "", comb), () => insert(c))));
  DIA.forEach(({ c, name, comb, digit }) => {
    const k = makeKey(glyphLabel(c, comb), describe(c, name, digit ? "Key " + digit : "", comb), () => insert(c));
    if (digit) {
      const n = document.createElement("span"); n.className = "num"; n.textContent = digit; n.setAttribute("aria-hidden", "true");
      k.append(n);
    }
    k.setAttribute("aria-label", name + (digit ? ", key " + digit : ""));
    $("row-dia").append(k);
  });

  const shiftIcon = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M12 4 4 12h4.5v7h7v-7H20z"/></svg>';
  shiftKey = makeKey("", () => "Shift: tap once for one capital, double-tap to lock", () => {
    const now = Date.now();
    if (shift === "off") shift = (now - lastShiftTap < 350) ? "lock" : "once";
    else if (shift === "once" && now - lastShiftTap < 350) shift = "lock";
    else shift = "off";
    lastShiftTap = now; renderShift();
  }, "fn shift");
  shiftKey.innerHTML = shiftIcon; shiftKey.setAttribute("aria-label", "Shift");
  $("row-let").append(shiftKey);

  LET.forEach(({ c: lo, hi, name, comb }) => {
    const el = makeKey(lo, () => {
      const c = upper() ? hi : lo;
      return describe(c, "cyrillic " + (upper() ? "capital" : "small") + " letter " + name, "", comb)();
    }, () => {
      insert(upper() ? hi : lo);
      if (shift === "once") { shift = "off"; renderShift(); }
    });
    letterKeys.push({ el, lo, hi });
    $("row-let").append(el);
  });

  $("row-let").append(
    (() => { const b = makeKey("", () => "Delete the character before the cursor", backspace, "fn");
      b.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"><path d="M9 5h11v14H9l-6-7z"/><path d="m12 9 5 6m0-6-5 6"/></svg>';
      b.setAttribute("aria-label", "Backspace"); return b; })()
  );

  }

  // physical Shift previews capitals on the deck
  addEventListener("keydown", e => { if (e.key === "Shift" && !physShift) { physShift = true; renderShift(); } });
  addEventListener("keyup", e => { if (e.key === "Shift") { physShift = false; renderShift(); } });
  addEventListener("blur", () => { physShift = false; renderShift(); });

  // ---- click to copy ----
  let toastTimer;
  function toast(msg) {
    toastEl.textContent = msg; toastEl.classList.add("show");
    clearTimeout(toastTimer); toastTimer = setTimeout(() => toastEl.classList.remove("show"), 1400);
  }
  function fallbackCopy(text, partial) {
    const s = ta.selectionStart, e = ta.selectionEnd;
    if (!partial) ta.select();
    let ok = false; try { ok = document.execCommand("copy"); } catch (err) {}
    if (!partial) ta.setSelectionRange(s, e);
    toast(ok ? "Copied" : "Copy blocked here. Press Ctrl+C");
  }
  function copyAll() {
    const text = ta.value;
    if (!text) { toast("Nothing to copy"); return; }
    const n = [...text].length, label = "Copied · " + n + (n === 1 ? " character" : " characters");
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(() => toast(label), () => fallbackCopy(text, false));
    } else fallbackCopy(text, false);
  }
  ta.addEventListener("dblclick", () => {
    // double-click natively selects a word; drop that highlight so it is clear the whole text was copied
    const caret = ta.selectionEnd; ta.setSelectionRange(caret, caret);
    copyAll();
  });

  // shrink the text as more is typed so it always fits the field
  const AUTO_FS = () => Math.round(Math.min(72, Math.max(36, innerWidth / 14)));
  const MIN_FS = 18, SIZE_KEY = "wlachtype:size";
  let userSize = null; // null = automatic
  try { const v = parseInt(localStorage.getItem(SIZE_KEY), 10); if (v) userSize = v; } catch (e) {}
  const MAX_FS = () => userSize ?? AUTO_FS();
  function fit() {
    let fs = MAX_FS();
    ta.style.fontSize = fs + "px";
    while (fs > MIN_FS && ta.scrollHeight > ta.clientHeight + 1) {
      fs -= 2; ta.style.fontSize = fs + "px";
    }
  }
  addEventListener("resize", fit);
  document.fonts?.ready.then(fit);

  // block copying, cutting or dragging anything outside the text field
  ["copy","cut","dragstart"].forEach(t => document.addEventListener(t, e => { if (e.target !== ta) e.preventDefault(); }));

  ta.addEventListener("input", () => { save(); updateCount(); fit(); });
  // ---- options menu ----
  const menu = $("menu"), menuBtn = $("menu-btn"), sizeIn = $("size"), sizeOut = $("size-out"), clearBtn = $("clear-all");
  function disarm() { clearBtn.dataset.armed = "false"; clearBtn.textContent = "Clear all"; }
  function openMenu(open) {
    menu.hidden = !open; menuBtn.setAttribute("aria-expanded", open);
    if (!open) disarm();
  }
  menuBtn.addEventListener("click", () => openMenu(menu.hidden));
  document.addEventListener("pointerdown", e => { if (!menu.hidden && !e.target.closest(".menu-wrap")) openMenu(false); });
  addEventListener("keydown", e => { if (e.key === "Escape" && !menu.hidden) { openMenu(false); menuBtn.focus(); } });

  function renderSize() {
    sizeIn.value = MAX_FS();
    $("vsize").value = MAX_FS();
    sizeOut.textContent = userSize ? userSize + " px" : "Auto · " + AUTO_FS() + " px";
    $("size-auto").hidden = !userSize;
  }
  function setSize(v) {
    userSize = v == null ? null : Math.max(20, Math.min(120, v));
    try { userSize ? localStorage.setItem(SIZE_KEY, userSize) : localStorage.removeItem(SIZE_KEY); } catch (e) {}
    renderSize(); fit();
  }
  sizeIn.addEventListener("input", () => setSize(+sizeIn.value));
  $("vsize").addEventListener("input", e => setSize(+e.target.value));
  $("size-down").addEventListener("click", () => setSize(MAX_FS() - 4));
  $("size-up").addEventListener("click", () => setSize(MAX_FS() + 4));
  $("size-auto").addEventListener("click", () => setSize(null));
  addEventListener("resize", renderSize);

  $("copy-all").addEventListener("click", () => { copyAll(); openMenu(false); });

  clearBtn.addEventListener("click", () => {
    if (!ta.value) { toast("Nothing to clear"); return; }
    if (clearBtn.dataset.armed !== "true") {
      clearBtn.dataset.armed = "true"; clearBtn.textContent = "Click again to delete all text"; return;
    }
    ta.value = ""; ta.dispatchEvent(new Event("input"));
    openMenu(false); toast("Text cleared"); ta.focus();
  });

  updateCount(); renderSize(); fit();
  ta.focus();

  fetch(KEYS_URL, { cache: "no-cache" })
    .then(r => { if (!r.ok) throw new Error("HTTP " + r.status + " for " + KEYS_URL); return r.text(); })
    .then(t => {
      const problems = loadKeys(t); buildDeck(); renderShift();
      if (problems.length) statusEl.textContent = "keys.csv: skipped " + problems.length + " line(s), e.g. " + problems[0];
    })
    .catch(err => {
      statusEl.textContent = location.protocol === "file:"
        ? "Keys could not be loaded: open this page through a web server (python3 -m http.server), not from disk."
        : "Keys could not be loaded: " + (err.message || err);
    });
})();