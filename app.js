// ===================================================================
// KETHRAVAX — Interactive Client-Side Engine & UX Controller
// Copyright (c) 2026 Arin Goel. All rights reserved.
// ===================================================================

// --- Theme Management ---
(function initTheme() {
  const savedTheme = localStorage.getItem('kethra_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('kethra_theme', next);
}

// --- Category Palette ---
const CAT_COLORS = {
  CODE: "#00F0FF",
  DATA_STRING: "#F59E0B",
  DATA_TABLE: "#10B981",
  DATA_RAW: "#38BDF8",
  PADDING: "#64748B",
  COMPRESSED_OPAQUE: "#8B5CF6",
  UNKNOWN_AMBIGUOUS: "#F43F5E"
};

// --- Preset Binary Samples ---
const PRESET_SAMPLES = {
  mixed: {
    name: "synthetic_mixed_payload.bin",
    type: "Mixed ISA & Structural Stream",
    generator: () => {
      const size = 16384;
      const buf = new Uint8Array(size);
      // 0..4096: x86_64 code
      for (let i = 0; i < 4096; i++) buf[i] = (i % 8 === 0) ? 0x55 : (i % 6 === 0) ? 0x48 : (i * 37) % 256;
      // 4096..4160: Padding
      for (let i = 4096; i < 4160; i++) buf[i] = 0x00;
      // 4160..7000: Strings
      const s = "KETHRAVAX_REVERSE_ENGINEERING_SUITE_SEC_INITIALIZE_KERNEL_TRAP_DEBUG_0x00_FATAL\x00";
      for (let i = 4160; i < 7000; i++) buf[i] = s.charCodeAt((i - 4160) % s.length);
      // 7000..10000: Jump table
      for (let i = 7000; i < 10000; i += 4) { buf[i] = i & 0xFF; buf[i+1] = 0x20; buf[i+2] = 0x40; buf[i+3] = 0x00; }
      // 10000..size: Compressed
      for (let i = 10000; i < size; i++) buf[i] = Math.floor(Math.random() * 256);
      return buf;
    }
  },
  x86: {
    name: "stripped_x86_64.elf",
    type: "Native x86-64 Linux Executable",
    generator: () => {
      const size = 16384;
      const buf = new Uint8Array(size);
      for (let i = 0; i < 12000; i++) buf[i] = (i % 7 === 0) ? 0x48 : (i % 5 === 0) ? 0x89 : (i * 19) % 256;
      for (let i = 12000; i < 12200; i++) buf[i] = 0xCC;
      for (let i = 12200; i < size; i++) buf[i] = "GLIBC_2.34_START_MAIN\x00".charCodeAt((i - 12200) % 22);
      return buf;
    }
  },
  firmware: {
    name: "iot_arm32_firmware.rom",
    type: "Bare-Metal ARM32/Thumb Microcontroller",
    generator: () => {
      const size = 16384;
      const buf = new Uint8Array(size);
      for (let i = 0; i < 8000; i++) buf[i] = (i % 4 === 3) ? 0xEB : (i * 13) % 256;
      for (let i = 8000; i < 8192; i++) buf[i] = 0xFF;
      for (let i = 8192; i < size; i++) buf[i] = "UBOOT_SPL_STAGE2_INIT\x00".charCodeAt((i - 8192) % 22);
      return buf;
    }
  },
  crypto: {
    name: "aes_gcm_ciphertext.bin",
    type: "High-Entropy Encrypted / Deflate Payload",
    generator: () => {
      const size = 16384;
      const buf = new Uint8Array(size);
      for (let i = 0; i < size; i++) buf[i] = Math.floor(Math.random() * 256);
      return buf;
    }
  }
};

// --- In-Page Playground Engine ---
let activeData = null;
let activeResults = null;

function calcEntropy(bytes) {
  if (!bytes || bytes.length === 0) return 0;
  const freq = new Uint32Array(256);
  for (let i = 0; i < bytes.length; i++) freq[bytes[i]]++;
  let ent = 0;
  const len = bytes.length;
  for (let i = 0; i < 256; i++) {
    if (freq[i] > 0) {
      const p = freq[i] / len;
      ent -= p * Math.log2(p);
    }
  }
  return ent;
}

function analyzeBytes(name, bytes) {
  activeData = bytes;
  const len = bytes.length;

  const nameEl = document.getElementById("pgStreamName");
  if (nameEl) nameEl.innerText = name.length > 22 ? name.slice(0, 20) + "..." : name;
  const sizeEl = document.getElementById("pgStreamSize");
  if (sizeEl) sizeEl.innerText = len.toLocaleString() + " B";

  const segments = [];
  const windowSize = 64;
  const step = 32;
  const frames = [];

  for (let off = 0; off < len; off += step) {
    const end = Math.min(off + windowSize, len);
    const chunk = bytes.subarray(off, end);
    const ent = calcEntropy(chunk);
    let nulls = 0, printable = 0;
    for (let i = 0; i < chunk.length; i++) {
      if (chunk[i] === 0) nulls++;
      else if (chunk[i] >= 0x20 && chunk[i] <= 0x7E) printable++;
    }
    const nullRatio = nulls / chunk.length;
    const printRatio = printable / chunk.length;

    let cat = "DATA_RAW", arch = "NONE", conf = 0.90;
    if (nullRatio >= 0.75 || (ent < 0.5 && nullRatio > 0.4)) {
      cat = "PADDING"; conf = 0.99;
    } else if (printRatio >= 0.70) {
      cat = "DATA_STRING"; conf = 0.96;
    } else if (ent >= 7.3) {
      cat = "COMPRESSED_OPAQUE"; conf = 0.98;
    } else if (nullRatio >= 0.20 && ent <= 4.2) {
      cat = "DATA_TABLE"; conf = 0.92;
    } else if (ent >= 4.8 && ent <= 6.8 && printRatio < 0.40) {
      cat = "CODE";
      arch = (off % 4 === 0 && chunk[3] === 0xEB) ? "ARM32" : "x86_64";
      conf = 0.95;
    }
    frames.push({ start: off, end, cat, arch, conf, ent, printRatio, nullRatio });
  }

  // Merge into contiguous segments
  let segStart = 0;
  let curCat = frames.length > 0 ? frames[0].cat : "DATA_RAW";
  let curArch = frames.length > 0 ? frames[0].arch : "NONE";

  for (let i = 1; i < frames.length; i++) {
    if (frames[i].cat !== curCat || frames[i].arch !== curArch) {
      const cut = frames[i].start;
      const chunk = bytes.subarray(segStart, cut);
      segments.push(createSegmentObj(segStart, cut, curCat, curArch, chunk));
      segStart = cut;
      curCat = frames[i].cat;
      curArch = frames[i].arch;
    }
  }
  if (segStart < len) {
    segments.push(createSegmentObj(segStart, len, curCat, curArch, bytes.subarray(segStart, len)));
  }

  activeResults = { name, bytes, segments };
  renderPlayground();
}

function createSegmentObj(start, end, cat, arch, chunk) {
  let nulls = 0, printable = 0;
  for (let i = 0; i < chunk.length; i++) {
    if (chunk[i] === 0) nulls++;
    else if (chunk[i] >= 0x20 && chunk[i] <= 0x7E) printable++;
  }
  return {
    start, end, length: end - start,
    category: cat, arch,
    confidence: cat === "PADDING" ? 0.99 : 0.94,
    entropy: calcEntropy(chunk),
    nullRatio: nulls / (chunk.length || 1),
    printRatio: printable / (chunk.length || 1)
  };
}

function renderPlayground() {
  if (!activeResults) return;
  const segs = activeResults.segments;
  const totalLen = activeResults.bytes.length;

  const countEl = document.getElementById("pgSegCount");
  if (countEl) countEl.innerText = segs.length;
  const entEl = document.getElementById("pgEntropy");
  if (entEl) {
    const avgEnt = segs.reduce((a, b) => a + b.entropy, 0) / (segs.length || 1);
    entEl.innerText = avgEnt.toFixed(2) + " b/B";
  }

  // Render Byte Ribbon
  const ribbon = document.getElementById("pgByteRibbon");
  if (ribbon) {
    ribbon.innerHTML = "";
    segs.forEach((seg, idx) => {
      const pct = Math.max((seg.length / totalLen) * 100, 0.5);
      const bar = document.createElement("div");
      bar.className = "byte-segment";
      bar.style.width = pct + "%";
      bar.style.backgroundColor = CAT_COLORS[seg.category] || "#64748B";
      bar.title = `0x${seg.start.toString(16).padStart(4,'0')}..0x${seg.end.toString(16).padStart(4,'0')} [${seg.category}] (${seg.length} B)`;
      bar.onclick = () => selectPlaygroundSeg(idx);
      ribbon.appendChild(bar);
    });
  }

  // Render Segment Table
  const list = document.getElementById("pgSegList");
  if (list) {
    list.innerHTML = "";
    segs.forEach((seg, idx) => {
      const row = document.createElement("div");
      row.className = "seg-row" + (idx === 0 ? " active" : "");
      const hexStart = "0x" + seg.start.toString(16).padStart(4, "0").toUpperCase();
      const hexEnd = "0x" + seg.end.toString(16).padStart(4, "0").toUpperCase();
      const col = CAT_COLORS[seg.category] || "#94A3B8";

      row.innerHTML = `
        <span style="color:var(--text); font-weight:600;">${hexStart}</span>
        <span style="color:var(--text-dim);">${hexEnd}</span>
        <span><span style="color:${col}; font-weight:700;">● ${seg.category}</span> ${seg.arch !== 'NONE' ? '<small style="color:var(--text-dim);">['+seg.arch+']</small>' : ''}</span>
        <span style="color:var(--accent); text-align:right;">${(seg.confidence * 100).toFixed(0)}%</span>
      `;
      row.onclick = () => selectPlaygroundSeg(idx);
      list.appendChild(row);
    });
  }

  selectPlaygroundSeg(0);
}

function selectPlaygroundSeg(idx) {
  if (!activeResults || idx < 0 || idx >= activeResults.segments.length) return;
  const seg = activeResults.segments[idx];

  const rows = document.querySelectorAll(".seg-row");
  rows.forEach((r, i) => r.classList.toggle("active", i === idx));

  // Diagnostic Detail
  const nameEl = document.getElementById("pgDiagName");
  if (nameEl) {
    nameEl.innerText = seg.category;
    nameEl.style.color = CAT_COLORS[seg.category];
  }
  const rangeEl = document.getElementById("pgDiagRange");
  if (rangeEl) rangeEl.innerText = `0x${seg.start.toString(16).padStart(4, "0").toUpperCase()} .. 0x${seg.end.toString(16).padStart(4, "0").toUpperCase()}`;
  const lenEl = document.getElementById("pgDiagLength");
  if (lenEl) lenEl.innerText = seg.length.toLocaleString() + " B";
  const archEl = document.getElementById("pgDiagArch");
  if (archEl) archEl.innerText = seg.arch;
  const confEl = document.getElementById("pgDiagConf");
  if (confEl) confEl.innerText = (seg.confidence * 100).toFixed(1) + "%";
  const entEl = document.getElementById("pgDiagEntropy");
  if (entEl) entEl.innerText = seg.entropy.toFixed(2) + " b/B";

  renderPlaygroundHex(seg.start, 512);
}

function renderPlaygroundHex(offset, maxBytes) {
  const hexEl = document.getElementById("pgHexDump");
  if (!hexEl || !activeData) return;
  const end = Math.min(activeData.length, offset + maxBytes);

  let html = "";
  for (let i = offset; i < end; i += 16) {
    const addr = "0x" + i.toString(16).padStart(8, "0").toUpperCase();
    let bytesHex = "";
    let ascii = "";
    for (let j = 0; j < 16; j++) {
      if (i + j < end) {
        const b = activeData[i + j];
        bytesHex += b.toString(16).padStart(2, "0").toUpperCase() + " ";
        ascii += (b >= 0x20 && b <= 0x7E) ? String.fromCharCode(b) : ".";
      } else {
        bytesHex += "   ";
      }
      if (j === 7) bytesHex += " ";
    }
    html += `<div class="hex-line"><span class="hex-addr">${addr}</span><span class="hex-bytes">${bytesHex}</span><span class="hex-ascii">${escapeHtml(ascii)}</span></div>`;
  }
  hexEl.innerHTML = html;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function loadPlaygroundPreset(key) {
  const sample = PRESET_SAMPLES[key];
  if (!sample) return;
  const bytes = sample.generator();
  analyzeBytes(sample.name, bytes);
}

// Global Export helper
function exportPlaygroundJSON() {
  if (!activeResults) {
    alert("Please run a playground analysis first.");
    return;
  }
  const blob = new Blob([JSON.stringify(activeResults.segments, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${activeResults.name}_kethravax_segments.json`;
  a.click();
}

// Auto-initialize on load if playground exists
document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("pgByteRibbon")) {
    loadPlaygroundPreset("mixed");
  }

  // Setup drag-and-drop if element exists
  const dropZone = document.getElementById("pgDropArea");
  if (dropZone) {
    ['dragenter', 'dragover'].forEach(n => dropZone.addEventListener(n, e => { e.preventDefault(); dropZone.classList.add('dragover'); }));
    ['dragleave', 'drop'].forEach(n => dropZone.addEventListener(n, e => { e.preventDefault(); dropZone.classList.remove('dragover'); }));
    dropZone.addEventListener('drop', e => {
      const f = e.dataTransfer.files;
      if (f.length > 0) {
        const r = new FileReader();
        r.onload = ev => analyzeBytes(f[0].name, new Uint8Array(ev.target.result));
        r.readAsArrayBuffer(f[0]);
      }
    });
  }
});
