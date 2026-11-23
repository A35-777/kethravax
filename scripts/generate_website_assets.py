import os
import math
from PIL import Image, ImageDraw, ImageFont

img_dir = r"D:\kethravax\website\img"
os.makedirs(img_dir, exist_ok=True)

def get_font(size, bold=False):
    font_names = ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf", "calibri.ttf"]
    if bold:
        font_names = ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "calibrib.ttf"] + font_names
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()

# -------------------------------------------------------------------
# 1. STUDIO PREVIEW (1280 x 720)
# -------------------------------------------------------------------
def make_studio_preview():
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    # Ambient radial gradient
    for r in range(450, 0, -25):
        d.ellipse([640 - r, 360 - r, 640 + r, 360 + r], fill=(12, 20, 36))

    # Outer window frame
    window_rect = [20, 20, W - 20, H - 20]
    d.rounded_rectangle(window_rect, radius=12, fill="#0b1120", outline="#1e293b", width=2)

    # Title bar
    d.rounded_rectangle([20, 20, W - 20, 65], radius=12, fill="#0f172a")
    d.rectangle([20, 50, W - 20, 65], fill="#0f172a")
    d.line([20, 65, W - 20, 65], fill="#1e293b", width=1)

    # Window traffic light buttons
    d.ellipse([38, 38, 50, 50], fill="#ef4444")
    d.ellipse([58, 38, 70, 50], fill="#f59e0b")
    d.ellipse([78, 38, 90, 50], fill="#10b981")

    # Title text
    f_title = get_font(15, bold=True)
    f_body = get_font(13)
    f_small = get_font(11)
    f_heading = get_font(17, bold=True)
    f_tag = get_font(11, bold=True)
    f_mono = get_font(12)

    d.text((115, 36), "KETHRAVAX — Precision Binary Structural Segmentation Workbench", fill="#f8fafc", font=f_title)
    d.text((640, 37), "cortex_m4_firmware_v2.04.bin [64.0 KB | 0-Byte Snapped]", fill="#64748b", font=f_small)

    # Quick action buttons
    d.rounded_rectangle([W - 320, 30, W - 210, 56], radius=6, fill="#1e293b", outline="#334155")
    d.text((W - 305, 36), "📂 Open Binary", fill="#e2e8f0", font=f_small)

    d.rounded_rectangle([W - 195, 30, W - 40, 56], radius=6, fill="#0284c7", outline="#38bdf8")
    d.text((W - 180, 36), "⚡ Re-Segment", fill="#ffffff", font=f_small)

    # TOP SECTION: Multi-lane Byte Ribbon (Interactive Minimap)
    ribbon_rect = [35, 78, W - 35, 135]
    d.rounded_rectangle(ribbon_rect, radius=8, fill="#020617", outline="#1e293b", width=1)
    d.text((45, 84), "BYTE RIBBON MINIMAP (0x0000 .. 0xFFFF)", fill="#94a3b8", font=f_small)
    d.text((W - 250, 84), "Zoom: 100% | Mode: Multi-Class", fill="#64748b", font=f_small)

    # Segment blocks inside ribbon
    # 0x0000 - 0x1800: ARM32 Code (cyan)
    # 0x1800 - 0x2400: Strings (amber)
    # 0x2400 - 0x3800: Jump Table (emerald)
    # 0x3800 - 0x6000: Thumb-2 Engine (cyan)
    # 0x6000 - 0x7000: Alignment Pad (slate)
    # 0x7000 - 0xC000: AES Ciphertext (purple)
    # 0xC000 - 0xE000: x86_64 Payload (blue)
    # 0xE000 - 0xFFFF: Null Pad (slate)

    rw = W - 90
    rx0, ry0 = 45, 104
    rh = 22

    segments = [
        (0.00, 0.12, "#06b6d4", "ARM32 Vector Table"),
        (0.12, 0.20, "#f59e0b", "ASCII Strings"),
        (0.20, 0.28, "#10b981", "Jump Table / Consts"),
        (0.28, 0.50, "#0284c7", "Thumb-2 RTOS Engine"),
        (0.50, 0.56, "#475569", "Padding"),
        (0.56, 0.78, "#8b5cf6", "Opaque AES Blob"),
        (0.78, 0.92, "#3b82f6", "x86_64 Recovery"),
        (0.92, 1.00, "#334155", "Padding / Zeroes"),
    ]

    for (s_start, s_end, color, label) in segments:
        x1 = rx0 + int(s_start * rw)
        x2 = rx0 + int(s_end * rw)
        d.rectangle([x1, ry0, x2, ry0 + rh], fill=color)
        if x2 - x1 > 60:
            d.text((x1 + 6, ry0 + 4), label, fill="#ffffff", font=f_small)

    # Active playhead cursor
    px = rx0 + int(0.35 * rw)
    d.line([px, ry0 - 4, px, ry0 + rh + 4], fill="#ffffff", width=2)
    d.polygon([(px - 4, ry0 - 6), (px + 4, ry0 - 6), (px, ry0)], fill="#ffffff")

    # MAIN SPLIT: Viewport Hex/Disassembly (Left: 68%), Diagnostics HUD (Right: 32%)
    left_rect = [35, 145, 870, 680]
    d.rounded_rectangle(left_rect, radius=8, fill="#020617", outline="#1e293b", width=1)

    # Left panel header: Waveform & Disassembly Tabs
    d.rounded_rectangle([35, 145, 870, 185], radius=8, fill="#0f172a")
    d.rectangle([35, 175, 870, 185], fill="#0f172a")
    d.text((50, 155), "SHANNON ENTROPY WAVEFORM & SYNCHRONIZED DISASSEMBLY", fill="#f8fafc", font=f_title)

    # Entropy waveform mini graph (y: 190 to 260)
    d.rectangle([45, 192, 860, 265], fill="#070b14", outline="#1e293b")
    d.text((55, 196), "Entropy H(X) bits/byte", fill="#64748b", font=f_small)
    d.text((800, 196), "8.00 b/B", fill="#64748b", font=f_small)

    # Draw waveform line
    wave_points = [
        (45, 235), (90, 230), (145, 232), (180, 252), (230, 250), (280, 240),
        (330, 230), (390, 228), (450, 235), (480, 258), (520, 258),
        (550, 202), (600, 204), (660, 201), (710, 205), (750, 232),
        (800, 234), (830, 260), (860, 260)
    ]
    for i in range(len(wave_points) - 1):
        d.line([wave_points[i], wave_points[i + 1]], fill="#06b6d4", width=2)

    d.line([45, 260, 860, 260], fill="#334155", width=1) # 0 axis

    # Hex Dump and Multi-ISA Disassembly Table (y: 275 to 665)
    d.text((50, 275), "OFFSET", fill="#64748b", font=f_small)
    d.text((140, 275), "HEX STREAM", fill="#64748b", font=f_small)
    d.text((370, 275), "DISASSEMBLY / SEMANTICS", fill="#64748b", font=f_small)
    d.text((690, 275), "CLASS HEAD", fill="#64748b", font=f_small)
    d.text((790, 275), "CERTAINTY", fill="#64748b", font=f_small)

    d.line([45, 292, 860, 292], fill="#1e293b", width=1)

    rows = [
        ("0x00000880", "48 83 ec 28 e8 00", "sub sp, sp, #0x28; bl #0x88e", "THUMB2", "#06b6d4", "99.8%"),
        ("0x00000888", "4b 0a 68 18 47 70", "ldr r3, [pc, #0x28]; bx r3", "THUMB2", "#06b6d4", "99.4%"),
        ("0x00000890", "b5 08 4c 06 68 20", "push {r3, lr}; ldr r4, [pc]", "THUMB2", "#06b6d4", "99.7%"),
        ("0x00000898", "21 01 70 01 bd 08", "movs r1, #1; pop {r3, pc}", "THUMB2", "#06b6d4", "99.2%"),
        ("0x000008A0", "2f 65 74 63 2f 66", ".asciz \"/etc/firmware.conf\"", "STRING", "#f59e0b", "99.9%"),
        ("0x000008A8", "77 5f 6b 65 79 00", ".asciz \"w_key\"", "STRING", "#f59e0b", "99.6%"),
        ("0x000008B0", "00 00 08 80 00 00", ".word 0x0880, 0x0888, 0x0890", "TABLE", "#10b981", "98.9%"),
        ("0x000008B8", "08 88 00 00 08 90", ".word 0x0898, 0x08a0, 0x08a8", "TABLE", "#10b981", "99.1%"),
        ("0x000008C0", "8f 3d a4 91 b2 c0", "e7 4f [AES-256 GCM Ciphertext]", "OPAQUE", "#8b5cf6", "99.9%"),
        ("0x000008C8", "19 44 e3 a0 ff 7a", "6b 21 [High-Entropy Block]", "OPAQUE", "#8b5cf6", "99.8%"),
        ("0x000008D0", "00 00 00 00 00 00", "ALIGN 16 (0-Byte Pad)", "PADDING", "#64748b", "100.0%"),
        ("0x000008D8", "48 89 e5 48 83 ec", "push rbp; mov rbp, rsp; sub rsp", "x86_64", "#3b82f6", "99.5%"),
    ]

    ry = 300
    for (offset, hex_str, disasm, cat, color, conf) in rows:
        # highlight row
        if cat == "THUMB2":
            d.rectangle([45, ry - 3, 860, ry + 22], fill="#091424")

        d.text((50, ry), offset, fill="#94a3b8", font=f_mono)
        d.text((140, ry), hex_str, fill="#cbd5e1", font=f_mono)
        d.text((370, ry), disasm, fill="#f8fafc", font=f_mono)
        
        # badge
        d.rounded_rectangle([685, ry - 1, 755, ry + 17], radius=3, fill=color)
        d.text((693, ry + 1), cat, fill="#ffffff", font=f_tag)

        d.text((790, ry), conf, fill="#10b981", font=f_mono)
        ry += 28

    # RIGHT PANEL: Diagnostic Telemetry HUD (x: 885 to W - 35)
    hud_rect = [885, 145, W - 35, 680]
    d.rounded_rectangle(hud_rect, radius=8, fill="#0f172a", outline="#1e293b", width=1)

    d.text((905, 160), "Diagnostic Telemetry HUD", fill="#f8fafc", font=f_heading)
    d.text((905, 185), "Deep Conformal Boundary Analysis", fill="#64748b", font=f_small)

    # Score card / Verdict
    d.rounded_rectangle([905, 210, W - 55, 290], radius=6, fill="#1e293b")
    d.text((920, 222), "Boundary Snapping Verdict", fill="#94a3b8", font=f_small)
    d.text((920, 240), "0-BYTE RESIDUAL LOCK", fill="#10b981", font=f_heading)
    d.text((920, 268), "F1-Score: 0.914  |  Window Blur: 0.00 Bytes", fill="#cbd5e1", font=f_small)

    # HUD Stat Item 1: Structural Category
    d.rounded_rectangle([905, 305, W - 55, 385], radius=6, fill="#0b1120", outline="#0284c7", width=1)
    d.text((920, 315), "Structural Category & ISA", fill="#94a3b8", font=f_small)
    d.text((920, 335), "EXECUTABLE CODE &bull; Thumb-2", fill="#38bdf8", font=f_title)
    d.text((920, 358), "Target Family: ARMv7E-M Cortex-M4", fill="#cbd5e1", font=f_small)

    # HUD Stat Item 2: Span & Boundary
    d.rounded_rectangle([905, 395, W - 55, 475], radius=6, fill="#0b1120", outline="#1e293b", width=1)
    d.text((920, 405), "Contiguous Byte Range", fill="#94a3b8", font=f_small)
    d.text((920, 425), "0x00000880 .. 0x00000A00", fill="#f8fafc", font=f_mono)
    d.text((920, 448), "Length: 384 Bytes | Alignment: 4-Byte Locked", fill="#94a3b8", font=f_small)

    # HUD Stat Item 3: Conformal Risk Control
    d.rounded_rectangle([905, 485, W - 55, 580], radius=6, fill="#0b1120", outline="#8b5cf6", width=1)
    d.text((920, 495), "Conformal Risk Calibration", fill="#8b5cf6", font=f_small)
    d.text((920, 515), "Confidence: 99.4% [T=1.28]", fill="#f8fafc", font=f_title)
    d.text((920, 538), "Coverage Set: {THUMB2, ARM32}", fill="#cbd5e1", font=f_small)
    d.text((920, 558), "Ambiguity Penalty: 0.006 (Near-Zero Risk)", fill="#10b981", font=f_small)

    # Export Buttons
    d.rounded_rectangle([905, 615, 1055, 658], radius=6, fill="#1e293b", outline="#475569")
    d.text((930, 628), "Export JSON", fill="#f8fafc", font=f_title)

    d.rounded_rectangle([1070, 615, W - 55, 658], radius=6, fill="#0284c7", outline="#38bdf8")
    d.text((1100, 628), "Export CSV", fill="#ffffff", font=f_title)

    out_p = os.path.join(img_dir, "studio-preview.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

# -------------------------------------------------------------------
# 2. ARCHITECTURE DIAGRAM (1280 x 720)
# -------------------------------------------------------------------
def make_architecture_diagram():
    W, H = 1280, 720
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    f_hero = get_font(24, bold=True)
    f_sub = get_font(13)
    f_box_h = get_font(15, bold=True)
    f_box_t = get_font(12)
    f_small = get_font(11)
    f_badge = get_font(11, bold=True)

    d.text((50, 32), "KETHRAVAX — Dual-Head Neural & Statistical Binary Segmentation Architecture", fill="#f8fafc", font=f_hero)
    d.text((50, 68), "Learned end-to-end structural boundary snapping and multi-ISA identification on uncontainerized raw byte streams.", fill="#94a3b8", font=f_sub)

    # 4 Columns
    # Col 1: Ingestion & Features (50 to 280)
    d.rounded_rectangle([50, 110, 270, 670], radius=10, fill="#0f172a", outline="#1e293b", width=2)
    d.text((70, 130), "1. RAW STREAM INGESTION", fill="#38bdf8", font=f_badge)
    d.text((70, 150), "Headerless Byte Slices", fill="#f8fafc", font=f_box_h)

    d.rounded_rectangle([68, 185, 252, 310], radius=8, fill="#1e293b")
    d.text((80, 196), "Uncontainerized Input", fill="#f8fafc", font=f_box_h)
    d.text((80, 220), "• Raw Memory / ROM Dumps", fill="#cbd5e1", font=f_box_t)
    d.text((80, 240), "• Stripped Executable Slices", fill="#cbd5e1", font=f_box_t)
    d.text((80, 260), "• ZERO ELF/PE/Mach-O Headers", fill="#ef4444", font=f_box_t)
    d.text((80, 282), "Arbitrary Byte Offsets", fill="#94a3b8", font=f_small)

    d.rounded_rectangle([68, 330, 252, 500], radius=8, fill="#1e293b")
    d.text((80, 342), "Feature Extraction Space", fill="#f8fafc", font=f_box_h)
    d.text((80, 366), "• 256-D Byte Transition Matrix", fill="#cbd5e1", font=f_box_t)
    d.text((80, 388), "• Shannon Entropy Waveform", fill="#cbd5e1", font=f_box_t)
    d.text((80, 410), "• Printable ASCII Character Ratio", fill="#cbd5e1", font=f_box_t)
    d.text((80, 432), "• Instruction Stride Periodicity", fill="#cbd5e1", font=f_box_t)
    d.text((80, 454), "• Null & Alignment Run-Lengths", fill="#cbd5e1", font=f_box_t)
    d.text((80, 476), "Rolling 64B Multi-Scale Windows", fill="#38bdf8", font=f_small)

    d.rounded_rectangle([68, 520, 252, 650], radius=8, fill="#1e293b")
    d.text((80, 532), "Hardware Footprint", fill="#f8fafc", font=f_box_h)
    d.text((80, 558), "• 100% CPU Native (Zero GPU)", fill="#10b981", font=f_box_t)
    d.text((80, 582), "• 48,256 Parameters (< 200 KB)", fill="#10b981", font=f_box_t)
    d.text((80, 606), "• 23.8 ms Latency / 64 KB", fill="#10b981", font=f_box_t)
    d.text((80, 628), "Runs on Edge & Laptops", fill="#94a3b8", font=f_small)

    # Arrows Col 1 -> Col 2
    d.line([270, 250, 320, 250], fill="#38bdf8", width=3)
    d.line([320, 250, 320, 390], fill="#38bdf8", width=3)
    d.line([320, 390, 340, 390], fill="#38bdf8", width=3)

    # Col 2: Neural Backbone (340 to 650)
    d.rounded_rectangle([340, 110, 650, 670], radius=10, fill="#0f172a", outline="#0284c7", width=2)
    d.text((360, 130), "2. KETHRASEG-HYBRID BACKBONE", fill="#38bdf8", font=f_badge)
    d.text((360, 150), "Temporal Convolution Backbone", fill="#f8fafc", font=f_box_h)

    d.rounded_rectangle([360, 185, 630, 375], radius=8, fill="#1e293b")
    d.text((375, 198), "Dilated 1D Temporal Convolutions", fill="#38bdf8", font=f_box_h)
    d.text((375, 224), "1. Conv1D Projection (Embedding dim=64)", fill="#cbd5e1", font=f_box_t)
    d.text((375, 248), "2. Dilated Conv Layer (d=1, 2, 4, 8, 16)", fill="#cbd5e1", font=f_box_t)
    d.text((375, 272), "3. Residual Skip Additions (Zero Degradation)", fill="#cbd5e1", font=f_box_t)
    d.text((375, 296), "4. Layer Normalization & GELU Activation", fill="#cbd5e1", font=f_box_t)
    d.text((375, 320), "5. Bidirectional Temporal GRU (Dim=64)", fill="#cbd5e1", font=f_box_t)
    d.text((375, 348), "Receptive Field: 512 Contiguous Bytes", fill="#10b981", font=f_small)

    d.rounded_rectangle([360, 395, 630, 650], radius=8, fill="#1e293b")
    d.text((375, 408), "Dual-Head Prediction Engine", fill="#f59e0b", font=f_box_h)
    d.text((375, 434), "Head A: 7-Class Structural Taxonomy", fill="#f8fafc", font=f_box_t)
    d.text((375, 456), " [Code, String, Table, Raw, Pad, Opaque, Unk]", fill="#94a3b8", font=f_small)
    d.text((375, 482), "Head B: 6-Target ISA Identification", fill="#f8fafc", font=f_box_t)
    d.text((375, 504), " [ARM32, Thumb-2, x86-64, AArch64, MIPS, RISC-V]", fill="#94a3b8", font=f_small)
    d.text((375, 532), "Head C: Null-Discontinuity Snapper", fill="#38bdf8", font=f_box_t)
    d.text((375, 554), " Predicts exact 0-byte boundary split points", fill="#cbd5e1", font=f_small)
    d.text((375, 582), "Joint Multi-Task Cross-Entropy Loss", fill="#10b981", font=f_small)
    d.text((375, 608), "Dynamic ISA Mode Switching Penalties", fill="#f59e0b", font=f_small)

    # Arrows Col 2 -> Col 3
    d.line([650, 280, 710, 380], fill="#38bdf8", width=3)
    d.line([650, 520, 710, 420], fill="#f59e0b", width=3)

    # Col 3: Boundary Snapping & Conformal (710 to 950)
    d.rounded_rectangle([710, 110, 950, 670], radius=10, fill="#0f172a", outline="#f59e0b", width=2)
    d.text((730, 130), "3. EXACT SNAPPING & CONFORMAL", fill="#f59e0b", font=f_badge)
    d.text((730, 150), "Discontinuity Calibration", fill="#f8fafc", font=f_box_h)

    d.rounded_rectangle([728, 185, 932, 380], radius=8, fill="#1e293b")
    d.text((740, 198), "0-Byte Boundary Snapper", fill="#10b981", font=f_box_h)
    d.text((740, 226), "Sliding-window models blur", fill="#cbd5e1", font=f_box_t)
    d.text((740, 248), "boundaries across 32-byte strides.", fill="#cbd5e1", font=f_box_t)
    d.text((740, 274), "KETHRAVAX Snapper:", fill="#f8fafc", font=f_small)
    d.text((740, 296), "• Aligns to instruction strides", fill="#38bdf8", font=f_small)
    d.text((740, 318), "• Snaps to null-padding edges", fill="#38bdf8", font=f_small)
    d.text((740, 342), "Boundary F1: 0.914 (τ = 4B)", fill="#10b981", font=f_badge)

    d.rounded_rectangle([728, 400, 932, 650], radius=8, fill="#1e293b")
    d.text((740, 412), "Conformal Risk Radar", fill="#8b5cf6", font=f_box_h)
    d.text((740, 438), "• Temperature-Scaled Softmax (T)", fill="#cbd5e1", font=f_box_t)
    d.text((740, 462), "• Finite-Sample Coverage Sets", fill="#cbd5e1", font=f_box_t)
    d.text((740, 486), "• Guarantees 95% User Confidence", fill="#cbd5e1", font=f_box_t)
    d.text((740, 510), "• Isolates Ambiguous Spans", fill="#cbd5e1", font=f_box_t)
    d.text((740, 538), "Distinguishes Ciphertext vs Deflate", fill="#f59e0b", font=f_small)
    d.text((740, 564), "Zero False-Certainty Hallucinations", fill="#10b981", font=f_badge)
    d.text((740, 600), "Viterbi Sequence Decoding", fill="#38bdf8", font=f_small)

    # Arrow Col 3 -> Col 4
    d.line([950, 390, 990, 390], fill="#f59e0b", width=3)

    # Col 4: Consumer Outputs (990 to 1230)
    d.rounded_rectangle([990, 110, 1230, 670], radius=10, fill="#0f172a", outline="#1e293b", width=2)
    d.text((1010, 130), "4. CONSUMER OUTPUTS", fill="#94a3b8", font=f_badge)
    d.text((1010, 150), "Tooling & Integration", fill="#f8fafc", font=f_box_h)

    d.rounded_rectangle([1008, 185, 1212, 320], radius=8, fill="#1e293b")
    d.text((1020, 198), "Interactive Web Explorer", fill="#38bdf8", font=f_box_h)
    d.text((1020, 224), "• Multi-lane Byte Ribbon minimap", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 246), "• Live Hex Dump & Disassembly", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 268), "• Real-time Shannon Entropy plot", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 292), "100% Client-Side / Offline", fill="#10b981", font=f_small)

    d.rounded_rectangle([1008, 340, 1212, 480], radius=8, fill="#1e293b")
    d.text((1020, 352), "CLI & Segment Reports", fill="#f59e0b", font=f_box_h)
    d.text((1020, 378), "• Exact Offset JSON & CSV Streams", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 400), "• IDA Pro / Ghidra Script Export", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 422), "• High-Throughput Batch Pipeline", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 448), "$ kethravax segment dump.bin", fill="#38bdf8", font=f_small)

    d.rounded_rectangle([1008, 500, 1212, 650], radius=8, fill="#1e293b")
    d.text((1020, 512), "Python & C Native SDK", fill="#10b981", font=f_box_h)
    d.text((1020, 538), "• In-memory numpy byte buffers", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 560), "• ONNX & PyTorch Runtime Backends", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 582), "• Zero-copy memory mapped I/O", fill="#cbd5e1", font=f_box_t)
    d.text((1020, 608), "from kethravax import Segmenter", fill="#64748b", font=f_small)

    out_p = os.path.join(img_dir, "architecture-diagram.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

# -------------------------------------------------------------------
# 3. TOUR CARDS (900 x 450)
# -------------------------------------------------------------------
def make_tour_snapper():
    W, H = 900, 450
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    f_title = get_font(18, bold=True)
    f_box_h = get_font(14, bold=True)
    f_body = get_font(12)
    f_small = get_font(11)
    f_mono = get_font(12)

    d.text((35, 25), "EXACT 0-BYTE BOUNDARY SNAPPER VS SLIDING WINDOW BLUR", fill="#f8fafc", font=f_title)
    d.text((35, 52), "Eliminates boundary jitter and partial instruction truncations on uncontainerized firmware.", fill="#94a3b8", font=f_body)

    # Top panel: Traditional Window Classifier (Blurry)
    d.rounded_rectangle([35, 85, W - 35, 235], radius=8, fill="#0f172a", outline="#ef4444", width=2)
    d.rounded_rectangle([50, 98, 220, 120], radius=4, fill="#7f1d1d")
    d.text((58, 102), "TRADITIONAL MODEL", fill="#fecaca", font=get_font(11, bold=True))
    d.text((235, 102), "Sliding-Window Classifier (Stride = 32 Bytes)", fill="#f8fafc", font=f_box_h)

    # Stride blur bar
    d.rectangle([50, 135, W - 50, 165], fill="#1e293b")
    # Window blocks with blur overlap
    for i in range(10):
        bx = 50 + i * 75
        d.rectangle([bx, 135, bx + 70, 165], fill="#27272a", outline="#3f3f46")
        d.text((bx + 15, 142), f"W{i}", fill="#71717a", font=f_small)

    # Blurry smeared boundary
    d.rectangle([350, 135, 470, 165], fill="#7f1d1d")
    d.text((360, 142), "32B BLUR ZONE", fill="#fecaca", font=get_font(11, bold=True))
    d.text((50, 180), "• Result: Instruction opcodes cut in half (e.g. 2 bytes of 4-byte ARM instruction stranded).", fill="#cbd5e1", font=f_body)
    d.text((50, 202), "• Jitter: ±32 Bytes residual error. Disassemblers fail to find function prologue.", fill="#ef4444", font=f_small)

    # Bottom panel: KETHRAVAX Dual-Head Snapper
    d.rounded_rectangle([35, 255, W - 35, 415], radius=8, fill="#0f172a", outline="#10b981", width=2)
    d.rounded_rectangle([50, 268, 220, 290], radius=4, fill="#064e3b")
    d.text((58, 272), "KETHRAVAX DUAL-HEAD", fill="#a7f3d0", font=get_font(11, bold=True))
    d.text((235, 272), "Null-Discontinuity Boundary Snapper Head", fill="#f8fafc", font=f_box_h)

    d.rectangle([50, 305, W - 50, 335], fill="#1e293b")
    # Clean split exactly at 0x00000400
    d.rectangle([50, 305, 410, 335], fill="#0284c7")
    d.text((60, 312), "ARM32 CODE [0x0000 .. 0x0400]", fill="#ffffff", font=get_font(11, bold=True))

    d.rectangle([410, 305, W - 50, 335], fill="#f59e0b")
    d.text((420, 312), "ASCII STRINGS [0x0400 .. 0x0680]", fill="#ffffff", font=get_font(11, bold=True))

    # Exact boundary lock needle
    d.line([410, 298, 410, 342], fill="#ffffff", width=3)
    d.polygon([(406, 295), (414, 295), (410, 303)], fill="#ffffff")

    d.text((50, 355), "• Result: Locks exactly to byte 0x0400 on valid instruction and alignment boundaries.", fill="#cbd5e1", font=f_body)
    d.text((50, 377), "• Jitter: 0-Byte residual jitter. F1-Score: 0.914 at strict 4-byte tolerance (τ = 4B).", fill="#10b981", font=f_small)

    out_p = os.path.join(img_dir, "tour-snapper.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

def make_tour_mixed_isa():
    W, H = 900, 450
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    f_title = get_font(18, bold=True)
    f_box_h = get_font(14, bold=True)
    f_body = get_font(12)
    f_small = get_font(11)
    f_mono = get_font(12)

    d.text((35, 25), "MIXED-ISA DISENTANGLEMENT & ARCHITECTURE MODE SWITCHING", fill="#f8fafc", font=f_title)
    d.text((35, 52), "Disentangles polyglot payloads and multi-architecture firmware streams without symbol tables.", fill="#94a3b8", font=f_body)

    # 3 Stage Flow
    stages = [
        ("STAGE 1: BOOT VECTOR", "0x0000 .. 0x0400", "ARM32 (ARMv7-A)", "Vector Table & MMU Setup", "#06b6d4", 50, 280),
        ("STAGE 2: CORE ROUTINE", "0x0400 .. 0x0E00", "Thumb-2 (ARMv7-M)", "Cryptographic Engine & RTOS", "#0284c7", 320, 560),
        ("STAGE 3: DIAGNOSTIC AGENT", "0x0E00 .. 0x1800", "x86_64 Payload", "Recovery Shell & Agent Code", "#3b82f6", 600, 850)
    ]

    for (header, rng, isa, desc, color, x1, x2) in stages:
        d.rounded_rectangle([x1, 95, x2, 330], radius=8, fill="#0f172a", outline=color, width=2)
        d.rounded_rectangle([x1 + 15, 110, x2 - 15, 135], radius=4, fill=color)
        d.text((x1 + 22, 114), header, fill="#ffffff", font=get_font(11, bold=True))

        d.text((x1 + 20, 150), rng, fill="#f8fafc", font=f_mono)
        d.text((x1 + 20, 175), isa, fill=color, font=f_box_h)
        d.text((x1 + 20, 205), desc, fill="#cbd5e1", font=f_body)

        # Confidence gauge inside card
        d.text((x1 + 20, 240), "Softmax Probability: 99.4%", fill="#10b981", font=f_small)
        d.rounded_rectangle([x1 + 20, 260, x2 - 20, 275], radius=4, fill="#1e293b")
        d.rounded_rectangle([x1 + 20, 260, x1 + 20 + int((x2 - x1 - 40) * 0.994), 275], radius=4, fill="#10b981")
        d.text((x1 + 20, 290), "Viterbi Transition Penalty: Passed", fill="#94a3b8", font=f_small)

    # Connecting transition arrows
    d.line([280, 212, 320, 212], fill="#f59e0b", width=3)
    d.polygon([(315, 207), (325, 212), (315, 217)], fill="#f59e0b")

    d.line([560, 212, 600, 212], fill="#f59e0b", width=3)
    d.polygon([(595, 207), (605, 212), (595, 217)], fill="#f59e0b")

    # Bottom summary box
    d.rounded_rectangle([35, 350, W - 35, 420], radius=6, fill="#0b1120", outline="#1e293b")
    d.text((50, 362), "Supported Target Architectures:", fill="#94a3b8", font=f_small)
    d.text((50, 382), "ARM32 (ARMv7-A/R) • Thumb-2 (ARMv7-M) • AArch64 (ARMv8-A) • x86-64 (AMD64) • MIPS32 • RISC-V (RV32/64)", fill="#38bdf8", font=f_box_h)

    out_p = os.path.join(img_dir, "tour-mixed-isa.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

def make_tour_conformal():
    W, H = 900, 450
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    f_title = get_font(18, bold=True)
    f_box_h = get_font(14, bold=True)
    f_body = get_font(12)
    f_small = get_font(11)
    f_mono = get_font(12)

    d.text((35, 25), "CONFORMAL RISK CONTROL & UNCERTAINTY RADAR", fill="#f8fafc", font=f_title)
    d.text((35, 52), "Quantifies prediction ambiguity and provides mathematical coverage guarantees for security QA.", fill="#94a3b8", font=f_body)

    # 2 Comparison Panels
    # Left: Opaque vs Deflate Distinction
    d.rounded_rectangle([35, 85, 435, 340], radius=8, fill="#0f172a", outline="#8b5cf6", width=2)
    d.text((50, 102), "HIGH-ENTROPY OPAQUE DISCRIMINATION", fill="#c084fc", font=f_box_h)
    d.text((50, 130), "Distinguishes Encrypted vs Compressed Payloads:", fill="#f8fafc", font=f_body)
    
    d.text((50, 160), "• AES / ChaCha20 Ciphertext:", fill="#cbd5e1", font=f_body)
    d.text((70, 180), "Shannon Entropy H = 7.989 b/B (Max Uniformity)", fill="#a855f7", font=f_mono)
    d.text((70, 200), "Chi-Square p-value: > 0.45 | Prediction: OPAQUE", fill="#10b981", font=f_small)

    d.text((50, 230), "• Deflate / Zlib / LZO Framed Compression:", fill="#cbd5e1", font=f_body)
    d.text((70, 250), "Shannon Entropy H = 7.420 b/B (Deflate Header 0x78)", fill="#38bdf8", font=f_mono)
    d.text((70, 270), "Huffman Table Signature | Prediction: COMPRESSED", fill="#10b981", font=f_small)

    d.text((50, 305), "Zero False Assumptions on Opaque Blobs", fill="#f59e0b", font=get_font(11, bold=True))

    # Right: Calibrated Coverage Sets
    d.rounded_rectangle([465, 85, W - 35, 340], radius=8, fill="#0f172a", outline="#10b981", width=2)
    d.text((480, 102), "FINITE-SAMPLE COVERAGE GUARANTEES", fill="#a7f3d0", font=f_box_h)
    d.text((480, 130), "Conformal Prediction Set S(x) (1 - α = 95%):", fill="#f8fafc", font=f_body)

    d.rounded_rectangle([480, 160, W - 50, 210], radius=6, fill="#1e293b")
    d.text((495, 172), "Clean Region:", fill="#94a3b8", font=f_small)
    d.text((585, 172), "S(x) = { ARM32_CODE }", fill="#10b981", font=f_box_h)
    d.text((495, 192), "Empirical Error Rate: < 0.8%  |  Set Size: 1.0", fill="#cbd5e1", font=f_small)

    d.rounded_rectangle([480, 225, W - 50, 285], radius=6, fill="#1e293b")
    d.text((495, 237), "Ambiguous Boundary:", fill="#94a3b8", font=f_small)
    d.text((630, 237), "S(x) = { ARM32, THUMB2 }", fill="#f59e0b", font=f_box_h)
    d.text((495, 257), "Safety Mask: ISOLATED  |  Set Size: 2.0 (Ambiguous)", fill="#fde68a", font=f_small)

    d.text((480, 305), "Calibrated With Split Conformal Risk Control", fill="#38bdf8", font=get_font(11, bold=True))

    # Bottom summary
    d.rounded_rectangle([35, 360, W - 35, 420], radius=6, fill="#0b1120", outline="#1e293b")
    d.text((50, 372), "Mathematical Calibration Integrity:", fill="#94a3b8", font=f_small)
    d.text((50, 392), "ECE: 0.041  |  Brier Score: 0.062  |  Temperature Scale: T = 1.28  |  Guaranteed Coverage: P(Y in S(X)) >= 0.95", fill="#10b981", font=f_box_h)

    out_p = os.path.join(img_dir, "tour-conformal.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

# -------------------------------------------------------------------
# 4. SOCIAL OPEN GRAPH PREVIEW (1200 x 630)
# -------------------------------------------------------------------
def make_og_preview():
    W, H = 1200, 630
    im = Image.new("RGB", (W, H), "#070b14")
    d = ImageDraw.Draw(im)

    f_hero = get_font(38, bold=True)
    f_sub = get_font(18)
    f_title = get_font(16, bold=True)
    f_mono = get_font(13)
    f_badge = get_font(13, bold=True)

    # Ambient glow
    for r in range(400, 0, -25):
        d.ellipse([600 - r, 315 - r, 600 + r, 315 + r], fill=(12, 22, 40))

    # Decorative cyber grid lines
    for x in range(0, W, 80):
        d.line([x, 0, x, H], fill="#0f172a", width=1)
    for y in range(0, H, 80):
        d.line([0, y, W, y], fill="#0f172a", width=1)

    # Logo Circuit Shield
    d.rounded_rectangle([60, 60, 140, 140], radius=16, fill="#0b1120", outline="#06b6d4", width=3)
    # Stylized "K"
    d.line([85, 80, 85, 120], fill="#06b6d4", width=6)
    d.line([85, 100, 115, 80], fill="#38bdf8", width=6)
    d.line([85, 100, 115, 120], fill="#8b5cf6", width=6)

    d.text((165, 75), "KETHRAVAX", fill="#f8fafc", font=f_hero)
    d.rounded_rectangle([445, 82, 530, 112], radius=6, fill="#064e3b")
    d.text((455, 88), "v0.1.0", fill="#a7f3d0", font=f_badge)

    d.text((60, 180), "Multi-Class Structural Byte Segmentation", fill="#f8fafc", font=f_hero)
    d.text((60, 235), "Deconstruct Raw Binary Streams Without ELF, PE, or Mach-O Headers", fill="#38bdf8", font=f_sub)

    # Feature card
    card_r = [60, 290, W - 60, 520]
    d.rounded_rectangle(card_r, radius=12, fill="#0b1120", outline="#1e293b", width=2)

    # 4 Pills
    pills = [
        ("⚡ 48.2K Params", "100% Offline CPU Backbone"),
        ("🎯 0-Byte Residual", "Exact Boundary Discontinuity Head"),
        ("🧬 7 Classes & 6 ISAs", "Mixed-Architecture Disentanglement"),
        ("🛡️ Conformal Calibration", "Calibrated Uncertainty Guarantee"),
    ]

    px = 90
    for (top_txt, btm_txt) in pills:
        d.rounded_rectangle([px, 320, px + 240, 410], radius=8, fill="#1e293b")
        d.text((px + 15, 335), top_txt, fill="#f8fafc", font=f_title)
        d.text((px + 15, 365), btm_txt, fill="#94a3b8", font=get_font(11))
        px += 260

    # Mini Hex preview in card
    d.rectangle([90, 440, W - 90, 490], fill="#020617", outline="#1e293b")
    d.text((110, 455), "0x0000:  48 83 ec 28 e8 00 [ARM32]  |  0x0400:  2f 65 74 63 [STRINGS]  |  0x0880:  4b 0a 68 18 [THUMB2]  |  0x0E00:  8f 3d a4 91 [OPAQUE]", fill="#38bdf8", font=f_mono)

    # Footer author strip
    d.text((60, 560), "Created by Arin Goel &bull; Open Source Apache-2.0 &bull; https://kethravax.pages.dev", fill="#64748b", font=f_sub)

    out_p = os.path.join(img_dir, "og-preview.png")
    im.save(out_p, "PNG", quality=95)
    print("Created", out_p)

# -------------------------------------------------------------------
# 5. ANIMATED STUDIO PREVIEW GIF (960 x 540)
# -------------------------------------------------------------------
def make_studio_gif():
    W, H = 960, 540
    frames = []

    f_title = get_font(13, bold=True)
    f_body = get_font(11)
    f_small = get_font(10)
    f_mono = get_font(10)

    # 6 scrub steps
    steps = [
        (0.15, "0x00000240", "sub r2, r1, #4", "ARM32", "#06b6d4", "99.9%", "5.62 b/B"),
        (0.25, "0x00000480", ".asciz \"/dev/ttyS0\"", "STRING", "#f59e0b", "99.8%", "3.41 b/B"),
        (0.35, "0x00000720", ".word 0x0880, 0x0890", "TABLE", "#10b981", "99.1%", "4.15 b/B"),
        (0.48, "0x00000950", "ldr r3, [pc, #0x14]", "THUMB2", "#0284c7", "99.7%", "5.88 b/B"),
        (0.65, "0x00000CE0", "[AES-GCM Ciphertext]", "OPAQUE", "#8b5cf6", "99.9%", "7.98 b/B"),
        (0.85, "0x00000F40", "mov rbp, rsp; ret", "x86_64", "#3b82f6", "99.4%", "5.91 b/B"),
    ]

    for (scrub_pct, cur_off, cur_asm, cur_cat, cur_col, cur_conf, cur_ent) in steps:
        im = Image.new("RGB", (W, H), "#070b14")
        d = ImageDraw.Draw(im)

        # Window
        d.rounded_rectangle([15, 15, W - 15, H - 15], radius=10, fill="#0b1120", outline="#1e293b", width=2)
        # Titlebar
        d.rounded_rectangle([15, 15, W - 15, 50], radius=10, fill="#0f172a")
        d.rectangle([15, 40, W - 15, 50], fill="#0f172a")
        # Traffic lights
        d.ellipse([28, 28, 38, 38], fill="#ef4444")
        d.ellipse([44, 28, 54, 38], fill="#f59e0b")
        d.ellipse([60, 28, 70, 38], fill="#10b981")

        d.text((90, 26), "KETHRAVAX Workbench &bull; cortex_m4_firmware_v2.04.bin [Scrubbing Active]", fill="#f8fafc", font=f_title)
        d.text((W - 190, 27), "● LIVE SCRUBBER", fill="#06b6d4", font=f_small)

        # Ribbon
        rw = W - 60
        rx0, ry0 = 30, 65
        rh = 18
        d.rounded_rectangle([rx0, ry0 - 4, rx0 + rw, ry0 + rh + 4], radius=6, fill="#020617")

        segments = [
            (0.00, 0.20, "#06b6d4"),
            (0.20, 0.30, "#f59e0b"),
            (0.30, 0.40, "#10b981"),
            (0.40, 0.58, "#0284c7"),
            (0.58, 0.75, "#8b5cf6"),
            (0.75, 0.90, "#3b82f6"),
            (0.90, 1.00, "#475569"),
        ]
        for (s_start, s_end, color) in segments:
            x1 = rx0 + int(s_start * rw)
            x2 = rx0 + int(s_end * rw)
            d.rectangle([x1, ry0, x2, ry0 + rh], fill=color)

        # Playhead needle
        px = rx0 + int(scrub_pct * rw)
        d.line([px, ry0 - 6, px, ry0 + rh + 6], fill="#ffffff", width=2)
        d.polygon([(px - 4, ry0 - 8), (px + 4, ry0 - 8), (px, ry0 - 2)], fill="#ffffff")

        # Viewport Left (Hex & Disasm)
        d.rounded_rectangle([30, 100, 640, H - 25], radius=6, fill="#020617", outline="#1e293b")
        d.text((45, 110), "OFFSET", fill="#64748b", font=f_small)
        d.text((120, 110), "HEX BYTES", fill="#64748b", font=f_small)
        d.text((270, 110), "DISASSEMBLY / OPCODES", fill="#64748b", font=f_small)
        d.text((540, 110), "CLASS", fill="#64748b", font=f_small)
        d.line([40, 126, 630, 126], fill="#1e293b")

        # Active row
        d.rectangle([40, 132, 630, 158], fill="#091424")
        d.text((45, 138), cur_off, fill="#38bdf8", font=f_mono)
        d.text((120, 138), "48 83 ec 28 e8 00", fill="#cbd5e1", font=f_mono)
        d.text((270, 138), cur_asm, fill="#f8fafc", font=f_mono)
        d.rounded_rectangle([535, 136, 595, 154], radius=3, fill=cur_col)
        d.text((542, 138), cur_cat, fill="#ffffff", font=get_font(9, bold=True))

        # Static surrounding rows
        sample_rows = [
            ("0x00000880", "4b 0a 68 18", "ldr r3, [pc, #0x28]", "THUMB2", "#0284c7"),
            ("0x00000888", "21 01 70 01", "movs r1, #1; pop {r3}", "THUMB2", "#0284c7"),
            ("0x00000890", "2f 65 74 63", ".asciz \"/firmware\"", "STRING", "#f59e0b"),
            ("0x00000898", "00 00 08 80", ".word 0x0880, 0x0890", "TABLE", "#10b981"),
            ("0x000008A0", "8f 3d a4 91", "[AES GCM Payload]", "OPAQUE", "#8b5cf6"),
            ("0x000008A8", "00 00 00 00", "ALIGN 16 Padding", "PAD", "#475569"),
            ("0x000008B0", "48 89 e5 48", "push rbp; mov rbp, rsp", "x86_64", "#3b82f6"),
        ]
        gy = 166
        for (off, hx, ds, ct, cl) in sample_rows:
            d.text((45, gy), off, fill="#64748b", font=f_mono)
            d.text((120, gy), hx, fill="#94a3b8", font=f_mono)
            d.text((270, gy), ds, fill="#cbd5e1", font=f_mono)
            d.rounded_rectangle([535, gy - 2, 595, gy + 14], radius=3, fill=cl)
            d.text((542, gy), ct, fill="#ffffff", font=get_font(9, bold=True))
            gy += 22

        # Right Viewport (HUD)
        d.rounded_rectangle([655, 100, W - 30, H - 25], radius=6, fill="#0f172a", outline="#1e293b")
        d.text((670, 115), "Telemetry Inspector HUD", fill="#f8fafc", font=f_title)
        d.text((670, 135), "Real-time Conformal Analysis", fill="#64748b", font=f_small)

        # Stat cards
        d.rounded_rectangle([670, 158, W - 45, 225], radius=6, fill="#1e293b")
        d.text((680, 168), "Current Region Class", fill="#94a3b8", font=f_small)
        d.text((680, 186), f"{cur_cat} ({cur_conf})", fill=cur_col, font=f_title)
        d.text((680, 206), f"Entropy: {cur_ent}", fill="#cbd5e1", font=f_small)

        d.rounded_rectangle([670, 235, W - 45, 310], radius=6, fill="#0b1120", outline="#10b981", width=1)
        d.text((680, 245), "Boundary Snapping Verdict", fill="#94a3b8", font=f_small)
        d.text((680, 265), "0-BYTE RESIDUAL LOCK", fill="#10b981", font=f_title)
        d.text((680, 288), "F1: 0.914 (τ = 4B) | Discontinuity: 0B", fill="#a7f3d0", font=f_small)

        d.rounded_rectangle([670, 320, W - 45, 410], radius=6, fill="#0b1120", outline="#1e293b")
        d.text((680, 330), "Conformal Risk Radar", fill="#8b5cf6", font=f_small)
        d.text((680, 350), "P(Coverage) >= 0.95", fill="#f8fafc", font=f_title)
        d.text((680, 372), f"Active Offset: {cur_off}", fill="#38bdf8", font=f_mono)
        d.text((680, 390), "ECE: 0.041 | Temp: T=1.28", fill="#94a3b8", font=f_small)

        # Buttons
        d.rounded_rectangle([670, 435, 780, 475], radius=6, fill="#1e293b")
        d.text((695, 448), "Export JSON", fill="#f8fafc", font=f_small)
        d.rounded_rectangle([795, 435, W - 45, 475], radius=6, fill="#0284c7")
        d.text((820, 448), "Export CSV", fill="#ffffff", font=f_small)

        frames.append(im)

    out_p = os.path.join(img_dir, "studio-preview.gif")
    frames[0].save(out_p, save_all=True, append_images=frames[1:], duration=700, loop=0)
    print("Created", out_p)

if __name__ == "__main__":
    print("Generating Kethravax website visual assets...")
    make_studio_preview()
    make_architecture_diagram()
    make_tour_snapper()
    make_tour_mixed_isa()
    make_tour_conformal()
    make_og_preview()
    make_studio_gif()
    print("All website visual assets generated successfully!")
