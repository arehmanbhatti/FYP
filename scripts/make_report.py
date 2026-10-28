"""Generates the Day 2 and Day 3 progress report as a PDF for the supervisor."""

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
    fontSize=13.5, textColor=ACCENT, spaceBefore=10, spaceAfter=5,
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
note_style = ParagraphStyle(
    "Note", parent=body, fontSize=9, textColor=MUTED, leading=13,
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
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t

doc = SimpleDocTemplate(
    "Day 2 and Day 3 Progress Report.pdf", pagesize=A4,
    topMargin=1.4 * cm, bottomMargin=1.3 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    title="Day 2 and Day 3 Progress Report",
)

story = []

story.append(Paragraph("Week One Progress Report", title_style))
story.append(Paragraph("AI Based Biodiversity Monitoring Using Video Analysis • Day 2 and Day 3", subtitle_style))

info = Table(
    [["Week goal", "Establish and evaluate the initial AI wildlife detection system"],
     ["Focus of these two days", "Species shortlist, dataset collection, and pretrained model evaluation"]],
    colWidths=[4.2 * cm, 11.3 * cm],
)
info.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
    ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("TEXTCOLOR", (0, 0), (0, -1), ACCENT),
    ("TEXTCOLOR", (1, 0), (1, -1), INK),
    ("BOX", (0, 0), (-1, -1), 0.6, LINE),
    ("INNERGRID", (0, 0), (-1, -1), 0.4, LINE),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
]))
story.append(info)

# ---------------- Day 2 ----------------
story.append(Paragraph("Day 2: Species Shortlist and Initial Dataset", h1))
story.append(Paragraph(
    "Wildlife species relevant to Sindh and Pakistan were surveyed on iNaturalist, using research "
    "grade, openly licensed photo records as a proxy for real world data availability.", body))
story.append(Spacer(1, 4))

story.append(Paragraph("Completed", h2))
story.extend(bullets([
    "Surveyed 11 candidate species and reviewed how many usable photos exist for each",
    "Shortlisted 8 target species, plus humans, based on data availability and project relevance",
    "Downloaded a working dataset of 480 photos in total, 60 per species, with full source attribution",
    "Ran a dataset quality check covering corrupt files, duplicates, and low resolution images",
]))

story.append(Paragraph("Dataset quality check result", h2))
story.append(Paragraph("Zero corrupt files, zero duplicates, only 5 of 480 images below 400 pixels.", result_style))
story.append(Spacer(1, 5))

story.append(Paragraph("Final target species", h2))
story.append(make_table(
    ["Species", "Closest class in the pretrained model", "Available reference photos"],
    [
        ["Leopard", "Leopard", "6,776"],
        ["Chinkara gazelle", "Antelope", "632"],
        ["Wild boar", "Pig", "35,197"],
        ["Striped hyena", "No matching class", "6,761"],
        ["Golden jackal", "Dog", "3,979"],
        ["Indian peafowl", "Bird", "24,213"],
        ["Nilgai", "Antelope", "2,367"],
        ["Mugger crocodile", "Crocodile", "2,779"],
        ["Human", "Person", "not applicable"],
    ],
    [4.7 * cm, 6.3 * cm, 4.5 * cm],
))
story.append(Spacer(1, 4))
story.append(Paragraph(
    "Two candidates were dropped for insufficient data: urial and Bengal fox. Sindh ibex was "
    "set aside because its species record is merged with domestic goat in the source data and "
    "would need a separate camera trap or curated source.", note_style))

# ---------------- Day 3 ----------------
story.append(Paragraph("Day 3: Pretrained Model Performance on the Dataset", h1))
story.append(Paragraph(
    "The pretrained detection model was run on all 480 dataset images, and separately on 14 short "
    "wildlife video clips, to measure how well it performs on the shortlisted species before any "
    "training decision is made.", body))
story.append(Spacer(1, 4))

story.append(Paragraph("Completed", h2))
story.extend(bullets([
    "Ran the pretrained model across the full image dataset and recorded every detection for later analysis",
    "Reviewed all images with no detection and identified the reason in each case",
    "Measured detection accuracy per species across a range of confidence thresholds",
    "Extended testing to 14 openly licensed video clips covering most target species",
]))

table_body = ParagraphStyle("TableBody", parent=body, fontSize=9, leading=11.5)
table_head = ParagraphStyle("TableHead", parent=table_body, textColor=colors.white, fontName="Helvetica-Bold")

def cell(text, head=False):
    return Paragraph(text, table_head if head else table_body)

story.append(Paragraph("Detection accuracy by species (confidence threshold 0.25)", h2))
story.append(make_table(
    [cell("Species", True), cell("Exact label match", True),
     cell("Exact or related match", True), cell("Assessment", True)],
    [
        [cell("Indian peafowl"), "95%", "95%", cell("Reliable as is")],
        [cell("Mugger crocodile"), "68%", "68%", cell("Usable, misses partly hidden animals")],
        [cell("Chinkara gazelle"), "38%", "96%", cell("Found, but often labelled Deer")],
        [cell("Nilgai"), "12%", "78%", cell("Found, but often labelled Deer")],
        [cell("Leopard"), "12%", "71%", cell("Found, but often labelled Cheetah")],
        [cell("Golden jackal"), "11%", "52%", cell("Weak, often labelled Fox")],
        [cell("Striped hyena"), "0%", "43%", cell("No matching class in the model")],
        [cell("Wild boar"), "20%", "20%", cell("Weak, frequently missed")],
    ],
    [3.2 * cm, 2.9 * cm, 3.5 * cm, 6.4 * cm],
))
story.append(Spacer(1, 5))

story.append(Paragraph("Key findings", h2))
story.extend(bullets([
    "The main issue is species confusion rather than missed animals: the model usually finds the "
    "animal but names a similar species, for example leopard as cheetah, or chinkara and nilgai as deer",
    "There is no matching class for striped hyena in the pretrained model at all",
    "A confidence threshold around 0.25 to 0.30 gives the best balance, raising it to 0.50 sharply "
    "reduces correct detections for most species",
    "Background objects such as plants and trees produce frequent false detections and will need "
    "to be filtered out",
    "About 11 percent of the collected images contain no live animal, such as tracks or remains, "
    "and should be excluded from any future training set",
])
)

story.append(Paragraph("Video testing", h2))
story.append(Paragraph(
    "The same species confusion patterns were confirmed on video. Two additional risks were found: "
    "a stork was briefly misread as a human, which matters because human detection drives the "
    "poaching alert feature, and detection quality drops sharply on night and low light footage, "
    "which is the setting the finished system must support.", body))

story.append(Spacer(1, 6))
story.append(Paragraph("Status against the Week One plan", h1))
story.append(Paragraph(
    "Days 1 to 3 are complete and verified. The pretrained model works, the target species and "
    "dataset are finalised, and its strengths and weaknesses are now documented with evidence.", body))
story.append(Spacer(1, 4))
story.append(Paragraph("Remaining for Days 4 to 7", h2))
story.extend(bullets([
    "Decide whether the pretrained model is sufficient or fine tuning is needed",
    "Prepare training data if fine tuning is chosen, or optimise detection settings if not",
    "Build the video detection pipeline using OpenCV",
    "Test the complete prototype and prepare the Week One demonstration",
]))

doc.build(story)
print("done")
