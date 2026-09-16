# AI Based Biodiversity Monitoring Using Video Analysis

Final Year Design Project — NED University, Department of Telecommunications Engineering

## Week 1 scope

Focus only on the AI detection component: pretrained YOLO model, wildlife
data, and video/image detection. Backend, database, dashboard, audio
recognition, and tracking are addressed in later weeks.

## Day 1 — Environment setup and first detection test

Completed:
- Python virtual environment created (`venv/`)
- Installed: ultralytics (YOLO), OpenCV, PyTorch
- Loaded and compared two pretrained YOLO models
- Collected sample wildlife and human test images (`data/sample_images/`)
- Ran detection on the samples and saved annotated results (`data/results/run/`)

### Model comparison (important Day 1 finding)

First attempt used the standard COCO-pretrained model (`yolo11n.pt`),
which only knows 80 generic object classes. It detected humans
correctly but failed on wildlife: no detection at all on the deer, and
the leopard was misclassified as "giraffe" — because COCO has no
"deer" or "leopard" class to begin with.

Switched the default model to `yolov8m-oiv7.pt`, pretrained on the
Open Images V7 dataset (601 classes, including deer, leopard, tiger,
fox, monkey, and more). Re-ran the same tests:

| Image | Model | Result |
|---|---|---|
| deer.jpg (chital) | yolo11n (COCO) | No detection |
| deer.jpg (chital) | yolov8m-oiv7 | **Deer, confidence 0.84** |
| leopard.jpg | yolo11n (COCO) | Misclassified as "giraffe", 0.72 |
| leopard.jpg | yolov8m-oiv7 | **Leopard, confidence 0.47** |
| person_hiking.jpg | yolov8m-oiv7 | **Person, confidence 0.54** |

### Key observation

A generic COCO-pretrained model cannot label wildlife species by name
since COCO's 80 classes don't include them. Switching to an
Open-Images-V7-pretrained model fixed this immediately, since it
already includes most of our target species. This is now the
project's default detection model (`scripts/detect.py`). Some species
in our target list (e.g. wild boar, peacock) may still need dedicated
fine-tuning — that comparison continues on Day 2 to Day 5 as planned
(species shortlisting, dataset collection, and the
pretrained-vs-fine-tune decision).

## How to run

```
venv\Scripts\python.exe scripts\detect.py --source data\sample_images\deer.jpg
venv\Scripts\python.exe scripts\detect.py --source data\sample_images\leopard.jpg
venv\Scripts\python.exe scripts\detect.py --source data\sample_images\person_hiking.jpg
```

Annotated output images are saved to `data/results/run/`.

## Project structure

```
FYP/
  venv/                  Python virtual environment
  data/
    sample_images/       test images for detection
    sample_videos/        test videos for detection
    results/              YOLO output (annotated images/videos)
  scripts/
    detect.py             runs YOLO detection on an image or video
  requirements.txt
```

## Tech stack (from project proposal)

YOLOv11, OpenCV, ByteTrack, Python, FastAPI, React.js, TailwindCSS,
Chart.js, Firebase Firestore, EmailJS, YAMNet, Librosa. Training on
Google Colab, deployment on Vercel + Render.
