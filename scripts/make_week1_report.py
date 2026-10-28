"""Generates the Week 1 final report (Days 1-7) as a PDF for the supervisor."""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#2f5d50")
LINE = colors.HexColor("#d9dde1")
PALE = colors.HexColor("#f4f5f6")

styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    "TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=20, textColor=INK, spaceAfter=2, leading=24,
)
subtitle_style = ParagraphStyle(
    "SubtitleCustom", parent=styles["Normal"], fontName="Helvetica",
    fontSize=11, textColor=MUTED, spaceAfter=12,
)
h1 = ParagraphStyle(
    "H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
    fontSize=13.5, textColor=ACCENT, spaceBefore=10, spaceAfter=5, keepWithNext=1,
)
h2 = ParagraphStyle(
    "H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=11, textColor=INK, spaceBefore=7, spaceAfter=3,
)
body = ParagraphStyle(
    "Body", parent=styles["Normal"], fontName="Helvetica",
    fontSize=9.7, textColor=INK, leading=13.5,
)
bullet_style = ParagraphStyle(
    "Bullet", parent=body, leftIndent=12, firstLineIndent=-12, spaceAfter=3,
    bulletFontName="Helvetica", bulletIndent=0,
)
result_style = ParagraphStyle(
    "Result", parent=body, fontName="Helvetica-Bold", fontSize=9.5, textColor=ACCENT,
)

def bullets(items):
    flow = [Paragraph(f"•&nbsp;&nbsp;{t}", bullet_style) for t in items]
    flow.append(Spacer(1, 4))
    return flow

def make_table(header, rows, col_widths):
    data = [header] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t

doc = SimpleDocTemplate(
    "Week 1 Final Report.pdf", pagesize=A4,
    topMargin=1.4 * cm, bottomMargin=1.3 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    title="Week 1 Final Report",
)

story = []

story.append(Paragraph("Week One Final Report", title_style))
story.append(Paragraph("AI Based Biodiversity Monitoring Using Video Analysis • Days 1 to 7", subtitle_style))

info = Table(
    [["Week goal", "Establish and evaluate the initial AI wildlife detection system"],
     ["Base paper", Paragraph("Velpula et al. 2026, Multimodal Deep Learning Based Wildlife Intrusion "
                              "Perception Using YOLOv12 and YAMNet", body)],
     ["Week 1 scope", "Visual branch (YOLO) and output layer (alerts, CSV log) of the base paper"]],
    colWidths=[3.4 * cm, 12.1 * cm],
)
info.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.3),
    ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
    ("TEXTCOLOR", (1, 0), (1, -1), INK),
    ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
]))
story.append(info)

# ---------------- Summary ----------------
story.append(Paragraph("Week Summary", h1))
story.append(make_table(
    ["Day", "Work", "Outcome"],
    [
        ["1", "Environment setup, first detection test", "YOLO working; OIV7 model chosen over COCO"],
        ["2", "Species shortlist, initial dataset", "8 target species + human, 480 photos"],
        ["3", "Pretrained model evaluation", "Exact species name for only 41% of images"],
        ["4", "Pretrained or fine-tune?", "Decision: fine-tune"],
        ["5", "Training dataset, fine-tuning, threshold", "mAP@50 0.700, conf 0.25 chosen"],
        ["6", "Video detection pipeline", "Species + person detection, alerts, CSV log"],
        ["7", "Prototype vs pretrained on test videos", "Big gains on leopard, hyena, jackal"],
    ],
    [1.2 * cm, 6.6 * cm, 7.7 * cm],
))

# ---------------- Days 1-3 ----------------
story.append(Paragraph("Days 1 to 3: Setup, Dataset and Pretrained Baseline", h1))
story.extend(bullets([
    "Environment set up with Python, Ultralytics YOLO and OpenCV. The COCO model only knows 80 generic "
    "classes, so the Open Images V7 model (601 classes) was used as the pretrained baseline.",
    "Target species: leopard, chinkara, wild boar, striped hyena, golden jackal, Indian peafowl, nilgai "
    "and mugger crocodile, plus humans for intrusion alerts. Photos were collected worldwide since "
    "Pakistan-only photos are scarce.",
    "The pretrained model named the exact species for only 41% of images. It has no hyena class and "
    "confuses leopard with cheetah and nilgai or chinkara with deer. Full details are in the Day 2 and "
    "Day 3 progress report.",
]))

# ---------------- Day 4-5 ----------------
story.append(Paragraph("Day 4 and 5: Fine-tuning", h1))
story.append(Paragraph(
    "Threshold tuning cannot fix a wrong class name, so the model was fine-tuned on our 8 species. "
    "The training set (319 images, 256 train / 63 val) uses pseudo-labels: the pretrained model's boxes "
    "renamed to our species. YOLO11n was trained at the base paper's settings (320x320, batch 16, "
    "100 epochs).", body))
story.append(Spacer(1, 5))
story.append(Paragraph("Validation result: mAP@50 = 0.700, mAP@50-95 = 0.506, conf = 0.25 "
                       "(precision 0.67, recall 0.61).", result_style))
story.append(Spacer(1, 5))
story.append(make_table(
    ["Species", "Precision", "Recall", "Exact hit, pretrained", "Exact hit, fine-tuned"],
    [
        ["Leopard", "0.67", "0.67", "12%", "88%"],
        ["Chinkara", "0.78", "0.54", "30%", "70%"],
        ["Wild boar", "0.50", "0.40", "50%", "50%"],
        ["Striped hyena", "0.43", "0.38", "0%", "57%"],
        ["Golden jackal", "1.00", "0.83", "17%", "83%"],
        ["Indian peafowl", "0.64", "0.64", "100%", "73%"],
        ["Nilgai", "0.64", "0.54", "10%", "70%"],
        ["Mugger", "0.70", "0.88", "100%", "100%"],
        ["All", "0.67", "0.61", "41%", "75%"],
    ],
    [3.5 * cm, 2.2 * cm, 2.2 * cm, 3.8 * cm, 3.8 * cm],
))
story.append(Spacer(1, 4))
story.extend(bullets([
    "Fine-tuning fixed the naming problem: exact-species hits went from 41% to 75%.",
    "Peafowl got worse (100% to 73%) and wild boar is the weakest class (only 14 training images).",
    "These numbers are optimistic: validation boxes are pseudo-labels, not hand-drawn, and the "
    "validation set is tiny (4 to 11 images per species).",
]))

# ---------------- Day 6 ----------------
story.append(Paragraph("Day 6: Video Detection Pipeline", h1))
story.extend(bullets([
    "OpenCV reads a video file or webcam. Each processed frame goes through the fine-tuned species model "
    "and the COCO person model for human intrusion.",
    "Output: annotated video, a CSV log of every detection, and an alerts CSV (WILDLIFE or HUMAN INTRUSION, "
    "one alert per label per 10 seconds).",
    "Problem found: the species model labelled hikers as nilgai or peafowl (confidence up to 0.97), "
    "since it never saw people. Fixed with an overlap rule between person and species boxes: nilgai "
    "false alarms on the hiking clip went from 57 to 0.",
]))

# ---------------- Day 7 ----------------
story.append(Paragraph("Day 7: Prototype vs Pretrained on Test Videos", h1))
story.append(Paragraph(
    "14 test clips, one frame every 0.5 s, conf 0.25. Each cell: frames with the correct label / "
    "frames with a wrong species label / frames with a false person.", body))
story.append(Spacer(1, 5))
story.append(make_table(
    ["Clip", "Expected", "Pretrained", "Prototype"],
    [
        ["leopard_india", "leopard", "0 / 31 / 0", "28 / 0 / 1"],
        ["leopard_tree", "leopard", "0 / 2 / 0", "9 / 0 / 0"],
        ["hyena_spotted", "striped hyena", "0 / 7 / 0", "7 / 0 / 0"],
        ["jackals", "golden jackal", "19 / 45 / 0", "38 / 35 / 0"],
        ["peafowl_walking", "Indian peafowl", "30 / 0 / 0", "30 / 0 / 0"],
        ["human_hiking", "person", "48 / 3 / 0", "45 / 8 / 0"],
        ["gazelle_hluhluwe", "chinkara", "46 / 39 / 0", "11 / 42 / 1"],
        ["peafowl_running", "Indian peafowl", "6 / 1 / 0", "0 / 44 / 0"],
        ["nilgai_zoo", "nilgai", "0 / 20 / 0", "0 / 26 / 9"],
        ["crocodile_nile", "mugger", "0 / 3 / 7", "0 / 0 / 9"],
        ["boar_berlin", "wild boar", "0 / 0 / 0", "0 / 0 / 0"],
        ["boar_bulgaria", "wild boar", "0 / 6 / 0", "0 / 0 / 1"],
        ["camtrap_general", "none", "0 / 20 / 0", "0 / 20 / 0"],
        ["camtrap_jaguarundi", "none", "0 / 6 / 0", "0 / 10 / 0"],
    ],
    [4.3 * cm, 3.6 * cm, 3.8 * cm, 3.8 * cm],
))
story.append(Spacer(1, 4))
story.extend(bullets([
    "Clear wins on species the pretrained model could not name: leopard, hyena and jackal.",
    "Regressions: the gazelle clip (46 to 11 correct) and peafowl_running, where a chital herd is "
    "called nilgai and wild boar. Nilgai in the zoo clip is labelled wild boar.",
    "Wild boar is still not detected in night and dusk footage. No night or IR images were used in training.",
    "There is no unknown-animal handling: non-target animals in camera-trap clips are forced into one "
    "of the 8 classes. The COCO person model also fires on some animals (stork, nilgai).",
]))

# ---------------- Limitations / next ----------------
story.append(Paragraph("Limitations and Next Steps", h1))
story.extend(bullets([
    "More data: 200 to 300 images per species with boxes reviewed in Roboflow, including night/IR images, "
    "and people and empty scenes as negative examples.",
    "Retrain on Google Colab, and also train YOLOv12 to match the base paper exactly.",
    "Week 2: YAMNet audio branch and the fusion layer from the base paper, then measure how much fusion "
    "improves detection (the paper gives no numbers for this).",
]))

doc.build(story)
print("Wrote Week 1 Final Report.pdf")
