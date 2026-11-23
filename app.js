// ===================================================================
// KETHRAVAX — Interactive Client-Side Engine & UX Controller
// Copyright (c) 2026 Arin Goel. All rights reserved.
// ===================================================================

const KETHRAVAX_PRESETS = {
  cortex_m4: {
    name: "Cortex-M4 Bootloader & Firmware",
    filename: "cortex_m4_bootloader.bin",
    totalBytes: 4096,
    architecture: "ARMv7E-M (Thumb-2)",
    entropyOverall: 5.24,
    segments: [
      {
        start: 0,
        end: 1024,
        category: "CODE",
        catName: "ARM32 / Thumb-2 Code",
        arch: "ARMv7E-M",
        color: "var(--cat-code)",
        conf: 0.994,
        entropy: 5.84,
        disasm: "push {r4-r7, lr} | sub sp, #16 | ldr r0, [pc, #44]",
        hexSamples: "80 B5 00 AF 82 B0 02 4B 1B 68 00 2B 01 D0 00 20 | 00 20 80 BD 00 00 00 00 70 47 00 00 08 B5 02 4C 20 48"
      },
      {
        start: 1024,
        end: 1664,
        category: "STRING",
        catName: "Embedded ASCII String Pool",
        arch: "N/A",
        color: "var(--cat-string)",
        conf: 0.989,
        entropy: 3.42,
        disasm: ".asciz \"[BOOT] Firmware v2.04 Initializing Hardware...\"",
        hexSamples: "5B 42 4F 4F 54 5D 20 46 69 72 6D 77 61 72 65 20 | 76 32 2E 30 34 20 49 6E 69 74 69 61 6C 69 7A 69 6E 67 00"
      },
      {
        start: 1664,
        end: 2176,
        category: "TABLE",
        catName: "Structured Jump / Relocation Table",
        arch: "N/A",
        color: "var(--cat-table)",
        conf: 0.971,
        entropy: 4.15,
        disasm: ".word 0x08000104, 0x08000120, 0x08000158, 0x0800019C",
        hexSamples: "04 01 00 08 20 01 00 08 58 01 00 08 9C 01 00 08 | B0 01 00 08 E4 01 00 08 10 02 00 08 40 02 00 08 74 02 00"
      },
      {
        start: 2176,
        end: 3584,
        category: "CODE",
        catName: "Peripheral Driver Code",
        arch: "Thumb-2",
        color: "var(--cat-code)",
        conf: 0.991,
        entropy: 5.92,
        disasm: "mov.w r3, #0x40000000 | str r2, [r3, #0x14]",
        hexSamples: "4F F0 40 43 5A 61 40 F2 00 03 1A 68 02 F0 01 02 | 1A 60 70 47 00 BF 08 B5 00 21 02 48 00 F0 14 F8 08 BD 00"
      },
      {
        start: 3584,
        end: 4096,
        category: "PADDING",
        catName: "Alignment & Null Padding",
        arch: "N/A",
        color: "var(--cat-padding)",
        conf: 1.000,
        entropy: 0.00,
        disasm: ".fill 512, 1, 0x00  ; 0-byte residual alignment",
        hexSamples: "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 | 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
      }
    ]
  },
  dual_arch: {
    name: "Mixed x86_64 + AArch64 Dual-Arch Stub",
    filename: "polyglot_loader_x86_arm64.bin",
    totalBytes: 6144,
    architecture: "Mixed (x86_64 -> AArch64)",
    entropyOverall: 5.76,
    segments: [
      {
        start: 0,
        end: 2048,
        category: "CODE",
        catName: "x86_64 Host Entry Stub",
        arch: "x86_64",
        color: "var(--cat-code)",
        conf: 0.995,
        entropy: 6.08,
        disasm: "mov %rsp, %rbp | sub $0x40, %rsp | callq 0x400",
        hexSamples: "48 89 E5 48 83 EC 40 E8 2B 02 00 00 48 85 C0 74 | 1A 48 8B 05 3F 10 00 00 48 89 C7 E8 1A 02 00 00 48 89 EC"
      },
      {
        start: 2048,
        end: 2560,
        category: "STRING",
        catName: "ASCII Cross-Platform Signatures",
        arch: "N/A",
        color: "var(--cat-string)",
        conf: 0.986,
        entropy: 3.65,
        disasm: ".asciz \"KethraPolyglot: Switching context to AArch64\"",
        hexSamples: "4B 65 74 68 72 61 50 6F 6C 79 67 6C 6F 74 3A 20 | 53 77 69 74 63 68 69 6E 67 20 63 6F 6E 74 65 78 74 00 00"
      },
      {
        start: 2560,
        end: 5120,
        category: "CODE",
        catName: "AArch64 Payload Section",
        arch: "AArch64",
        color: "var(--cat-code)",
        conf: 0.992,
        entropy: 5.78,
        disasm: "stp x29, x30, [sp, #-32]! | mov x29, sp | bl #0x120",
        hexSamples: "FD 7B BE A9 FD 03 00 91 94 00 00 94 E0 03 1F 2A | F3 03 00 AA F4 03 01 AA 00 00 00 14 FD 7B C2 A8 C0 03 5F"
      },
      {
        start: 5120,
        end: 5632,
        category: "TABLE",
        catName: "64-bit Relocation Offsets",
        arch: "N/A",
        color: "var(--cat-table)",
        conf: 0.968,
        entropy: 4.22,
        disasm: ".quad 0x0000000000401000, 0x0000000000401080",
        hexSamples: "00 10 40 00 00 00 00 00 80 10 40 00 00 00 00 00 | 00 11 40 00 00 00 00 00 80 11 40 00 00 00 00 00 00 12 40"
      },
      {
        start: 5632,
        end: 6144,
        category: "PADDING",
        catName: "Alignment Fill",
        arch: "N/A",
        color: "var(--cat-padding)",
        conf: 1.000,
        entropy: 0.00,
        disasm: ".fill 512, 1, 0x90  ; NOP sled padding",
        hexSamples: "90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 | 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90 90"
      }
    ]
  },
  ransomware: {
    name: "Stripped IoT Ransomware Payload",
    filename: "mirai_variant_stripped.bin",
    totalBytes: 5632,
    architecture: "MIPS32 (Big-Endian)",
    entropyOverall: 7.12,
    segments: [
      {
        start: 0,
        end: 1536,
        category: "CODE",
        catName: "MIPS32 Unpacker Loop",
        arch: "MIPS32 (BE)",
        color: "var(--cat-code)",
        conf: 0.987,
        entropy: 5.89,
        disasm: "lui $gp, 0x42 | addiu $sp, $sp, -32 | sw $ra, 28($sp)",
        hexSamples: "3C 1C 00 42 27 BD FF E0 AF BF 00 1C AF B0 00 18 | 8F 99 80 24 00 00 00 00 03 20 F8 09 00 00 00 00 8F BF 00"
      },
      {
        start: 1536,
        end: 1792,
        category: "TABLE",
        catName: "AES-256 S-Box Substitution Table",
        arch: "N/A",
        color: "var(--cat-table)",
        conf: 0.998,
        entropy: 7.95,
        disasm: ".byte 0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5",
        hexSamples: "63 7C 77 7B F2 6B 6F C5 30 01 67 2B FE D7 AB 76 | CA 82 C9 7D FA 59 47 F0 AD D4 A2 AF 9C A4 72 C0 B7 FD 93"
      },
      {
        start: 1792,
        end: 4608,
        category: "OPAQUE",
        catName: "High-Entropy Encrypted Shellcode",
        arch: "Encrypted Payload",
        color: "var(--cat-opaque)",
        conf: 0.996,
        entropy: 7.98,
        disasm: "[OPAQUE HIGH-ENTROPY CIPHERTEXT STREAM: p_value=0.998]",
        hexSamples: "D8 4A 91 BC E3 2F 11 08 77 C2 44 FA 88 19 32 EF | A1 B9 7C 33 04 DE 55 61 FF 20 8E 7A B3 C8 90 12 43 ED A8"
      },
      {
        start: 4608,
        end: 5120,
        category: "STRING",
        catName: "XOR-Obfuscated C2 IP & Commands",
        arch: "N/A",
        color: "var(--cat-string)",
        conf: 0.914,
        entropy: 4.82,
        disasm: ".byte 0x5a, 0x4f, 0x12, 0x3d  ; XOR key 0x7F",
        hexSamples: "25 3A 3A 22 7A 30 38 23 2B 36 30 2B 36 7F 7F 7F | 18 1B 1E 0F 12 1A 19 40 18 1B 1D 1F 7F 7F 7F 7F 00 00 00"
      },
      {
        start: 5120,
        end: 5632,
        category: "PADDING",
        catName: "Trailing Null Bounds",
        arch: "N/A",
        color: "var(--cat-padding)",
        conf: 1.000,
        entropy: 0.00,
        disasm: ".fill 512, 1, 0x00",
        hexSamples: "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 | 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"
      }
    ]
  },
  rtos_image: {
    name: "RTOS Kernel & Peripheral Image",
    filename: "zephyr_rtos_stm32.bin",
    totalBytes: 5632,
    architecture: "ARM Cortex-M3 (Thumb-2)",
    entropyOverall: 5.18,
    segments: [
      {
        start: 0,
        end: 512,
        category: "TABLE",
        catName: "ISR Exception Vector Table",
        arch: "ARM32",
        color: "var(--cat-table)",
        conf: 0.999,
        entropy: 4.10,
        disasm: ".word 0x20008000, 0x08000181, 0x08000195, 0x08000199",
        hexSamples: "00 80 00 20 81 01 00 08 95 01 00 08 99 01 00 08 | 9D 01 00 08 A1 01 00 08 A5 01 00 08 00 00 00 00 A9 01 00"
      },
      {
        start: 512,
        end: 4096,
        category: "CODE",
        catName: "Zephyr RTOS Scheduler & SysTick",
        arch: "Thumb-2",
        color: "var(--cat-code)",
        conf: 0.994,
        entropy: 5.91,
        disasm: "cpsid i | ldr r1, =_kernel | ldr r2, [r1, #0] | cpsie i",
        hexSamples: "72 B6 06 49 0A 68 62 B6 70 47 00 BF 00 20 04 49 | 08 60 70 47 00 20 02 49 08 60 70 47 20 00 08 08 00 00 00"
      },
      {
        start: 4096,
        end: 5120,
        category: "STRING",
        catName: "Kernel Panic & Printk Constants",
        arch: "N/A",
        color: "var(--cat-string)",
        conf: 0.978,
        entropy: 4.35,
        disasm: ".asciz \"***** USAGE FAULT: INVSTATE *****\\n\"",
        hexSamples: "2A 2A 2A 2A 2A 20 55 53 41 47 45 20 46 41 55 4C | 54 3A 20 49 4E 56 53 54 41 54 45 20 2A 2A 2A 2A 2A 0A 00"
      },
      {
        start: 5120,
        end: 5632,
        category: "PADDING",
        catName: "Flash Sector Boundary Alignment",
        arch: "N/A",
        color: "var(--cat-padding)",
        conf: 1.000,
        entropy: 0.00,
        disasm: ".fill 512, 1, 0xFF  ; Unprogrammed flash bytes",
        hexSamples: "FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF | FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF"
      }
    ]
  }
};

let currentPresetKey = "cortex_m4";
let activeSegmentIndex = 0;

// Theme Controller
function initTheme() {
  const saved = localStorage.getItem("kethravax-theme") || "dark";
  document.documentElement.setAttribute("data-theme", saved);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.innerHTML = saved === "dark" ? "🌓" : "🌞";
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "dark";
  const next = current === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("kethravax-theme", next);
  const btn = document.getElementById("theme-toggle");
  if (btn) btn.innerHTML = next === "dark" ? "🌓" : "🌞";
}

// Preset Selection
function selectPreset(key) {
  if (!KETHRAVAX_PRESETS[key]) return;
  currentPresetKey = key;
  activeSegmentIndex = 0;

  // Update preset buttons active state
  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-preset") === key);
  });

  const preset = KETHRAVAX_PRESETS[key];

  // Update Telemetry Header in Playground
  const metaEl = document.getElementById("pgMetaInfo");
  if (metaEl) {
    metaEl.innerHTML = `<strong>File:</strong> <code>${preset.filename}</code> &bull; <strong>Size:</strong> <code>${preset.totalBytes.toLocaleString()} B</code> &bull; <strong>ISA:</strong> <code>${preset.architecture}</code>`;
  }

  renderSegmentBar();
  renderActiveSegment();
}

// Render Interactive Stream Bar
function renderSegmentBar() {
  const container = document.getElementById("pgStreamBar");
  if (!container) return;
  const preset = KETHRAVAX_PRESETS[currentPresetKey];

  container.innerHTML = "";
  preset.segments.forEach((seg, idx) => {
    const pct = ((seg.end - seg.start) / preset.totalBytes) * 100;
    const div = document.createElement("div");
    div.className = "stream-segment";
    div.style.width = `${pct}%`;
    div.style.backgroundColor = seg.color;
    div.title = `${seg.catName} [0x${seg.start.toString(16).padStart(4, '0')}..0x${seg.end.toString(16).padStart(4, '0')}] (${(seg.conf * 100).toFixed(1)}%)`;

    if (idx === activeSegmentIndex) {
      div.style.outline = "2px solid #ffffff";
      div.style.zIndex = "3";
    }

    div.onclick = () => {
      activeSegmentIndex = idx;
      renderSegmentBar();
      renderActiveSegment();
    };

    container.appendChild(div);
  });
}

// Render Active Segment Diagnostics and Hex
function renderActiveSegment() {
  const preset = KETHRAVAX_PRESETS[currentPresetKey];
  const seg = preset.segments[activeSegmentIndex];
  if (!seg) return;

  // Update Diagnostics HUD
  const elCategory = document.getElementById("pgDiagCategory");
  const elRange = document.getElementById("pgDiagRange");
  const elSpan = document.getElementById("pgDiagSpan");
  const elArch = document.getElementById("pgDiagArch");
  const elConf = document.getElementById("pgDiagConf");
  const elEntropy = document.getElementById("pgDiagEntropy");
  const elDisasm = document.getElementById("pgDiagDisasm");

  if (elCategory) {
    elCategory.textContent = seg.catName;
    elCategory.style.color = seg.color;
  }
  if (elRange) elRange.textContent = `0x${seg.start.toString(16).toUpperCase().padStart(4, '0')} .. 0x${seg.end.toString(16).toUpperCase().padStart(4, '0')}`;
  if (elSpan) elSpan.textContent = `${(seg.end - seg.start).toLocaleString()} Bytes`;
  if (elArch) elArch.textContent = seg.arch;
  if (elConf) elConf.textContent = `${(seg.conf * 100).toFixed(1)}%`;
  if (elEntropy) elEntropy.textContent = `${seg.entropy.toFixed(2)} bits/byte`;
  if (elDisasm) elDisasm.textContent = seg.disasm;

  // Render Hex Table
  const hexBody = document.getElementById("pgHexRows");
  if (hexBody) {
    hexBody.innerHTML = "";
    const startHex = seg.start;
    const lines = [
      { offset: startHex, hex: seg.hexSamples.split(" | ")[0] || seg.hexSamples, ascii: "KethraCore....." },
      { offset: startHex + 16, hex: seg.hexSamples.split(" | ")[1] || "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00", ascii: "................" },
      { offset: startHex + 32, hex: "48 83 EC 20 48 89 5C 24 10 48 89 74 24 18 48 89", ascii: "H.. H.\\$.H.t$.H." }
    ];

    lines.forEach(line => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="hex-offset">0x${line.offset.toString(16).toUpperCase().padStart(6, '0')}</td>
        <td class="hex-bytes" style="color:${seg.color}">${line.hex}</td>
        <td class="hex-disasm" style="color:var(--text-muted); font-size:0.78rem;">${line.ascii}</td>
      `;
      hexBody.appendChild(tr);
    });
  }
}

// Code Tabs Switcher
function switchTab(btn, tabId) {
  const parent = btn.closest(".tabs-container");
  if (!parent) return;

  parent.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
  parent.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

  btn.classList.add("active");
  const target = parent.querySelector(`#${tabId}`);
  if (target) target.classList.add("active");
}

// Copy to Clipboard
function copySnippet(elementId, btn) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const text = el.innerText || el.textContent;

  navigator.clipboard.writeText(text).then(() => {
    const originalText = btn.innerHTML;
    btn.innerHTML = "✔ Copied!";
    btn.style.color = "var(--emerald)";
    setTimeout(() => {
      btn.innerHTML = originalText;
      btn.style.color = "";
    }, 2000);
  });
}

// Export Segments to JSON
function exportPlaygroundJson() {
  const preset = KETHRAVAX_PRESETS[currentPresetKey];
  const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(preset, null, 2));
  const downloadAnchor = document.createElement("a");
  downloadAnchor.setAttribute("href", dataStr);
  downloadAnchor.setAttribute("download", `${preset.filename}_kethravax_segments.json`);
  document.body.appendChild(downloadAnchor);
  downloadAnchor.click();
  downloadAnchor.remove();
}

// Initialize on Load
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  selectPreset("cortex_m4");
});
