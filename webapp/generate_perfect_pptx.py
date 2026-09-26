import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE

def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    # Colors exactly matched to HTML presentation
    BG_DARK = RGBColor(11, 15, 23)        # #0b0f17
    CARD_BG = RGBColor(30, 41, 59)        # #1e293b
    CARD_BORDER = RGBColor(51, 65, 85)    # #334155
    TEXT_WHITE = RGBColor(248, 250, 252)  # #f8fafc
    TEXT_MUTED = RGBColor(203, 213, 225)  # #cbd5e1 (lighter than before for contrast)
    TEXT_SUBTLE = RGBColor(148, 163, 184) # #94a3b8
    TEAL_PRIMARY = RGBColor(20, 184, 166) # #14b8a6
    CYAN_ACCENT = RGBColor(6, 182, 212)   # #06b6d4
    EMERALD_GREEN = RGBColor(16, 185, 129)# #10b981
    AMBER_WARN = RGBColor(245, 158, 11)   # #f59e0b
    ROSE_ACCENT = RGBColor(244, 63, 94)   # #f43f5e
    PURPLE_ACCENT = RGBColor(168, 85, 247)# #a855f7
    WIN_HIGHLIGHT_BG = RGBColor(19, 78, 74) # #134e4a
    INNER_CARD_BG = RGBColor(15, 23, 42)  # #0f172a

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = BG_DARK
        bg.line.fill.background()
        return bg

    def add_header(slide, title, category, subtitle="", timing=""):
        # Header text
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.35), Inches(9.0), Inches(1.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = TEAL_PRIMARY
        
        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(25)  # Larger font
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE
        p_title.space_before = Pt(3)

        if subtitle:
            p_sub = tf.add_paragraph()
            p_sub.text = subtitle
            p_sub.font.size = Pt(13)  # Larger font
            p_sub.font.color.rgb = CYAN_ACCENT
            p_sub.space_before = Pt(2)

        # Timing Badge Pill on Top Right
        if timing:
            pill = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(10.0), Inches(0.4), Inches(2.533), Inches(0.48))
            pill.fill.solid()
            pill.fill.fore_color.rgb = RGBColor(8, 47, 73) # cyan-950
            pill.line.color.rgb = RGBColor(14, 116, 144) # cyan-700
            pill.line.width = Pt(1)
            ptf = pill.text_frame
            ptf.margin_left = ptf.margin_top = ptf.margin_right = ptf.margin_bottom = 0
            pp = ptf.paragraphs[0]
            pp.alignment = PP_ALIGN.CENTER
            pp.text = timing
            pp.font.size = Pt(11)
            pp.font.bold = True
            pp.font.color.rgb = CYAN_ACCENT

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER, border_width=1):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(border_width)
        return card

    def add_footer(slide, left_text, right_text):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(6.92), Inches(11.733), Inches(0.35))
        tf = tb.text_frame
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = left_text
        p.font.size = Pt(10.5)
        p.font.color.rgb = TEXT_SUBTLE

        tb_r = slide.shapes.add_textbox(Inches(7.0), Inches(6.92), Inches(5.533), Inches(0.35))
        tf_r = tb_r.text_frame
        tf_r.margin_left = tf_r.margin_top = tf_r.margin_right = tf_r.margin_bottom = 0
        pr = tf_r.paragraphs[0]
        pr.alignment = PP_ALIGN.RIGHT
        pr.text = right_text
        pr.font.size = Pt(10.5)
        pr.font.color.rgb = TEXT_SUBTLE

    def add_notes(slide, notes_text):
        notes_slide = slide.notes_slide
        tf = notes_slide.notes_text_frame
        tf.text = notes_text

    # =========================================================================
    # SLIDE 1: Title & Executive Summary
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    
    # Title & Subtitle box
    t_box = s1.shapes.add_textbox(Inches(0.8), Inches(0.55), Inches(11.733), Inches(2.2))
    ttf = t_box.text_frame
    ttf.word_wrap = True
    ttf.margin_left = ttf.margin_top = ttf.margin_right = ttf.margin_bottom = 0

    p = ttf.paragraphs[0]
    p.text = "EXECUTIVE SUMMARY • HACKATHON FINAL"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    p = ttf.add_paragraph()
    p.text = "SleepLens: Dual-Tier AI for Sleep Stage Classification\n& Sleep Quality Assessment"
    p.font.size = Pt(30) # Larger, bold
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(6)

    p = ttf.add_paragraph()
    p.text = "Bridging 30-Second Discrete Staging with Continuous Depth Dynamics & Microstructural Phenotyping"
    p.font.size = Pt(15)
    p.font.color.rgb = CYAN_ACCENT
    p.space_before = Pt(6)

    # 3 Cards matching HTML
    # Card 1: Amber border
    add_card(s1, Inches(0.8), Inches(2.95), Inches(3.64), Inches(3.8), border=AMBER_WARN, border_width=2)
    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(3.15), Inches(3.24), Inches(3.4))
    tf1 = tb1.text_frame
    tf1.word_wrap = True
    tf1.margin_left = tf1.margin_top = tf1.margin_right = tf1.margin_bottom = 0
    p = tf1.paragraphs[0]
    p.text = "⚠️ The Clinical Bottleneck"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = AMBER_WARN

    bullets1 = [
        "• Standard overnight PSG requires 1.5–2 hours of manual visual scoring per recording.",
        "• Inter-scorer agreement is notoriously low on transitions (N1 < 60%).",
        "• Coarse 5-stage AASM scoring discards continuous sleep depth and cortical synchronization dynamics."
    ]
    for b in bullets1:
        p = tf1.add_paragraph()
        p.text = b
        p.font.size = Pt(13) # Larger font
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(12)

    # Card 2: Cyan border (glow)
    add_card(s1, Inches(4.84), Inches(2.95), Inches(3.64), Inches(3.8), border=CYAN_ACCENT, border_width=2)
    tb2 = s1.shapes.add_textbox(Inches(5.04), Inches(3.15), Inches(3.24), Inches(3.4))
    tf2 = tb2.text_frame
    tf2.word_wrap = True
    tf2.margin_left = tf2.margin_top = tf2.margin_right = tf2.margin_bottom = 0
    p = tf2.paragraphs[0]
    p.text = "🧠 Dual-Tier AI Engine"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    bullets2 = [
        "• Tier 1 (Staging): 4-Model Ensemble Macro-F1 0.8425 (Cohen's κ 0.831) across 237,936 epochs.",
        "• Tier 2 (Depth): SDI Transformer (npj Digital Med 2025) continuous 0–1 depth trajectory + 96 clinical parameters.",
        "• Minimal Sensors: 2-sensor montage (Fpz+EOG) retains 99.5% F1 performance!"
    ]
    for b in bullets2:
        p = tf2.add_paragraph()
        p.text = b
        p.font.size = Pt(13) # Larger font
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(12)

    # Card 3: Emerald border
    add_card(s1, Inches(8.88), Inches(2.95), Inches(3.64), Inches(3.8), border=EMERALD_GREEN, border_width=2)
    tb3 = s1.shapes.add_textbox(Inches(9.08), Inches(3.15), Inches(3.24), Inches(3.4))
    tf3 = tb3.text_frame
    tf3.word_wrap = True
    tf3.margin_left = tf3.margin_top = tf3.margin_right = tf3.margin_bottom = 0
    p = tf3.paragraphs[0]
    p.text = "💻 Production Platform"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = EMERALD_GREEN

    bullets3 = [
        "• Full-stack clinical webapp: Next.js 14 + Django REST Framework.",
        "• Interactive hypnograms, continuous depth curves, and raw microvolt signals explorer.",
        "• Automated LLM clinical report + OpenCode interactive diagnostic assistant."
    ]
    for b in bullets3:
        p = tf3.add_paragraph()
        p.text = b
        p.font.size = Pt(13) # Larger font
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(12)

    add_footer(s1, "SleepLens Platform • Confidential & Clinical Research Prototype", "Slide 1 of 9 • 0:00–0:45")
    add_notes(s1, "Target: 0:00 - 0:45 (45s)\nGood morning. Today we present SleepLens, an end-to-end clinical AI platform designed to transform sleep diagnostics. Polysomnography is gold standard, yet analyzing 8 hours of multichannel PSG takes hours of tedious manual scoring and collapses complex neurobiology into 5 discrete stages. SleepLens solves this with a two-tiered AI system: an ensemble staging model with calibrated uncertainty, and a continuous sleep depth transformer with a 96-feature phenotyping engine, deployed in a production-ready clinical web application.")

    # =========================================================================
    # SLIDE 2: Dataset, Preprocessing & Standardization
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Dataset, Preprocessing & Standardization", "BENCHMARK & EXPERIMENTAL INTEGRITY",
               "Sleep-EDF Expanded: Full 197 nights with leakage-free subject-atomic cross-validation", "0:45 – 1:30 | 45s")

    # Left Card: Dataset Stats
    add_card(s2, Inches(0.8), Inches(1.6), Inches(5.65), Inches(5.1))
    tb_ds = s2.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.7))
    tf_ds = tb_ds.text_frame
    tf_ds.word_wrap = True
    tf_ds.margin_left = tf_ds.margin_top = tf_ds.margin_right = tf_ds.margin_bottom = 0

    p = tf_ds.paragraphs[0]
    p.text = "📊 Full Benchmark: Sleep-EDF Expanded (PhysioNet)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    # Inner box 1
    p = tf_ds.add_paragraph()
    p.text = "Scale & Volume:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(14)
    p = tf_ds.add_paragraph()
    p.text = "• 197 all-night recordings (~2,000 hours of continuous PSG)\n• 237,936 validated 30-second epochs (epochs_v3 benchmark)"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Inner box 2
    p = tf_ds.add_paragraph()
    p.text = "Dual-Cohort Validation (Never Confounded):"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(14)
    p = tf_ds.add_paragraph()
    p.text = "• Sleep Cassette (SC): 153 recordings (ambulatory healthy subjects)\n• Sleep Telemetry (ST): 44 recordings (in-patient clinical cohort)"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Inner box 3
    p = tf_ds.add_paragraph()
    p.text = "Leakage-Free Protocol: Subject-Atomic 5-Fold CV"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(14)
    p = tf_ds.add_paragraph()
    p.text = "• Zero subject overlap between training, tuning, and testing (folds5_v3)\n• Prevents overoptimistic memorization seen in subject-leaked studies."
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    # Right Card: Preprocessing
    add_card(s2, Inches(6.85), Inches(1.6), Inches(5.68), Inches(5.1))
    tb_pr = s2.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.18), Inches(4.7))
    tf_pr = tb_pr.text_frame
    tf_pr.word_wrap = True
    tf_pr.margin_left = tf_pr.margin_top = tf_pr.margin_right = tf_pr.margin_bottom = 0

    p = tf_pr.paragraphs[0]
    p.text = "⚙️ Signal Harmonization & Preprocessing"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    steps = [
        ("1. Canonical 100 Hz Resampling", "Polyphase anti-aliasing filtering across all raw input channels to eliminate sample rate divergence across hospital equipment."),
        ("2. Electrode Standardization", "Harmonizes diverse montages to canonical channels: Frontal EEG (Fpz-Cz), Occipital EEG (Pz-Oz), Ocular (EOG horiz), Chin (EMG submental)."),
        ("3. Lights-Off Windowing (BENCHMARK_30)", "Automatically cuts extensive pre/post recording waking padding while strictly preserving sleep onset and offset transition dynamics.")
    ]

    for title, desc in steps:
        p = tf_pr.add_paragraph()
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(16)
        p = tf_pr.add_paragraph()
        p.text = desc
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    add_footer(s2, "Evaluation Protocol: Subject-disjoint 5-fold cross validation with unified benchmark windowing", "BENCHMARK_30 Window: 237,936 valid epochs")
    add_notes(s2, "Target: 0:45 - 1:30 (45s)\nTo ensure clinical validity, we used the full Sleep-EDF Expanded dataset across all 197 nights and nearly 238,000 epochs. Unlike many published papers that suffer from subject leakage, we enforced a strict subject-atomic 5-fold cross-validation scheme. We evaluated both cohorts: ambulatory cassette and clinical telemetry. Every recording is harmonized to 100 Hz, with standardized electrode alignments and automated lights-off windowing to ensure fair, reproducible benchmarking.")

    # =========================================================================
    # SLIDE 3: Tier 1 Model — Staging Benchmarks
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "30-Second Sleep Stage Classification (SSC)", "TIER 1 AI MODEL",
               "Systematic benchmark of 25+ configurations across all 197 nights", "1:30 – 2:25 | 55s")

    # Table
    rows, cols = 7, 10
    tbl_shape = s3.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.733), Inches(3.1))
    table = tbl_shape.table

    col_widths = [Inches(1.1), Inches(3.633), Inches(0.95), Inches(0.85), Inches(0.85), Inches(0.9), Inches(0.85), Inches(0.85), Inches(0.85), Inches(0.9)]
    for i, w in enumerate(col_widths):
        table.columns[i].width = w

    headers = ["Run", "Architecture / Montage", "Macro-F1", "SC F1", "ST F1", "N1 F1", "N2 F1", "N3 F1", "REM F1", "Cohen κ"]
    data = [
        ["E19 (Best)", "4-Model Diverse Ensemble (ANY3ch + ANY2ch + USleep + LGBM)", "0.8425", "0.836", "0.865", "0.635", "0.892", "0.833", "0.915", "0.831"],
        ["E11", "AnySleep 3ch (Fpz+Pz+EOG) — Best Single Model", "0.8267", "0.809", "0.878", "0.622", "0.880", "0.788", "0.904", "0.812"],
        ["E11d", "AnySleep 2-Sensor (Fpz+EOG) — Best 2-Sensor", "0.8227", "0.811", "0.865", "0.592", "0.880", "0.812", "0.905", "0.808"],
        ["E20", "RobustSleepNet Fpz (Clean Baseline — No Sleep-EDF)", "0.7501", "0.736", "0.788", "0.442", "0.828", "0.717", "0.855", "0.724"],
        ["E00", "LightGBM (11 Spectral/Bandpower Features)", "0.6672", "—", "—", "0.339", "0.752", "0.687", "0.585", "0.612"],
        ["E01", "YASA Clinical Baseline (Fpz-Cz Random Forest)", "0.5225", "0.486", "0.611", "0.100", "0.737", "0.538", "0.557", "0.473"],
    ]

    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = CARD_BG
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(11.5) # Larger font
        p.font.bold = True
        p.font.color.rgb = CYAN_ACCENT
        if c >= 2:
            p.alignment = PP_ALIGN.CENTER

    for r, row in enumerate(data):
        for c, val in enumerate(row):
            cell = table.cell(r + 1, c)
            cell.text = val
            cell.fill.solid()
            if r == 0:
                cell.fill.fore_color.rgb = WIN_HIGHLIGHT_BG
            else:
                cell.fill.fore_color.rgb = INNER_CARD_BG
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(11) # Larger font
            if c >= 2:
                p.alignment = PP_ALIGN.CENTER
            if r == 0:
                p.font.bold = True
                p.font.color.rgb = TEAL_PRIMARY if c in [0, 2, 5, 8, 9] else TEXT_WHITE
            else:
                p.font.color.rgb = TEXT_WHITE if c in [0, 1] else (ROSE_ACCENT if (r==5 and c in [2,5]) else TEXT_MUTED)

    # 3 Key Insights Cards matching HTML
    card_w = Inches(3.64)
    c_y = Inches(4.88)
    c_h = Inches(1.85)

    insights = [
        ("1. Diversity Beats Scale", "Adding our weak LightGBM model (0.667 F1) boosted deep models by +0.016 F1 because it captures orthogonal spectral features rather than raw waveforms.", TEAL_PRIMARY, Inches(0.8)),
        ("2. Record Class Breakdown", "Winning ensemble sets benchmark records across all 4 key sleep stages: N1 (0.635), N2 (0.892), N3 (0.833), and REM (0.915).", CYAN_ACCENT, Inches(4.84)),
        ("3. Viterbi Rejected", "Viterbi transition prior degraded performance (0.8267 → 0.8259) because AnySleep already has an intrinsic 14-minute temporal receptive field.", AMBER_WARN, Inches(8.88)),
    ]

    for title, text, col, left_x in insights:
        add_card(s3, left_x, c_y, card_w, c_h)
        tb = s3.shapes.add_textbox(left_x + Inches(0.2), c_y + Inches(0.15), card_w - Inches(0.4), c_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13.5) # Larger font
        p.font.bold = True
        p.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.size = Pt(11.5) # Larger font
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(4)

    add_footer(s3, "Winning 4-member ensemble: Fold-honest OOF evaluation agreement across all 5 folds", "Cohen's κ = 0.831 (Matches expert human consensus)")
    add_notes(s3, "Target: 1:30 - 2:25 (55s)\nFor sleep stage classification, we systematically benchmarked 25+ configurations. Classical heuristics like YASA struggle severely on N1 sleep at only 0.10 F1. Deep neural models like AnySleep perform exceptionally at 0.8267. Our winning system, E19, is a 4-member fold-honest ensemble combining AnySleep 3-channel, AnySleep 2-channel, U-Sleep CSDP, and our engineered LightGBM model. It reached 0.8425 Macro-F1 with a Cohen's Kappa of 0.831. Crucially, the weak LightGBM model improved the ensemble by introducing non-redundant spectral feature diversity.")

    # =========================================================================
    # SLIDE 4: Sensor Ablation & Explainability
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Sensor Ablation & Explainable AI (XAI)", "SSC ENGINEERING INSIGHTS",
               "Finding the minimal wearable configuration and auditing deep network attention", "2:25 – 3:15 | 50s")

    # Left: Channel Ablation Card
    add_card(s4, Inches(0.8), Inches(1.6), Inches(5.65), Inches(5.1))
    tb_ab = s4.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.7))
    tf_ab = tb_ab.text_frame
    tf_ab.word_wrap = True
    tf_ab.margin_left = tf_ab.margin_top = tf_ab.margin_right = tf_ab.margin_bottom = 0

    p = tf_ab.paragraphs[0]
    p.text = "🔌 Channel Ablation: Minimal Hardware Montage"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    ablation_items = [
        ("Full 3-Channel (Fpz-Cz + Pz-Oz + EOG)", "0.8267 F1 (Ref)", False),
        ("★ 2-Sensor Setup (Fpz-Cz + EOG)", "0.8227 F1 (-0.004 Δ)", True),
        ("Dual EEG (Fpz-Cz + Pz-Oz, no EOG)", "0.8134 F1 (-0.013 Δ)", False),
        ("Single Frontal EEG (Fpz-Cz Only)", "0.8015 F1 (-0.025 Δ)", False),
        ("Single Occipital EEG (Pz-Oz Only)", "0.7736 F1 (-0.053 Δ)", False),
    ]

    for label, score, highlight in ablation_items:
        p = tf_ab.add_paragraph()
        p.text = f"{label}  ──▶  {score}"
        p.font.size = Pt(13) # Larger font
        p.space_before = Pt(8)
        if highlight:
            p.font.bold = True
            p.font.color.rgb = CYAN_ACCENT
        else:
            p.font.color.rgb = TEXT_WHITE if "Full" in label else TEXT_MUTED

    p = tf_ab.add_paragraph()
    p.text = "Clinical Finding: Posterior EEG (Pz-Oz) is droppable. Adding EOG to frontal EEG captures ocular dipole saccades directly, boosting true REM recall to 0.913 (vs 0.897 on full 3-channel)."
    p.font.size = Pt(12)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(14)

    # Right: Attention & Confidence
    add_card(s4, Inches(6.85), Inches(1.6), Inches(5.68), Inches(5.1))
    tb_att = s4.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.18), Inches(4.7))
    tf_att = tb_att.text_frame
    tf_att.word_wrap = True
    tf_att.margin_left = tf_att.margin_top = tf_att.margin_right = tf_att.margin_bottom = 0

    p = tf_att.paragraphs[0]
    p.text = "🔍 Attention Routing & Uncertainty Calibration"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    p = tf_att.add_paragraph()
    p.text = "Layer 12 Skip-Connection Channel Attention Routing:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(12)

    attn_points = [
        ("• WAKE:", "67.2% Pz Attention", "(Occipital alpha rhythm tracking)"),
        ("• N3 DEEP:", "93.0% EEG Attention", "(Slow-wave cortical sync, eyes quiet <7.1%)"),
        ("• REM SLEEP:", "52.0% EOG Attention", "(Saccadic burst tracking during atonia)"),
    ]
    for stage, stat, note in attn_points:
        p = tf_att.add_paragraph()
        p.text = f"{stage} {stat} {note}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(6)

    p = tf_att.add_paragraph()
    p.text = "Monotonic Confidence Calibration (ECE = 0.029):"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(14)

    p = tf_att.add_paragraph()
    p.text = "• Conf ≥ 0.90 (30.3% of night): 99.5% empirical accuracy.\n• Conf < 0.60 (~15% of night): Flagged with needs_review = true.\n• Doctor-in-the-Loop: Clinicians inspect only uncertain epochs."
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(6)

    add_footer(s4, "Hardware Target: 2-Sensor Wearable Headband (Fpz-Cz + EOG)", "Expected Calibration Error (ECE) = 0.029")
    add_notes(s4, "Target: 2:25 - 3:15 (50s)\nTwo practical questions: Can we run this on a minimal home device, and is the model interpretable? Our ablation proved that a two-sensor setup—one frontal EEG and one EOG—achieves 0.8227 F1, losing only 0.004 compared to three channels while actually improving REM detection. Deep skip-layer attention reveals the network dynamically shifts attention to posterior alpha in Wake, slow waves in N3, and surges to 52% EOG attention during REM. Finally, our confidence calibration is monotonic: epochs above 90% confidence are 99.5% accurate, enabling intelligent human-in-the-loop triage.")

    # =========================================================================
    # SLIDE 5: Tier 2 Model — Continuous Depth (SDI) & 96 Features
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Continuous Sleep Depth (SDI) & 96-Feature Engine", "TIER 2 AI MODEL",
               "Transcending 5 discrete steps into continuous neurobiological synchronization", "3:15 – 4:05 | 50s")

    # Top Card: SDI Transformer
    add_card(s5, Inches(0.8), Inches(1.6), Inches(11.733), Inches(2.35), border=CYAN_ACCENT, border_width=2)
    tb_sdi = s5.shapes.add_textbox(Inches(1.05), Inches(1.75), Inches(11.233), Inches(2.05))
    tf_sdi = tb_sdi.text_frame
    tf_sdi.word_wrap = True
    tf_sdi.margin_left = tf_sdi.margin_top = tf_sdi.margin_right = tf_sdi.margin_bottom = 0

    p = tf_sdi.paragraphs[0]
    p.text = "SDI Transformer Network (Zhou et al., npj Digital Medicine 2025)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    p = tf_sdi.add_paragraph()
    p.text = "Computes a continuous Sleep Depth Index (0.0 = Light/Wake to 1.0 = Deep SWA Sink) per 30-s epoch. Unlike discrete AASM staging, SDI quantifies gradual micro-arousals, sleep debt dissipation, and cyclic alternating patterns (CAP)."
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(6)

    # 5 Metrics
    p = tf_sdi.add_paragraph()
    p.text = "Standardized Research Vector:  [RB: SDI < 0.20 Shallow Burden]  •  [AP: Mean Sleep Depth]  •  [CV: Instability SD/Mean]  •  [MDR: Mean REM Depth]  •  [PR: Model REM Share]"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY
    p.space_before = Pt(8)

    # Bottom Card: 96-Parameter Engine
    add_card(s5, Inches(0.8), Inches(4.1), Inches(11.733), Inches(2.65))
    tb_feat = s5.shapes.add_textbox(Inches(1.05), Inches(4.25), Inches(11.233), Inches(2.35))
    tf_feat = tb_feat.text_frame
    tf_feat.word_wrap = True
    tf_feat.margin_left = tf_feat.margin_top = tf_feat.margin_right = tf_feat.margin_bottom = 0

    p = tf_feat.paragraphs[0]
    p.text = "📈 96-Parameter Physiological Extraction Engine"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    # 4 columns within bottom card
    f_cols = [
        ("Continuity & Fragmentation", "• Total Sleep Time, TIB, SE%\n• SOL, WASO, REM Latency\n• Awakening Index\n• Sleep Fragmentation Index"),
        ("Architecture & Dynamics", "• % N1, N2, N3, REM of TST\n• 1st vs 2nd half stage shifts\n• Bout duration statistics\n• 5x5 Markov Transition Matrix"),
        ("Spectral Power Dynamics", "• Welch Powers (δ, θ, α, σ, β)\n• Slow Wave Activity (SWA)\n• Spectral Entropy\n• Permutation Entropy"),
        ("Microstructure & Muscle", "• YASA Spindle Density (N2)\n• Slow Wave Amplitude & Dur\n• Submental EMG RMS\n• REM Muscle Atonia Ratio"),
    ]

    for i, (title, desc) in enumerate(f_cols):
        c_left = Inches(1.05 + i * 2.85)
        box = s5.shapes.add_textbox(c_left, Inches(4.65), Inches(2.7), Inches(1.95))
        btf = box.text_frame
        btf.word_wrap = True
        btf.margin_left = btf.margin_top = btf.margin_right = btf.margin_bottom = 0
        p = btf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p2 = btf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(11.5)
        p2.font.color.rgb = TEXT_MUTED
        p2.space_before = Pt(4)

    add_footer(s5, "Dual Perspective: Discrete 30s macro hypnogram + Continuous microstructural depth", "Output: 96 clinical parameters per night")
    add_notes(s5, "Target: 3:15 - 4:05 (50s)\nIn Tier 2, we transcend discrete 5-stage hypnograms. We implement the Sleep Depth Index Transformer from Zhou et al., published in npj Digital Medicine 2025. This computes a continuous 0.0 to 1.0 sleep depth score for every epoch, capturing micro-arousals and depth dynamics that discrete staging obscures. In tandem, our feature extraction engine computes ~96 clinical parameters per night: sleep continuity, 5x5 Markov transition matrices, spectral bandpowers, and microstructural events like YASA sleep spindle density and REM muscle atonia ratios.")

    # =========================================================================
    # SLIDE 6: Sleep Quality Index & Multi-Modal Scoring
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Sleep Quality Index & Multi-Modal Scoring", "CLINICAL INTELLIGENCE",
               "Synthesizing 96 physiological parameters, continuous depth, and patient perception", "4:05 – 4:55 | 50s")

    # Left Card: SleepLens Score
    add_card(s6, Inches(0.8), Inches(1.6), Inches(6.0), Inches(5.1))
    tb_sc = s6.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.5), Inches(4.7))
    tf_sc = tb_sc.text_frame
    tf_sc.word_wrap = True
    tf_sc.margin_left = tf_sc.margin_top = tf_sc.margin_right = tf_sc.margin_bottom = 0

    p = tf_sc.paragraphs[0]
    p.text = "🎯 SleepLens Unified Sleep Score (0–100)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    p = tf_sc.add_paragraph()
    p.text = "A transparent, non-black-box 100-point composite formula:"
    p.font.size = Pt(13)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(4)

    score_parts = [
        ("• Sleep Efficiency (SE%)", "Max 25 pts", "(TST / Time in Bed)"),
        ("• Continuous Sleep Depth", "Max 25 pts", "(Mean SDI slow-wave saturation)"),
        ("• Sleep Continuity", "Max 20 pts", "(Shift index & awakenings penalty)"),
        ("• Deep Sleep Share (N3%)", "Max 10 pts", "(Physical restoration)"),
        ("• REM Sleep Share (REM%)", "Max 10 pts", "(Cognitive restoration)"),
        ("• Sleep Onset Latency (SOL)", "Max 5 pts", "(<30 min target)"),
        ("• Fragmentation Resistance", "Max 5 pts", "(Shallow SDI <0.20 burden)"),
    ]

    for label, pts, note in score_parts:
        p = tf_sc.add_paragraph()
        p.text = f"{label}: {pts}  {note}"
        p.font.size = Pt(12)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(5)

    p = tf_sc.add_paragraph()
    p.text = "Clinical Grading:  ≥85: Excellent  |  70–84: Good  |  55–69: Fair  |  <55: Poor"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT
    p.space_before = Pt(10)

    # Right Card: PSQI & Synthesis
    add_card(s6, Inches(7.0), Inches(1.6), Inches(5.533), Inches(5.1))
    tb_ps = s6.shapes.add_textbox(Inches(7.25), Inches(1.8), Inches(5.033), Inches(4.7))
    tf_ps = tb_ps.text_frame
    tf_ps.word_wrap = True
    tf_ps.margin_left = tf_ps.margin_top = tf_ps.margin_right = tf_ps.margin_bottom = 0

    p = tf_ps.paragraphs[0]
    p.text = "🩺 Subjective-Objective Synthesis (PSQI)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    p = tf_ps.add_paragraph()
    p.text = "Standardized PSQI Integration (0–21 Global):"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(12)
    p = tf_ps.add_paragraph()
    p.text = "Includes all 7 clinical component domains (latency, duration, efficiency, disturbances, meds, daytime dysfunction). Directly compares patient perception against objective EEG signals."
    p.font.size = Pt(12.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    p = tf_ps.add_paragraph()
    p.text = "Sleep State Misperception Detection:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = AMBER_WARN
    p.space_before = Pt(14)
    p = tf_ps.add_paragraph()
    p.text = "Identifies paradoxical insomnia: high subjective distress (PSQI > 12) despite objectively normal sleep architecture (SE > 85%, deep N3 intact)."
    p.font.size = Pt(12.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    p = tf_ps.add_paragraph()
    p.text = "Automated Clinical Narrative Synthesis:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = EMERALD_GREEN
    p.space_before = Pt(14)
    p = tf_ps.add_paragraph()
    p.text = "LLM generator (gpt-6-luna) formats 96 metrics, continuous depth, and PSQI into structured clinical findings ready for physician sign-off."
    p.font.size = Pt(12.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(4)

    add_footer(s6, "Clinical Utility: Converts 96 engineering parameters into intuitive patient scoring", "Transparent, non-black-box composition")
    add_notes(s6, "Target: 4:05 - 4:55 (50s)\nTo synthesize these complex metrics into an actionable patient indicator, we designed the SleepLens Unified Sleep Score. Rather than an uninterpretable black-box score, it is a transparent 100-point scale: 25% sleep efficiency, 25% continuous depth, 20% continuity, and the remainder distributed across N3 deep sleep, REM, latency, and fragmentation. We also incorporate the standardized 7-component PSQI questionnaire. By contrasting subjective perception against objective PSG signals, SleepLens can flag paradoxical insomnia and feeds all metrics into an automated clinical reporting engine.")

    # =========================================================================
    # SLIDE 7: End-to-End System Architecture
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "End-to-End System Architecture & Data Flow", "SYSTEM DESIGN",
               "Scalable decoupled asynchronous processing pipeline from raw EDF to diagnostic report", "4:55 – 5:45 | 50s")

    # 4 Steps Horizontal
    step_boxes = [
        ("01 • UPLOAD & AUTH", "• Drag & drop EDF (≤500 MB)\n• Optional 7-part PSQI form\n• Patient metadata linkage\n• JWT httpOnly security", TEAL_PRIMARY, Inches(0.8)),
        ("02 • SIGNAL PIPELINE", "• Canonical 100 Hz resample\n• Lights-off windowing\n• Channel QC & alignment\n• Celery async worker queue", CYAN_ACCENT, Inches(3.8)),
        ("03 • DUAL AI ENGINES", "• Tier 1: 4-Model Ensemble\n  (Staging + Confidence)\n• Tier 2: SDI Transformer\n  (Continuous depth 0–1)", RGBColor(56, 189, 248), Inches(6.8)),
        ("04 • CLINICAL PLATFORM", "• SleepLens Score (0–100)\n• 96-parameter engine\n• Automated LLM report\n• OpenCode consultation chat", EMERALD_GREEN, Inches(9.8)),
    ]

    for title, desc, color, left_pos in step_boxes:
        add_card(s7, left_pos, Inches(1.6), Inches(2.733), Inches(3.1), border=color, border_width=2)
        tb = s7.shapes.add_textbox(left_pos + Inches(0.15), Inches(1.8), Inches(2.433), Inches(2.7))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(13.5)
        p.font.bold = True
        p.font.color.rgb = color
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12) # Larger font
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(8)

    # Technology Stack Box
    add_card(s7, Inches(0.8), Inches(4.9), Inches(11.733), Inches(1.85))
    tb_st = s7.shapes.add_textbox(Inches(1.05), Inches(5.05), Inches(11.233), Inches(1.55))
    tf_st = tb_st.text_frame
    tf_st.word_wrap = True
    tf_st.margin_left = tf_st.margin_top = tf_st.margin_right = tf_st.margin_bottom = 0
    p = tf_st.paragraphs[0]
    p.text = "Production Technology Stack & Data Contracts (Fully Containerized)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = TEXT_WHITE

    p = tf_st.add_paragraph()
    p.text = "• Frontend UI: Next.js 14 App Router, TypeScript, Tailwind CSS, Zustand, React Query.\n• Backend Core: Django REST Framework, PostgreSQL, Celery asynchronous workers, Redis broker.\n• Machine Learning: PyTorch, MNE-Python, LightGBM, YASA, SciPy signal processing.\n• Intelligence Layer: OpenAI API (gpt-6-luna) for diagnostic narrative; OpenCode local agent for consultation."
    p.font.size = Pt(12) # Larger font
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(6)

    add_footer(s7, "Decoupled architecture: ML workers never block web tier API requests", "Average end-to-end processing: < 35 seconds on 8-core CPU")
    add_notes(s7, "Target: 4:55 - 5:45 (50s)\nHere is our production system architecture. A clinician uploads an EDF file and optional PSQI through the Next.js web application. The Django REST backend sanitizes the upload and delegates heavy computation to Celery workers backed by Redis. Signals are canonically harmonized to 100 Hz, passed in parallel through both AI tiers—the 4-model staging ensemble and the SDI transformer—and combined with the 96-feature engine. Results are indexed in PostgreSQL and rendered back to the clinician with an LLM clinical report and an OpenCode consultation assistant.")

    # =========================================================================
    # SLIDE 8: Clinical Web Application Walkthrough
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Clinical Web Application (SleepLens UI/UX)", "THE PRODUCT",
               "Comprehensive diagnostic cockpit built specifically for sleep physicians and technologists", "5:45 – 6:30 | 45s")

    ui_features = [
        ("🎯 SleepLens ScoreCard & Core KPIs",
         "• Unified Score Gauge (0–100) with 7-part breakdown.\n• Core KPIs: Total Sleep Time (412.5 min), Sleep Efficiency (88.4%), SOL (14.0 min), WASO (38.5 min), REM Latency (78.0 min), Staging Confidence (91.2%).",
         TEAL_PRIMARY, Inches(0.8), Inches(1.6)),
        ("📊 Interactive Hypnogram & Confidence Bands",
         "• Synchronized 30-s stage timeline (Wake, REM, N1, N2, N3).\n• Confidence overlay: High (≥80%), Medium (≥60%), Low (<60%).\n• One-click review flags for borderline epochs requiring human check.",
         CYAN_ACCENT, Inches(6.85), Inches(1.6)),
        ("📈 SDI Sleep Depth Curve & Raw Signal Explorer",
         "• Continuous 0.0–1.0 Depth Waveform: Highlights cortical synchronization dips.\n• Signals Explorer: Zero-latency raw microvolt inspection for any 30-second epoch (Fpz-Cz, Pz-Oz, EOG, EMG).",
         RGBColor(56, 189, 248), Inches(0.8), Inches(4.25)),
        ("💬 Automated AI Report & Consultation Assistant",
         "• Clinical Narrative: LLM-generated report formatted in Markdown with clinician sign-off.\n• OpenCode Assistant: In-session interactive chat answering study-specific questions grounded in patient data.",
         EMERALD_GREEN, Inches(6.85), Inches(4.25)),
    ]

    for title, desc, col, left_x, top_y in ui_features:
        add_card(s8, left_x, top_y, Inches(5.68), Inches(2.45), border=col, border_width=2)
        tb = s8.shapes.add_textbox(left_x + Inches(0.2), top_y + Inches(0.18), Inches(5.28), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(15) # Larger font
        p.font.bold = True
        p.font.color.rgb = col
        p2 = tf.add_paragraph()
        p2.text = desc
        p2.font.size = Pt(12.5) # Larger font
        p2.font.color.rgb = TEXT_WHITE
        p2.space_before = Pt(8)

    add_footer(s8, "Responsive Next.js Frontend • Modern Slate & Teal Medical Theme", "Reduces clinician visual scoring time by >85%")
    add_notes(s8, "Target: 5:45 - 6:30 (45s)\nThis slide showcases the clinician interface. The dashboard presents the SleepLens Score and core KPIs at a glance. Below, the interactive hypnogram is coupled with real-time confidence tracking, highlighting exactly which epochs need human verification. Clinicians can view continuous sleep depth, open the raw signal viewer to inspect EEG microvolts for any 30-second epoch, review the AI-drafted diagnostic report, or ask questions in the OpenCode consultation chat. It reduces scoring overhead from 90 minutes down to a quick verification.")

    # =========================================================================
    # SLIDE 9: Deployment Performance & Roadmap
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "Deployment Performance & Future Roadmap", "CONCLUSION & IMPACT",
               "Real-world speed benchmarks, clinical impact, and wearable translation", "6:30 – 7:00 | 30s")

    # Left: Speed Benchmarks
    add_card(s9, Inches(0.8), Inches(1.6), Inches(5.65), Inches(5.1))
    tb_sp = s9.shapes.add_textbox(Inches(1.05), Inches(1.8), Inches(5.15), Inches(4.7))
    tf_sp = tb_sp.text_frame
    tf_sp.word_wrap = True
    tf_sp.margin_left = tf_sp.margin_top = tf_sp.margin_right = tf_sp.margin_bottom = 0

    p = tf_sp.paragraphs[0]
    p.text = "⚡ CPU Speed Benchmarks (8-Core CPU, No GPU)"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = TEAL_PRIMARY

    speed_rows = [
        ("• Single Epoch Inference:", "3.7–4.7 ms", "(×6,400 real-time)"),
        ("• Full 22-Hour Night PSG (2,650 ep):", "12.5 seconds", "(Ensemble)"),
        ("• Continuous SDI Depth Inference:", "8.2 seconds", "(Transformer)"),
        ("• 96-Parameter Extraction:", "9.8 seconds", "(Welch+YASA)"),
    ]

    for label, val, note in speed_rows:
        p = tf_sp.add_paragraph()
        p.text = f"{label} {val} {note}"
        p.font.size = Pt(13)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(8)

    # Highlight box for total turnaround
    p = tf_sp.add_paragraph()
    p.text = "★ Total Pipeline Turnaround: < 35 seconds per night!"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = EMERALD_GREEN
    p.space_before = Pt(16)

    p = tf_sp.add_paragraph()
    p.text = "Clinical Productivity Impact:\nReduces manual physician visual scoring time by >85% while delivering far deeper physiological insights and automated audit trails."
    p.font.size = Pt(12.5)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(10)

    # Right: Roadmap
    add_card(s9, Inches(6.85), Inches(1.6), Inches(5.68), Inches(5.1))
    tb_rd = s9.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.18), Inches(4.7))
    tf_rd = tb_rd.text_frame
    tf_rd.word_wrap = True
    tf_rd.margin_left = tf_rd.margin_top = tf_rd.margin_right = tf_rd.margin_bottom = 0

    p = tf_rd.paragraphs[0]
    p.text = "🚀 Translational Roadmap"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = CYAN_ACCENT

    roadmap = [
        ("1. Wearable Surrogate Translation", "Deploying our trained ResUNet and WatchSleepNet surrogate models for wrist-worn actigraphy and PPG without any EEG leads."),
        ("2. Formal Apnea & Movement Scoring", "Upgrading our proxy detectors to formal clinical AASM Apnea-Hypopnea Index (AHI) and Periodic Limb Movement Disorder (PLMD) scoring."),
        ("3. Multi-Center Clinical Trials", "Validation across large sleep cohorts (Sleep Heart Health Study) and neurological disorder groups (Parkinsonian REM sleep behavior disorder).")
    ]

    for title, desc in roadmap:
        p = tf_rd.add_paragraph()
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(14)
        p = tf_rd.add_paragraph()
        p.text = desc
        p.font.size = Pt(12.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    add_footer(s9, "SleepLens: Delivering Clinical Precision with Real-Time Efficiency", "Thank you! Questions & Discussion")
    add_notes(s9, "Target: 6:30 - 7:00 (30s)\nIn summary, SleepLens delivers state-of-the-art staging accuracy of 0.8425 F1 and 0.831 Kappa, with a complete turnaround time under 35 seconds on standard CPU hardware. By uniting discrete stage classification, continuous depth modeling, and automated clinical reporting, we cut physician scoring time by over 85% while providing unprecedented diagnostic depth. Our minimal two-sensor finding also enables accurate home wearable monitoring. SleepLens bridges machine learning with the daily realities of clinical sleep medicine. Thank you.")

    output_path = "SleepLens_Presentation.pptx"
    prs.save(output_path)
    print(f"Updated presentation saved successfully to {os.path.abspath(output_path)}")

if __name__ == "__main__":
    build_presentation()
