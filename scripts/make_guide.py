"""FYP complete explanation guide (Roman Urdu) - for the student's own study."""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2])

INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#6b7280")
ACCENT = colors.HexColor("#2f5d50")
LINE = colors.HexColor("#d9dde1")
PALE = colors.HexColor("#f4f5f6")
NOTE_BG = colors.HexColor("#eef5f2")
WARN_BG = colors.HexColor("#fdf6e7")
WARN_LINE = colors.HexColor("#e0c27a")

ss = getSampleStyleSheet()
title = ParagraphStyle("T", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=24, leading=29, textColor=INK)
subtitle = ParagraphStyle("ST", parent=ss["Normal"], fontName="Helvetica", fontSize=12, leading=16,
                          textColor=MUTED, alignment=TA_CENTER)
h1 = ParagraphStyle("H1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=16, leading=20,
                    textColor=ACCENT, spaceBefore=6, spaceAfter=8, keepWithNext=1)
h2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12, leading=15,
                    textColor=INK, spaceBefore=9, spaceAfter=4, keepWithNext=1)
body = ParagraphStyle("B", parent=ss["Normal"], fontName="Helvetica", fontSize=10, leading=14.5,
                      textColor=INK, spaceAfter=5)
small = ParagraphStyle("S", parent=body, fontSize=8.6, leading=11.5, textColor=MUTED)
bul = ParagraphStyle("BL", parent=body, leftIndent=14, firstLineIndent=-10, spaceAfter=3)
cell = ParagraphStyle("C", parent=body, fontSize=8.8, leading=11.5, spaceAfter=0)
cellh = ParagraphStyle("CH", parent=cell, fontName="Helvetica-Bold", textColor=colors.white)
q_style = ParagraphStyle("Q", parent=body, fontName="Helvetica-Bold", textColor=ACCENT, spaceBefore=6, spaceAfter=2,
                         keepWithNext=1)
code = ParagraphStyle("CODE", parent=body, fontName="Courier", fontSize=8.8, leading=12, textColor=INK)

W = A4[0] - 4 * cm  # usable width


def P(t, s=body):
    return Paragraph(t, s)


def bullets(items):
    return [Paragraph(f"&bull;&nbsp; {t}", bul) for t in items] + [Spacer(1, 3)]


def table(header, rows, widths):
    data = [[Paragraph(h, cellh) for h in header]] + [[Paragraph(str(c), cell) for c in r] for r in rows]
    t = Table(data, colWidths=[w * W for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [t, Spacer(1, 8)]


def box(content, bg=NOTE_BG, line=ACCENT, label=None):
    inner = []
    if label:
        inner.append(Paragraph(f"<b>{label}</b>", ParagraphStyle("BL2", parent=body, textColor=line
                                                                    if line != WARN_LINE else colors.HexColor("#8a6414"))))
    inner += [Paragraph(c, body) if isinstance(c, str) else c for c in content]
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, line),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return [t, Spacer(1, 8)]


def img(rel, width_frac, caption):
    p = ROOT / rel
    from PIL import Image as PI
    w, h = PI.open(p).size
    iw = W * width_frac
    return [KeepTogether([Image(str(p), width=iw, height=iw * h / w), Spacer(1, 3), P(caption, small)]),
            Spacer(1, 8)]


def flow_diagram(steps):
    """Horizontal pipeline of boxes with arrows."""
    cells, widths = [], []
    n = len(steps)
    bw = (W - (n - 1) * 0.6 * cm) / n
    for i, (head, sub) in enumerate(steps):
        cells.append([Paragraph(f"<b>{head}</b>", ParagraphStyle("fx", parent=cell, alignment=TA_CENTER,
                                                                 textColor=colors.white)),
                      Paragraph(sub, ParagraphStyle("fs", parent=cell, alignment=TA_CENTER,
                                                    textColor=colors.HexColor("#e6efe9"), fontSize=7.8, leading=10))])
        widths.append(bw)
        if i < n - 1:
            cells.append(Paragraph("&rarr;", ParagraphStyle("ar", parent=body, alignment=TA_CENTER, fontSize=14)))
            widths.append(0.6 * cm)
    t = Table([cells], colWidths=widths)
    style = [("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 3),
             ("RIGHTPADDING", (0, 0), (-1, -1), 3), ("TOPPADDING", (0, 0), (-1, -1), 6),
             ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]
    for i in range(0, len(cells), 2):
        style.append(("BACKGROUND", (i, 0), (i, 0), ACCENT))
    t.setStyle(TableStyle(style))
    return [t, Spacer(1, 10)]


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, 1.2 * cm, "FYP Complete Guide - AI Based Biodiversity Monitoring Using Video Analysis")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
    canvas.restoreState()


s = []

# ---------------- Cover ----------------
s += [Spacer(1, 3 * cm), P("FYP Complete Guide", title), Spacer(1, 6),
      P("AI Based Biodiversity Monitoring Using Video Analysis", subtitle), Spacer(1, 4),
      P("Start se end tak: konsa model, kyun, kese implement hua, dataset aur results", subtitle),
      Spacer(1, 1.2 * cm)]
s += table(["Is guide me kya hai", "Section"], [
    ["Project ka maqsad aur base paper", "1"],
    ["Zaroori concepts (YOLO, box, confidence, mAP, precision/recall...)", "2"],
    ["Konsa model kahan aur kyun use hua", "3"],
    ["Dataset - poori detail (supervisor ka favourite topic)", "4"],
    ["Day by day implementation (Day 1 se Day 7)", "5"],
    ["Results aur unka matlab", "6"],
    ["Kamzoriyan (limitations) - honestly", "7"],
    ["Week 1 fixes (v2) - results", "8"],
    ["Supervisor ke sawal aur jawab", "9"],
    ["Glossary + kaunsi file kya karti hai", "10"],
], [0.85, 0.15])
s += box(["Ye guide Week 1 ke <b>actual</b> kaam aur numbers par based hai (README, Week 1 Final Report, "
          "aur <font face='Courier'>data/results/</font> ki files). Jahan kaam abhi complete nahi hua, wahan "
          "saaf likha hai."], label="Note")
s.append(PageBreak())

# ---------------- 1. Goal ----------------
s.append(P("1. Project ka maqsad (The Goal)", h1))
s.append(P("Simple words me: <b>jungle / wildlife area me camera lagao, video aaye, aur AI khud bataye ke "
           "video me kaunsa janwar hai, aur agar koi insaan (poacher / intruder) aaye to alert de.</b> "
           "Har detection ek CSV log me save ho, taake baad me dashboard par dekha ja sake."))
s.append(P("Hamare target 8 janwar Sindh / Pakistan ke hain (Kirthar, Thar, Indus belt) + insaan:"))
s += table(["#", "Species", "Scientific name", "Kyun chuna"], [
    ["1", "Leopard", "Panthera pardus", "Endangered, poaching target"],
    ["2", "Chinkara gazelle", "Gazella bennettii", "Thar / Kirthar ka khaas hiran"],
    ["3", "Wild boar", "Sus scrofa", "Crop damage, bohot common"],
    ["4", "Striped hyena", "Hyaena hyaena", "Sindh me milta hai, pretrained model me class hi nahi"],
    ["5", "Golden jackal", "Canis aureus", "Common predator"],
    ["6", "Indian peafowl", "Pavo cristatus", "Thar ka mor, bird ka example"],
    ["7", "Nilgai", "Boselaphus tragocamelus", "Bara antelope"],
    ["8", "Mugger crocodile", "Crocodylus palustris", "Reptile ka example, Indus / lakes"],
    ["+", "Human", "-", "Poaching / intrusion alert ke liye"],
], [0.05, 0.22, 0.3, 0.43])

s.append(P("Base paper", h2))
s.append(P("Hum <b>Velpula et al. 2026</b>, <i>\"Multimodal Deep Learning Based Wildlife Intrusion Perception "
           "Using YOLOv12 and YAMNet\"</i> (<font face='Courier'>paper3.pdf</font>) follow kar rahe hain. "
           "Is paper ka system 4 layers ka hai:"))
s += flow_diagram([("Input layer", "Camera / video file<br/>(+ microphone)"),
                   ("Processing", "YOLO = video<br/>YAMNet = audio"),
                   ("Fusion layer", "Dono ko mila kar<br/>final faisla"),
                   ("Output layer", "Boxes, alerts,<br/>CSV log")])
s += table(["Layer", "Week 1 me status"], [
    ["Input (OpenCV video / webcam)", "<b>Done</b>"],
    ["Processing - YOLO visual branch", "<b>Done</b> (fine-tuned model + person model)"],
    ["Processing - YAMNet audio branch", "Baad me (Week 2 ke baad)"],
    ["Fusion layer", "Baad me (audio ke baad hi possible)"],
    ["Output (annotated video, detections CSV, alerts CSV)", "<b>Done</b>"],
], [0.55, 0.45])
s.append(P("Training settings bhi paper se li hain: <b>image size 320x320, batch 16, 100 epochs</b>. "
           "Paper YOLOv12 use karta hai; hamari proposal me YOLOv11 likha tha, isliye pehle YOLO11n train kiya. "
           "YOLOv12 wala run bhi plan me hai (Section 8)."))
s.append(PageBreak())

# ---------------- 2. Concepts ----------------
s.append(P("2. Zaroori concepts - pehle ye samajh lo", h1))
s.append(P("Object detection kya hai?", h2))
s.append(P("<b>Classification</b> sirf batata hai \"is photo me leopard hai\". <b>Object detection</b> batata hai "
           "\"leopard <u>yahan</u> hai\" - yani ek <b>bounding box</b> (rectangle) + <b>class</b> (naam) + "
           "<b>confidence</b> (kitna yakeen, 0 se 1). Video monitoring ke liye detection chahiye, kyunke ek frame "
           "me kai janwar / insaan ho sakte hain."))
s.append(P("YOLO kya hai?", h2))
s.append(P("<b>YOLO = You Only Look Once.</b> Ye ek deep learning (CNN) model hai jo poori image ko ek hi baar "
           "dekh kar saare boxes aur classes ek saath predict karta hai - isliye bohot fast hai aur real-time "
           "video ke liye best hai. Hum <b>Ultralytics</b> library use karte hain (Python), jis me YOLOv8, "
           "YOLO11, YOLO12 sab available hain."))
s += bullets([
    "<b>n / s / m</b> = model size (nano / small / medium). Nano sab se chhota aur fast, medium zyada accurate magar slow.",
    "<b>.pt file</b> = model ke weights (jo cheez model ne seekhi hai).",
    "<b>Pretrained</b> = kisi bare dataset par pehle se train hua model. Hum shuru se train nahi karte.",
])
s.append(P("Pretrained datasets: COCO vs Open Images V7", h2))
s += table(["Dataset", "Classes", "Wildlife ke liye?"], [
    ["COCO", "80 generic (person, dog, cat, bird, horse, giraffe...)", "Deer / leopard / hyena class hi nahi"],
    ["Open Images V7 (OIV7)", "601 (deer, leopard, cheetah, fox, antelope, crocodile...)", "Behtar, magar hamari exact species nahi"],
], [0.25, 0.45, 0.3])
s.append(P("Transfer learning / Fine-tuning", h2))
s.append(P("Pretrained model pehle se edges, textures, shapes, \"janwar jaisa\" pattern pehchanta hai. "
           "<b>Fine-tuning</b> me hum us model ko apni thodi si data (sirf ~300 images) par dobara train karte hain "
           "taake wo hamari 8 classes ke naam seekh le. Shuru se train karne ke liye lakhon images chahiye hoti; "
           "fine-tuning me kam data kaafi hota hai. Isi ko transfer learning kehte hain."))
s.append(P("Training ke terms", h2))
s += table(["Term", "Matlab"], [
    ["Epoch", "Poora training set ek dafa model ko dikhana. 100 epochs = 100 dafa."],
    ["Batch size (16)", "Ek step me 16 images ek saath process hoti hain, phir weights update hote hain."],
    ["Image size (320)", "Har image 320x320 pixel par resize hoti hai. Chhota size = fast, magar chhote janwar mushkil."],
    ["Train / Val split", "Train images se model seekhta hai. Val images model ne kabhi nahi dekhi - in par test karte hain."],
    ["Overfitting", "Model training images ratta laga le, nayi images par fail. Kam data me bara risk."],
    ["Label", "Har image ke saath ek .txt file: kaunsi class, box kahan hai."],
], [0.22, 0.78])
s.append(P("Results ke metrics (sab se zaroori)", h2))
s += table(["Metric", "Simple matlab", "Example"], [
    ["Confidence threshold (conf)", "Is se kam confidence wale boxes ignore. Kam threshold = zyada detections (+ zyada galat).",
     "conf 0.40 = 40% se kam yakeen wale box hata do"],
    ["IoU", "Predicted box aur sahi box kitna overlap karte hain (0-1). IoU >= 0.5 = sahi jagah.", "Box aadha bhi galat jagah ho to miss"],
    ["Precision", "Jo model ne bola, us me se kitna sahi tha. (False alarm kam = precision zyada)",
     "10 boxes diye, 8 sahi = 0.80"],
    ["Recall", "Jo asal me tha, us me se kitna model ne pakra. (Miss kam = recall zyada)",
     "10 janwar the, 6 pakre = 0.60"],
    ["F1", "Precision aur recall ka balance (harmonic mean).", "P 0.77, R 0.61 -> F1 0.68"],
    ["mAP@50", "Har class ki average precision (har threshold par), IoU 0.5 par, phir saari classes ka average. "
               "Detection ka standard score.", "0.707 = 70.7%"],
    ["mAP@50-95", "Wahi, magar IoU 0.50 se 0.95 tak average - box ka bilkul exact hona bhi zaroori. Hamesha kam aata hai.",
     "0.546"],
    ["Confusion matrix", "Table jo batata hai kaunsi class kis class ke saath confuse hui.", "boar -> peafowl"],
    ["Exact hit rate (hamara apna)", "Kitni images me kam az kam ek box sahi species naam ke saath aaya.", "41% -> 76%"],
], [0.22, 0.5, 0.28])
s.append(PageBreak())

# ---------------- 3. Models ----------------
s.append(P("3. Konsa model kahan aur kyun use hua", h1))
s.append(P("Project me 4 models ka role hai (5wa plan me hai). Ye table yaad kar lo - supervisor zaroor poochega:"))
s += table(["Model", "Pretrained on", "Kahan use hua", "Kyun"], [
    ["<b>yolo11n.pt</b> (COCO)", "COCO, 80 classes", "Day 1 test; Day 6 pipeline me <b>person detector</b>",
     "Insaan detect karne me bohot acha hai. Species model ke paas 'person' class nahi."],
    ["<b>yolov8m-oiv7.pt</b>", "Open Images V7, 601 classes", "Day 1-3 <b>baseline</b>; Day 5 <b>pseudo-labels</b> banane ke liye",
     "Leopard, deer, antelope, crocodile jaise classes isme pehle se hain."],
    ["<b>species_v1</b> (YOLO11n fine-tuned)", "yolo11n se shuru, hamari 319 images", "Day 5-7 - <b>hamara main model</b>",
     "Sirf yehi hamari 8 species ke exact naam deta hai."],
    ["yolov8s-worldv2 (YOLO-World)", "Open-vocabulary (text prompt)", "v2 pipeline (in progress): <b>unknown_animal</b>",
     "Jo janwar 8 me se nahi (elk, jaguarundi), use zabardasti 8 me na daale."],
    ["YOLO12n", "COCO", "Plan: base paper se exact match ke liye", "Paper YOLOv12 use karta hai."],
], [0.22, 0.2, 0.3, 0.28])
s.append(P("YOLO11n hi kyun (nano)?", h2))
s += bullets([
    "Proposal me <b>YOLOv11</b> likha tha; Ultralytics ka latest stable version.",
    "Dataset chhota hai (319 images) - chhota model kam overfit karta hai.",
    "Nano model fast hai: GTX 1660 Super par ~15 min me 100 epochs, aur field device (edge / Raspberry Pi / laptop) par real-time chal sakta hai.",
    "320x320 input base paper ki setting hai, is se bhi speed milti hai.",
])
s.append(P("Pipeline me 2 models saath kyun?", h2))
s.append(P("Hamara species model sirf janwaron par train hua, us ke paas \"person\" class nahi. Poaching alert ke liye "
           "insaan detect karna zaroori hai, aur COCO model (yolo11n) insaan pehchanne me pehle se bohot strong hai. "
           "Isliye har frame par dono chalte hain, aur ek <b>overlap rule</b> faisla karta hai (Day 6 dekho)."))
s.append(P("Poora system ek nazar me", h2))
s += flow_diagram([("Video / webcam", "OpenCV frame<br/>parhta hai"),
                   ("Species model", "species_v1<br/>8 janwar"),
                   ("Person model", "yolo11n COCO<br/>sirf 'person'"),
                   ("Overlap rule", "Ek hi cheez par<br/>2 box? ek hatao"),
                   ("Output", "Video + CSV<br/>+ alerts")])
s.append(PageBreak())

# ---------------- 4. Dataset ----------------
s.append(P("4. Dataset - poori detail", h1))
s += box(["Supervisor dataset par sab se zyada sawal karte hain. Is section ke 5 points yaad rakho: "
          "<b>(1) source kya hai, (2) kitni images, (3) labels kese bane, (4) split kese hua, (5) kamzoriyan kya hain.</b>"],
         label="Yaad rakhne wali baat")
s.append(P("4.1 Source: iNaturalist", h2))
s.append(P("<b>iNaturalist</b> ek citizen-science website hai jahan log janwaron ki photos upload karte hain aur "
           "community species identify karti hai. Hum ne sirf <b>\"research grade\"</b> observations li (jin par "
           "community ki ID agree karti hai) aur sirf open licence wali photos:"))
s += table(["Licence", "Images", "Matlab"], [
    ["CC BY-NC", "407", "Credit do, commercial use nahi (FYP academic hai, theek hai)"],
    ["CC BY", "64", "Credit de kar koi bhi use"],
    ["CC0", "9", "Public domain"],
    ["<b>Total</b>", "<b>480</b>", "Har photo ka credit <font face='Courier'>data/dataset/attribution.csv</font> me"],
], [0.2, 0.15, 0.65])
s.append(P("<b>Kyun iNaturalist?</b> Free, legal licence, species ka naam already verified, aur API se automatic "
           "download ho jata hai (<font face='Courier'>scripts/inat_survey.py</font>, "
           "<font face='Courier'>download_dataset.py</font>)."))

s.append(P("4.2 Species kese shortlist hui (Day 2)", h2))
s.append(P("11 candidate species ka survey kiya: duniya bhar me aur Pakistan me kitni photos hain "
           "(<font face='Courier'>data/dataset_survey.json</font>)."))
s += table(["Species", "Photos (world / Pakistan)", "Faisla"], [
    ["Leopard", "6776 / 31", "Rakha"], ["Chinkara", "632 / 11", "Rakha"], ["Wild boar", "35197 / 19", "Rakha"],
    ["Striped hyena", "509 / 3 (pehle galti se 6761 / 0)", "Rakha"], ["Golden jackal", "3979 / 36", "Rakha"],
    ["Indian peafowl", "24213 / 12", "Rakha"], ["Nilgai", "2367 / 4", "Rakha"], ["Mugger", "2779 / 5", "Rakha"],
    ["Urial", "121 worldwide", "<b>Drop</b> - bohot kam photos"],
    ["Bengal fox", "256 / 1", "<b>Drop</b> - bohot kam photos"],
    ["Sindh ibex", "-", "<b>Drop</b> - iNaturalist me domestic goat ke saath merged, count bekaar"],
], [0.3, 0.35, 0.35])
s.append(P("<b>Pakistan ki photos kam kyun?</b> Pakistan me bohot kam log iNaturalist use karte hain (striped hyena ki sirf 3 photos!). "
           "Isliye <b>worldwide photos</b> li. Janwar wahi hai, sirf background (habitat) different hai."))

s.append(P("4.3 Kitni images, quality check", h2))
s += bullets([
    "<b>60 photos per species x 8 = 480 photos</b> (Day 2).",
    "Quality check (<font face='Courier'>check_dataset.py</font>): <b>0 corrupt, 0 duplicate</b>, sirf 5 images 400 px se chhoti. Median size takreeban 1024x683.",
    "<b>Problem mila (Day 3):</b> 55 of 480 (11%) photos me zinda janwar tha hi nahi - paon ke nishaan, potty (scat), "
    "khopri, laash, sirf landscape. iNaturalist 'research grade' in ko allow karta hai (evidence of presence). "
    "Wild boar sab se bura: 60 me se 20. Ye images training se nikal di gayi.",
    "Kuch label galtiyan bhi mili: ek 'nilgai' gaye jaisa.",
])
s += box(["<b>Sab se bari galti jo baad me pakri gayi (16 Nov):</b> Day 2 me striped hyena ke liye iNaturalist ka "
          "taxon <font face='Courier'>41886</font> use hua tha. Woh asal me <b>Crocuta crocuta (spotted hyena)</b> hai, "
          "striped hyena (<i>Hyaena hyaena</i>, taxon <font face='Courier'>41888</font>) nahi. Yaani Week 1 ki <b>saari 60 "
          "'striped hyena' photos spotted hyena thi</b>. Isliye v1 ke hyena wale saare results (Day 3, Day 5, Day 7) "
          "asal me <b>spotted hyena</b> ke results hain.",
          "Wajah: survey script naam ko loosely match karti thi, aur pehla result utha leti thi. Ab exact naam match zaroori hai.",
          "Fix (v2): 300 asli <i>Hyaena hyaena</i> photos download hui (API se verify), purani 60 ab "
          "<font face='Courier'>data/negatives/crocuta_crocuta</font> me spotted-hyena negatives hain. Asli count: "
          "<b>509 worldwide, sirf 3 Pakistan</b>.",
          "Supervisor ko khud bata do: galti pakarna aur theek karna achi research practice hai."],
         bg=WARN_BG, line=WARN_LINE, label="Correction: striped hyena")

s.append(P("4.4 Labels kese bane - Pseudo-labelling (sab se important)", h2))
s.append(P("iNaturalist sirf batata hai \"is photo me leopard hai\" (<b>whole-image label</b>). YOLO ko train karne ke "
           "liye <b>bounding box</b> chahiye. 480 images par haath se box banana time leta, isliye "
           "<b>pseudo-labelling</b> kiya:"))
s += bullets([
    "<b>Step 1:</b> Pretrained OIV7 model ko har photo par chalaya (Day 3). Wo janwar dhoond leta hai magar naam galat deta hai (e.g. leopard ko 'Cheetah').",
    "<b>Step 2:</b> Box ko rakha agar uski class species ki apni ya <b>related</b> class ho (leopard ke liye Leopard/Cheetah/Jaguar/Tiger/Lion/Cat, "
    "chinkara ke liye Antelope/Deer/Goat/Sheep...) ya generic 'Animal/Mammal', aur conf >= 0.25.",
    "<b>Step 3:</b> Box ka naam badal kar hamari species rakh diya. Photo ka folder pehle se sahi naam batata hai, "
    "isliye 'Cheetah' box leopard photo par = <b>leopard</b> box.",
    "<b>Step 4:</b> Jin photos me zinda janwar nahi (Day 3 review) ya koi box nahi mila - wo drop.",
])
s.append(P("Iska fayda: model ka <b>box (jagah)</b> acha hota hai, sirf <b>naam</b> galat - aur naam hum folder se jaante hain. "
           "Code: <font face='Courier'>scripts/build_yolo_dataset.py</font>."))
s.append(P("YOLO label format", h2))
s.append(P("Har image ke saath ek .txt file, har line ek box:"))
s += box([Paragraph("class_id&nbsp; x_center&nbsp; y_center&nbsp; width&nbsp; height<br/>"
                    "0&nbsp; 0.512300&nbsp; 0.481200&nbsp; 0.402100&nbsp; 0.553000", code),
          "Saari values image ke size se divide (0-1, <b>normalized</b>). class 0 = leopard, 1 = chinkara, 2 = wild_boar, "
          "3 = striped_hyena, 4 = golden_jackal, 5 = indian_peafowl, 6 = nilgai, 7 = mugger. "
          "Ye mapping <font face='Courier'>data/yolo_dataset/data.yaml</font> me hai."], bg=PALE, line=MUTED)

s.append(P("4.5 Final training dataset aur split", h2))
s.append(P("Har species ki images ko <b>80% train / 20% val</b> me baanta, <b>fixed seed 42</b> (taake har dafa same split aaye, "
           "result reproducible ho). Split har species ke andar alag hua (stratified), taake val me har species ho."))
s += table(["Species", "Photos", "Usable (box mila)", "Train", "Val"], [
    ["Leopard", "60", "40", "32", "8"], ["Chinkara", "60", "52", "42", "10"],
    ["Wild boar", "60", "<b>18</b>", "<b>14</b>", "<b>4</b>"], ["Striped hyena", "60", "37", "30", "7"],
    ["Golden jackal", "60", "31", "25", "6"], ["Indian peafowl", "60", "54", "43", "11"],
    ["Nilgai", "60", "51", "41", "10"], ["Mugger", "60", "36", "29", "7"],
    ["<b>Total</b>", "<b>480</b>", "<b>319</b>", "<b>256</b>", "<b>63</b>"],
], [0.28, 0.15, 0.22, 0.17, 0.18])
s.append(P("480 se 319 kyun? 55 bina-janwar wali photos nikli, aur baaki jahan pretrained model ko koi usable box nahi mila "
           "(chhota, chhupa hua, pani me, ya galat class). Validation me total <b>76 boxes</b> hain (kuch photos me 1 se zyada janwar)."))

s.append(P("4.6 Test videos (Day 3 / Day 7)", h2))
s.append(P("Images ke ilawa model ko <b>video</b> par bhi test karna tha. Wikimedia Commons se <b>14 openly-licensed clips</b> "
           "liye (licence list: <font face='Courier'>data/sample_videos/attribution.csv</font>):"))
s += table(["Type", "Clips", "Note"], [
    ["Target species", "leopard_india, leopard_tree, boar_berlin, boar_bulgaria, jackals, peafowl_walking, peafowl_running, nilgai_zoo",
     "Mugger, chinkara, striped hyena ki free video mili hi nahi"],
    ["Stand-in", "hyena_spotted, crocodile_nile, gazelle_hluhluwe", "Milta-julta janwar (spotted hyena, Nile croc, gazelle)"],
    ["Camera trap", "camtrap_general (elk), camtrap_jaguarundi", "Non-target janwar - 'unknown' test"],
    ["Human", "human_hiking", "Person alert test"],
], [0.18, 0.5, 0.32])

s.append(P("4.7 Reproducibility", h2))
s.append(P("Photos aur videos git me nahi (size bara). <font face='Courier'>restore_dataset.py</font> wahi <b>exact 480 photos</b> "
           "observation ID se dobara download karta hai. <font face='Courier'>download_dataset.py</font> random sample karta hai, "
           "isliye restore ke liye use nahi karte (warna pseudo-labels match nahi karenge)."))
s += box(["Dataset ki kamzoriyan (khud hi bata do, supervisor impress hota hai):",
          *bullets([
              "Worldwide photos, Sindh ka habitat nahi.",
              "Zyada tar saaf din ki photos - camera trap, raat, IR (infrared) footage nahi.",
              "Boxes <b>pseudo-labels</b> hain, haath se check nahi hue - isliye validation score <b>optimistic</b> hai.",
              "Jin photos me pretrained model fail hua (mushkil, chhote janwar) wo dataset me hain hi nahi.",
              "Validation chhota: per species sirf 4-11 images. Wild boar ke sirf 14 train images.",
              "Negative images (insaan, khaali scene) nahi the - is wajah se model ne hikers ko nilgai bola (Day 6).",
          ])], bg=WARN_BG, line=WARN_LINE, label="Kamzoriyan")
s.append(PageBreak())

# ---------------- 5. Day by day ----------------
s.append(P("5. Day by day implementation", h1))
s.append(P("Day 1 - Environment setup aur pehla test", h2))
s += bullets([
    "Python virtual env (<font face='Courier'>venv/</font>), Ultralytics YOLO, OpenCV, PyTorch install kiye.",
    "COCO model (yolo11n) chalaya: deer par <b>kuch detect nahi</b>, leopard ko <b>'giraffe'</b> bola (0.72). Wajah: COCO me deer/leopard class hi nahi.",
    "OIV7 model (yolov8m-oiv7) par switch: deer 0.84, leopard 0.47, person 0.54 - sab sahi. Ye baseline ban gaya.",
    "Script: <font face='Courier'>scripts/detect.py</font>.",
])
s.append(P("Day 2 - Species shortlist aur dataset", h2))
s.append(P("Section 4 me detail. 11 candidates -> 8 species, 480 photos, quality check."))
s.append(P("Day 3 - Pretrained model ka imtihaan", h2))
s += bullets([
    "OIV7 model ko saari 480 photos par chalaya, conf 0.10 tak saari detections save ki (<font face='Courier'>day3_detections.json</font>) taake baad me har threshold bina dobara chalaye compare ho sake.",
    "Har result ko categories me dala: <b>exact</b> (sahi naam), <b>family</b> (milti-julti class, e.g. Cheetah), <b>generic</b> ('Animal'), <b>wrong</b>, <b>none</b>.",
    "Jin 116 images me kuch nahi mila unko haath se dekh kar wajah likhi: E = janwar hi nahi, S = chhota/chhupa, A = saaf janwar phir bhi miss.",
    "Result: sirf <b>41%</b> images me exact species naam. Main problem <b>galat naam</b> hai, janwar dhoondna nahi (leopard->Cheetah, nilgai/chinkara->Deer, jackal->Fox, hyena ki class hi nahi).",
    "Background false detections (Tree, Plant) bohot - inko class whitelist se filter karna padta.",
    "Video test bhi kiya: raat / IR / dusk footage par fail, aur ek stork ko 'Person' bola - false poaching alert ka khatra.",
])
s.append(P("Day 4 - Faisla: fine-tune", h2))
s.append(P("Threshold upar neeche karne se ya whitelist se <b>galat naam theek nahi hota</b>. Hyena ki class hi nahi. "
           "8 me se 5 species ka exact hit 40% se kam. Isliye faisla: <b>apni 8 classes par fine-tune karo</b>."))
s.append(P("Day 5 - Training dataset, training, threshold", h2))
s += bullets([
    "Pseudo-label dataset banaya (319 images, Section 4.4-4.5).",
    "<font face='Courier'>scripts/train.py</font>: yolo11n.pt se shuru, imgsz 320, batch 16, 100 epochs, seed 42, optimizer auto (SGD/AdamW Ultralytics khud chunta hai), lr0 0.01, 3 warmup epochs.",
    "Pehle CPU par train hua (purana laptop), naye PC par <b>GTX 1660 Super GPU</b> par retrain - takreeban 15 minute.",
    "Weights: <font face='Courier'>runs/species_v1/weights/best.pt</font> (sab se acha val score wala epoch).",
    "<font face='Courier'>day5_evaluate.py</font>: conf 0.10 se 0.70 tak sweep, best F1 par <b>conf = 0.40</b> chuna.",
])
s += img("runs/species_v1/results.png", 0.95,
         "Training curves (runs/species_v1/results.png): loss neeche ja raha hai (model seekh raha hai), "
         "precision / recall / mAP upar ja kar stable. Train aur val loss dono girte hain.")
s.append(P("Day 6 - Video pipeline", h2))
s.append(P("<font face='Courier'>scripts/video_pipeline.py</font> - base paper ka visual branch + output layer:"))
s += bullets([
    "OpenCV video file ya webcam parhta hai.",
    "Har <b>3rd frame</b> par models chalte hain, beech ke frames me pichle boxes reuse (speed ke liye).",
    "Species model + COCO person model dono chalte hain.",
    "<b>Overlap rule:</b> agar species box aur person box ek hi cheez par hain (chhote box ka >= 60% overlap) to "
    "person jeetta hai agar COCO confident ho (>= 0.5), warna person box hata do.",
    "Output: annotated mp4 (960 px), <b>detections CSV</b> (time, frame, label, confidence, box), "
    "<b>alerts CSV</b> (WILDLIFE ya HUMAN INTRUSION, har label ka ek alert per 10 sec - spam nahi).",
])
s.append(P("<b>Problem jo mila:</b> species model ne insaan kabhi dekha hi nahi tha, to hikers ko nilgai / peafowl bola (0.97 tak!). "
           "Overlap rule se hiking clip par nilgai false alarms <b>57 se 0</b> ho gaye. Asal fix: training me insaan aur khaali "
           "scenes ko <b>negative</b> images ke taur par daalna (v2 me ho raha hai)."))
s.append(P("Day 7 - Prototype vs pretrained, 14 videos par", h2))
s.append(P("<font face='Courier'>scripts/day7_videos.py</font>: dono systems ko same clips par chalaya, har 0.5 sec ek frame, conf 0.25. "
           "Har frame ko gina: sahi label / galat species / false person. Results Section 6 me."))
s.append(PageBreak())

# ---------------- 6. Results ----------------
s.append(P("6. Results aur unka matlab", h1))
s.append(P("6.1 Pretrained model (Day 3, 480 photos, conf 0.25, kharab photos hata kar)", h2))
s += table(["Species", "Valid images", "Exact naam", "Exact + related", "Kya hua"], [
    ["Indian peafowl", "57", "95%", "95%", "Acha - 'Bird' class"],
    ["Mugger", "53", "68%", "68%", "Pani me chhupe miss"],
    ["Chinkara", "53", "38%", "96%", "Mila, magar 'Deer' bola"],
    ["Nilgai", "58", "12%", "78%", "Mila, magar 'Deer' bola"],
    ["Leopard", "52", "12%", "71%", "Zyada tar 'Cheetah'"],
    ["Golden jackal", "54", "11%", "52%", "'Fox' ya miss"],
    ["Striped hyena*", "58", "0%", "43%", "Class hi nahi - Fox/Dog/Bear/Lion"],
    ["Wild boar", "40", "20%", "20%", "Zyada tar miss"],
], [0.2, 0.14, 0.14, 0.17, 0.35])
s.append(P("* v1 ki 'striped hyena' photos asal me spotted hyena thi (section 4.3 ka correction dekho). "
           "Ye note 6.2 aur 6.3 ki hyena rows par bhi lagta hai.", small))
s.append(P("6.2 Fine-tuned model (Day 5, validation: 63 images, 76 boxes)", h2))
s += box(["<b>mAP@50 = 0.707 &nbsp;|&nbsp; mAP@50-95 = 0.546 &nbsp;|&nbsp; conf 0.40 par: Precision 0.77, Recall 0.61, F1 0.68</b>"])
s += table(["conf", "Precision", "Recall", "F1"], [
    ["0.10", "0.66", "0.67", "0.67"], ["0.25", "0.75", "0.62", "0.68"], ["<b>0.40</b>", "<b>0.77</b>", "<b>0.61</b>", "<b>0.68</b>"],
    ["0.50", "0.75", "0.53", "0.62"], ["0.70", "0.87", "0.45", "0.59"],
], [0.25, 0.25, 0.25, 0.25])
s.append(P("<b>Threshold ka trade-off:</b> conf upar karo to precision barhti hai (kam false alarm) magar recall girta hai "
           "(zyada janwar miss). F1 0.25-0.40 par flat hai; 0.40 chuna kyunke wahan F1 best hai aur precision zyada."))
s += table(["Species", "Precision", "Recall", "Exact hit pretrained", "Exact hit fine-tuned"], [
    ["Leopard", "0.75", "0.67", "12%", "<b>88%</b>"], ["Chinkara", "0.73", "0.62", "30%", "<b>80%</b>"],
    ["Wild boar", "1.00", "0.20", "50%", "50%"], ["Striped hyena*", "0.80", "1.00", "0%", "<b>100%</b>"],
    ["Golden jackal", "1.00", "0.33", "17%", "33%"], ["Indian peafowl", "0.80", "0.57", "100%", "73% (gira)"],
    ["Nilgai", "0.67", "0.62", "10%", "<b>80%</b>"], ["Mugger", "0.83", "0.62", "100%", "86%"],
    ["<b>All</b>", "<b>0.77</b>", "<b>0.61</b>", "<b>41%</b>", "<b>76%</b>"],
], [0.22, 0.15, 0.15, 0.24, 0.24])
s.append(P("<b>Matlab:</b> fine-tuning ne naam wala masla hal kar diya - exact species <b>41% se 76%</b>. Sab se bara faida "
           "leopard, hyena, nilgai, chinkara par. Peafowl gira kyunke pretrained model ne lakhon birds dekhe the, hamare model ne "
           "sirf 43 peafowl. Wild boar sab se kamzor (sirf 14 train images, recall 0.20)."))
s += img("runs/species_v1/confusion_matrix_normalized.png", 0.75,
         "Normalized confusion matrix: diagonal = sahi. 'background' column/row = miss ya false box. "
         "Wild boar ke kuch boxes peafowl ki taraf confuse hote hain.")
s.append(P("6.3 Videos par (Day 7) - sahi frames / galat species frames / false person frames", h2))
s += table(["Clip", "Expected", "Pretrained OIV7", "Hamara prototype"], [
    ["leopard_india", "leopard", "0 / 31 / 0", "<b>31 / 2 / 1</b>"], ["leopard_tree", "leopard", "0 / 2 / 0", "<b>12 / 0 / 0</b>"],
    ["hyena_spotted*", "striped hyena", "0 / 7 / 0", "<b>6 / 1 / 0</b>"], ["jackals", "golden jackal", "19 / 45 / 0", "<b>27 / 35 / 0</b>"],
    ["nilgai_zoo", "nilgai", "0 / 20 / 0", "<b>20 / 7 / 9</b>"], ["peafowl_walking", "peafowl", "30 / 0 / 0", "28 / 15 / 0"],
    ["human_hiking", "person", "48 / 3 / 0", "46 / 3 / 0"], ["gazelle_hluhluwe", "chinkara", "46 / 39 / 0", "0 / 46 / 0"],
    ["peafowl_running", "peafowl", "6 / 1 / 0", "0 / 44 / 0"], ["crocodile_nile", "mugger", "0 / 3 / 7", "0 / 3 / 9"],
    ["boar_berlin", "wild boar", "0 / 0 / 0", "1 / 4 / 0"], ["boar_bulgaria", "wild boar", "0 / 6 / 0", "1 / 0 / 1"],
    ["camtrap_general", "none", "0 / 20 / 0", "0 / 19 / 0"], ["camtrap_jaguarundi", "none", "0 / 6 / 0", "0 / 7 / 0"],
], [0.25, 0.2, 0.25, 0.3])
s += bullets([
    "<b>Jeet:</b> leopard (0->31, 0->12), hyena (0->6, magar ye spotted hyena thi aur model bhi spotted hyena par train tha), nilgai zoo (0->20), jackal (19->27).",
    "<b>Clip correction:</b> hyena_spotted clip spotted hyena hai aur gazelle_hluhluwe asal me <b>impala</b> hai. v2 me dono ko non-target clip maana gaya hai (expected: none).",
    "<b>Haar:</b> gazelle clip (46->0, har frame 'nilgai'), peafowl_running (chital ka jhund 'nilgai' bana).",
    "<b>Wild boar</b> raat / dusk videos par sirf 1 frame - training me raat / IR images thi hi nahi.",
    "<b>Unknown janwar</b> (elk, jaguarundi) zabardasti 8 me se kisi class me daal diye gaye.",
    "COCO person model ne stork aur nilgai ko bhi 'person' bola - false intrusion alert.",
])
s += img("data/results/videos/false_person_on_bird.jpg", 0.6,
         "False person example: crocodile_nile clip me stork (bird) ko 'Person' detect kiya gaya.")
s.append(PageBreak())

# ---------------- 7. Limitations ----------------
s.append(P("7. Kamzoriyan (limitations) - honestly", h1))
s += table(["Kamzori", "Wajah", "Fix (plan)"], [
    ["Score optimistic", "Val boxes pseudo-labels; mushkil images dataset me hi nahi", "Roboflow me boxes haath se check; alag test set"],
    ["Wild boar kamzor", "Sirf 14 train images, 20/60 photos bekaar", "300 images per species"],
    ["Raat / IR fail", "Training me sirf din ki photos", "Night/IR images + synthetic IR copies"],
    ["Hikers ko janwar bolna", "Koi negative image nahi", "Insaan + khaali scenes as negatives"],
    ["Milte-julte janwar confuse", "Gazelle/chital -> nilgai; koi 'confuser' class nahi dekhi", "Confuser species as negatives"],
    ["Unknown janwar", "Model sirf 8 classes jaanta hai", "YOLO-World 'unknown_animal' detector"],
    ["False person", "COCO model ne bird/nilgai par 'person'", "Person conf 0.40 + 'zyada confident jeetay' rule"],
    ["Label flicker", "Frame-to-frame naam badalta hai", "Tracking (ByteTrack) + smoothing, baad me"],
    ["Habitat mismatch", "Worldwide photos", "Pakistan data + field test"],
], [0.24, 0.38, 0.38])
s.append(P("8. Week 1 fixes (v2) - results", h1))
s.append(P("Week 1 ki kamzoriyan theek karne ke liye naya data, naya dataset aur do naye models. Pura detail README me."))
s += bullets([
    "<b>Data:</b> har species ki <b>300</b> photos, 14 confuser species x 80 (gaye, bhains, bengal fox, spotted hyena, jungle cat...), "
    "6 khaali scene types x 40 (<font face='Courier'>download_more.py</font>, <font face='Courier'>manifest_v2.csv</font>).",
    "<b>Striped hyena fix:</b> section 4.3 ka correction dekho.",
    "<b>Dataset v2:</b> 1307 species train images + 416 synthetic IR copies + 1547 negatives, <b>70/15/15</b> train/val/test "
    "(test set training me kabhi use nahi hota).",
    "<b>Models:</b> species_v2 (YOLO11n) aur species_v12 (YOLO12n, base paper jaisa), dono paper ki settings par GPU par.",
])
s.append(P("Test split par result (269 janwar photos + 248 negatives, kisi model ne nahi dekhi)", h2))
s += table(["Model", "mAP@50", "Recall", "Exact hit", "False alarm (negatives)", "IR recall"], [
    ["v1 (Week 1)", "0.439", "0.50", "62%", "49%", "0.29"],
    ["<b>v2 (YOLO11n)</b>", "<b>0.791</b>", "<b>0.70</b>", "<b>81%</b>", "17%", "<b>0.59</b>"],
    ["v12 (YOLO12n)", "0.757", "0.66", "75%", "<b>8%</b>", "0.54"],
], [0.22, 0.13, 0.13, 0.14, 0.24, 0.14])
s += bullets([
    "<b>v2 sab se acha</b> - ab ye pipeline ka default model hai. mAP 0.44 se 0.79, raat/IR recall double.",
    "<b>Week 1 ka 0.707 optimistic tha:</b> naye mushkil test set par v1 sirf 0.439. Iska jawab tayyar rakho: chhota aur aasaan val set tha.",
    "<b>Negatives ne kaam kiya:</b> false alarm 49% se 17% (v2) / 8% (v12); insaan aur khaali scene par zero. Spotted hyena clip ab 'unknown_animal'.",
    "<b>YOLOv12 ne YOLO11n ko nahi haraya</b> - mAP aur recall kam, magar false alarm sab se kam. Same chhote data par naya architecture faida nahi deta.",
    "<b>Videos (Day 7):</b> jackals 27 -> 48 sahi frames, leopard_tree 12 -> 18, peafowl_walking ke 15 false mugger khatam. "
    "Magar nilgai_zoo 20 -> 0 (ab 'unknown_animal') aur impala clip abhi bhi 'nilgai'.",
    "<b>Abhi bhi kamzor:</b> golden jackal (recall 0.55, IR 0.30), raat ki wild boar video. Boxes abhi bhi pseudo-labels, IR synthetic.",
    "<b>Aage:</b> Roboflow me boxes check, Pakistan data, field test, phir YAMNet audio + fusion.",
])
s.append(PageBreak())

# ---------------- 9. Q&A ----------------
s.append(P("9. Supervisor ke sawal aur jawab", h1))
s.append(P("Jawab English me diye hain (viva / meeting English me hoti hai), short aur seedhe.", small))
qa = [
    ("Q1. Where does your dataset come from?",
     "From iNaturalist research-grade observations with open licences (407 CC BY-NC, 64 CC BY, 9 CC0). Every photo's author and "
     "link is in attribution.csv. Test videos are 14 openly licensed clips from Wikimedia Commons."),
    ("Q2. How many images do you have?",
     "480 photos (60 per species). After removing 55 photos with no live animal and photos with no usable box, 319 images "
     "remain: 256 train and 63 validation, with 76 validation boxes."),
    ("Q3. Who drew the bounding boxes?",
     "They are pseudo-labels. The pretrained Open Images V7 model detected the animal, and we renamed its box to our species "
     "using the folder label, for example a 'Cheetah' box on a leopard photo becomes 'leopard'. They are not yet hand-checked; "
     "manual review in Roboflow is planned."),
    ("Q4. Then isn't your accuracy unreliable?",
     "Yes, it is optimistic, and we say so. Validation boxes come from the same pseudo-labelling, and hard images where the "
     "pretrained model failed are not in the set. That is why we also tested on 14 independent videos (Day 7), and v2 adds "
     "a separate test split."),
    ("Q5. Why not use Pakistani images only?",
     "There are very few on iNaturalist (3 for striped hyena, 4 for nilgai). The species look the same worldwide; only the "
     "background differs. Pakistan data and a field test are planned."),
    ("Q6. How did you split the data?",
     "80/20 per species (stratified), with a fixed random seed of 42 so the split is reproducible."),
    ("Q7. Why did you fine-tune instead of using the pretrained model?",
     "The pretrained model found the animals but gave the wrong name: exact species for only 41% of images, with no hyena "
     "class at all. A threshold cannot fix a wrong class name. After fine-tuning, exact hits went to 76%."),
    ("Q8. Why YOLO and why YOLO11n?",
     "YOLO is a one-stage real-time detector, which suits video. YOLOv11 is in our proposal; the nano size is fast, runs on "
     "small hardware and overfits less on a small dataset. YOLOv12 (the base paper's model) will also be trained for comparison."),
    ("Q9. What are your training settings?",
     "Same as the base paper: 320x320 input, batch 16, 100 epochs, starting from pretrained yolo11n weights (transfer "
     "learning), seed 42. About 15 minutes on a GTX 1660 Super."),
    ("Q10. What is mAP@50 and what did you get?",
     "Mean average precision at IoU 0.5, averaged over all classes. We got 0.707; mAP@50-95, which is stricter about box "
     "position, is 0.546."),
    ("Q11. How did you choose the confidence threshold?",
     "By sweeping 0.10 to 0.70 on the validation set and choosing the best F1: conf 0.40 gives precision 0.77, recall 0.61, F1 0.68."),
    ("Q12. Which species is weakest and why?",
     "Wild boar (recall 0.20): only 14 training images, a third of its photos had no live animal, and the test clips are night "
     "or dusk footage, which the training set did not contain. Golden jackal is second (recall 0.33)."),
    ("Q13. How do you detect humans?",
     "A second model, COCO-pretrained yolo11n restricted to the 'person' class, runs on every processed frame. An overlap rule "
     "removes duplicate boxes when the species and person models fire on the same object."),
    ("Q14. What does the system output?",
     "An annotated video, a CSV log of every detection (time, frame, label, confidence, box) and an alerts CSV with WILDLIFE or "
     "HUMAN INTRUSION alerts, at most one per label every 10 seconds."),
    ("Q15. How is this related to the base paper?",
     "We follow Velpula et al. 2026: YOLO visual branch, YAMNet audio branch, a fusion layer and an output layer. Week 1 built "
     "the visual branch and the output layer, with the paper's training settings. Audio and fusion come next."),
    ("Q16. What happens with an animal that is not in your 8 classes?",
     "In v1 it is forced into one of the 8 classes, which is a known limitation. The v2 pipeline adds an open-vocabulary "
     "YOLO-World detector that reports it as 'unknown_animal'; on the test clips the spotted hyena and most of the elk "
     "and jaguarundi frames are now unknown_animal."),
    ("Q17. Were your striped hyena photos correct?",
     "No, and we found it ourselves. The iNaturalist taxon used in Week 1 (41886) is the spotted hyena, so all 60 'striped "
     "hyena' photos and the v1 hyena results are really spotted hyena. The survey script now requires an exact name match, "
     "v2 uses 300 verified Hyaena hyaena photos, and the old photos are kept as spotted-hyena negatives so the model learns "
     "to tell the two apart."),
]
for q, a in qa:
    s.append(KeepTogether([P(q, q_style), P(a)]))
s.append(PageBreak())

# ---------------- 10. Glossary / files ----------------
s.append(P("10. Kaunsi file kya karti hai", h1))
s += table(["File", "Kaam"], [
    ["scripts/detect.py", "Kisi image / video par YOLO chalana (Day 1)"],
    ["scripts/species_config.py", "11 candidate species aur unki closest OIV7 class"],
    ["scripts/inat_survey.py", "iNaturalist par photo counts ka survey (Day 2)"],
    ["scripts/download_dataset.py / restore_dataset.py", "Photos download / exact 480 restore"],
    ["scripts/check_dataset.py, flag_evidence.py", "Quality check, evidence-of-presence flags"],
    ["scripts/evaluate_pretrained.py, day3_adjusted.py", "Pretrained model ka evaluation + manual review (Day 3)"],
    ["scripts/find_videos.py, download_videos.py, evaluate_videos.py", "Test videos dhoondna, download, test (Day 3)"],
    ["scripts/build_yolo_dataset.py", "Pseudo-label dataset, 80/20 split (Day 5)"],
    ["scripts/train.py", "Fine-tuning (Day 5)"],
    ["scripts/day5_evaluate.py", "Threshold sweep, pretrained vs fine-tuned"],
    ["scripts/video_pipeline.py", "Video pipeline: species + person, alerts, CSV (Day 6)"],
    ["scripts/day7_videos.py", "Prototype vs pretrained, 14 clips (Day 7)"],
    ["scripts/download_more.py, build_yolo_dataset_v2.py", "v2: 300 photos/species, negatives, IR copies, 70/15/15 split"],
    ["scripts/evaluate_v2.py", "v2: v1 / v2 / v12 ka test split par comparison"],
    ["runs/species_v1, species_v2, species_v12 /weights/best.pt", "Hamare trained models (v1, v2, v12)"],
    ["data/yolo_dataset/data.yaml", "Training dataset ka config (8 class names)"],
    ["data/results/*.md", "Har din ke result tables"],
], [0.48, 0.52])
s.append(P("Glossary (quick revision)", h1))
s += table(["Lafz", "Ek line me"], [
    ["Bounding box", "Janwar ke gird rectangle"],
    ["Confidence", "Model ka yakeen, 0-1"],
    ["Pretrained", "Pehle se bare dataset par train"],
    ["Fine-tuning", "Pretrained model ko apne data par thoda aur train karna"],
    ["Pseudo-label", "Model se banaya hua label (insaan ne nahi)"],
    ["Negative image", "Jis me target janwar nahi - model ko 'yahan kuch nahi' sikhati hai"],
    ["Confuser", "Milta-julta janwar jo galti karwata hai (gaye vs nilgai)"],
    ["IoU", "Do boxes ka overlap"],
    ["Precision / Recall", "Kitna bola woh sahi / kitna tha woh pakra"],
    ["mAP@50", "Detection ka overall score (IoU 0.5)"],
    ["Overfitting", "Ratta - training par acha, naye data par bura"],
    ["Open-vocabulary (YOLO-World)", "Text se class batao ('animal'), fixed list nahi"],
    ["YAMNet", "Google ka audio model, 521 sound classes - baad me audio branch ke liye"],
    ["Fusion", "Video + audio dono ka faisla mila kar final alert"],
    ["ByteTrack", "Tracking: ek janwar ko frames me ek hi ID dena"],
], [0.3, 0.7])

doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.8 * cm,
                        bottomMargin=1.8 * cm, title="FYP Complete Guide", author="FYP")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("written", OUT)
