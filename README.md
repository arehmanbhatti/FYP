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

## Day 2 — Species shortlist and initial dataset

Completed:
- Surveyed iNaturalist (research-grade, CC0 / CC-BY / CC-BY-NC photos) for 11 candidate
  species from Sindh / Pakistan fauna (`scripts/inat_survey.py`, results in `data/dataset_survey.json`)
- Shortlisted **8 target species** + humans
- Downloaded 60 photos per species, 480 in total (`scripts/download_dataset.py`,
  attribution in `data/dataset/attribution.csv`)
- Ran a quality check: 0 corrupt files, 0 duplicates, 5 images under 400 px (`scripts/check_dataset.py`)

### Final target species

| Species | Closest OIV7 class the pretrained model has | iNat photos (world / Pakistan) |
|---|---|---|
| Leopard | Leopard | 6776 / 31 |
| Chinkara gazelle | Antelope | 632 / 11 |
| Wild boar | Pig | 35197 / 19 |
| Striped hyena | none | 6761 / 0 |
| Golden jackal | Dog | 3979 / 36 |
| Indian peafowl | Bird | 24213 / 12 |
| Nilgai | Antelope | 2367 / 4 |
| Mugger crocodile | Crocodile | 2779 / 5 |
| Human | Person | — |

Dropped: urial (121 photos worldwide) and Bengal fox (256 worldwide, 1 in Pakistan), too few images.
Sindh ibex was dropped because the iNaturalist taxon is merged with domestic goat, so its
count is meaningless. It needs a camera-trap / Kaggle source instead.

### Caveats
- Pakistan-only photos are scarce, so the dataset is worldwide. The classes look the same, but
  the backgrounds are not Sindh habitat.
- Photos are mostly clear daytime shots, unlike camera-trap or infrared footage. Real
  deployment footage will look different.
- Species labels rely on iNaturalist research-grade community IDs. No image-by-image manual check yet.
- These are whole-image class labels only. Fine-tuning YOLO would still need bounding boxes.

## Day 3 — Pretrained model performance on the dataset

Completed:
- Ran `yolov8m-oiv7` on all 480 dataset images and stored every detection down to conf 0.10,
  so thresholds can be compared without re-running (`scripts/evaluate_pretrained.py`,
  results in `data/results/day3_summary.md`)
- Looked at the 116 images where no animal was detected and labelled why (`scripts/day3_adjusted.py`,
  contact sheets in `data/results/day3/`)
- Recorded confidence, false detections and per-species weak spots (below)

### Corrected results (conf >= 0.25, bad dataset images removed)

| Species | valid images | exact-class hit | exact + related class hit | Verdict |
|---|---|---|---|---|
| Indian peafowl | 57 | 95% | 95% | Good, works as is |
| Mugger crocodile | 53 | 68% | 68% | Usable, misses mostly small or half-submerged animals |
| Chinkara | 53 | 38% | 96% | Found, but labelled "Deer" instead of "Antelope" |
| Nilgai | 58 | 12% | 78% | Found, but labelled "Deer" instead of "Antelope" |
| Leopard | 52 | 12% | 71% | Found as a big cat, but mostly labelled "Cheetah" (25 images) |
| Golden jackal | 54 | 11% | 52% | Weak: labelled "Fox" (22 images) or missed |
| Striped hyena | 58 | 0% | 43% | No OIV7 class. Labelled Fox / Dog / Bear / Lion |
| Wild boar | 40 | 20% | 20% | Weak: mostly not detected, or only a generic "Animal" |

"Exact + related" counts a detection as right if the class is a plausible neighbour (for
example Cheetah for leopard). For a species-level monitoring system only the exact column
counts, and it is low for 5 of 8 species.

### Observations
- **Confidence is low where the class is wrong.** Correct detections average 0.43-0.67
  (leopard 0.43, jackal 0.44, chinkara 0.66, mugger 0.67). Raising the threshold to 0.5 hurts
  most species (peafowl 90% -> 68%, mugger 60% -> 43%, leopard 10% -> 2%; chinkara barely changes, 33% -> 32%).
  A lower threshold (0.25-0.30) keeps more real detections. The proper threshold sweep is Day 5.
- **The main failure is species confusion, not missing animals.** The model finds
  the animal but names a similar class: leopard->Cheetah, chinkara/nilgai->Deer,
  jackal->Fox. It has no class for hyena at all. Wild boar is a mix of Pig, generic
  "Animal", and nothing.
- **False detections:** the background classes Plant and Tree fire constantly (dozens per species) and must be
  filtered out with a class whitelist. Wrong-animal detections are rare and scattered
  (Kangaroo on jackal, Brown bear/Lion on hyena, Owl on leopard).
- **Dataset problem found:** 55 of 480 images (11%) contain no live animal: paw prints, scat,
  skulls, carcasses, landscapes. iNaturalist "research grade" allows these, and the
  Evidence-of-Presence annotation only covers ~20% of images, so it is not enough to
  filter them. Wild boar is worst (20 of 60). These need removing before any training.
- **Hard cases the model misses:** tiny or camouflaged animals (leopard in a tree, crocodile
  in water, boar in undergrowth), 39 images. 22 further images contain a clearly visible animal that the model still
  missed, including a leopard on an infrared trail-camera frame and a running boar.
- **Possible label errors:** at least one "striped hyena" image is clearly a spotted hyena, and a
  "nilgai" image looks like a domestic cow. Community IDs are not fully reliable.
- **Species that need better training data:** hyena, jackal, wild boar (weak), then leopard
  vs cheetah, chinkara/nilgai vs deer (class naming). Peafowl and mugger do not.

### Video testing (added after the still-image results)

No free video of mugger, chinkara or striped hyena exists on Wikimedia Commons, so 14 openly
licensed clips were collected (`scripts/find_videos.py`, `scripts/download_videos.py`, licences in
`data/sample_videos/attribution.csv`). Three are **stand-ins, not the target species**: spotted hyena,
Nile crocodile, and a gazelle. Frames were sampled every 0.5 s and run through the model at conf 0.25
(`scripts/evaluate_videos.py`, table in `data/results/videos/video_summary.md`, best frames in the same folder).

| Video | What the model said | Verdict |
|---|---|---|
| leopard_india | Cheetah in 31 of 31 frames | Same confusion as on images |
| jackals | Fox, Deer, Dog (never one stable label) | Same confusion |
| peafowl_walking | Bird in 30 of 30 frames | Works |
| human_hiking | Person in 48 of 50 frames | Works |
| hyena_spotted (stand-in) | Dog / Horse | Wrong, as expected without a hyena class |
| gazelle_hluhluwe (stand-in) | Antelope, 46 of 46 frames | Works, but also fires "Bird" (39) |
| camtrap_general (elk) | Deer / Camel / Antelope | Found, class unstable |
| leopard_tree | Owl in 2 of 18 frames | Leopard mostly missed |
| crocodile_nile (stand-in) | croc never detected | Missed. Also "Person" in 7 frames |
| boar_berlin | nothing | Missed: dusk video, dark boars lying down |
| boar_bulgaria | "Bird" in 6 frames | Only false detections on this night IR clip |
| camtrap_jaguarundi | Kangaroo / Fox | Wrong labels |

New findings from video:
- **False humans are a risk.** The "Person" detections in the crocodile clip are a stork on the
  shore (`data/results/videos/false_person_on_bird.jpg`). Since human detection drives the poaching alert,
  a false "person" would raise a false alarm.
- **Night, infrared and dusk footage is a weak spot.** Camera-trap and low-light clips gave
  no detections or wrong ones. This is the setting the project must support.
- **Labels flicker between frames** (Fox / Deer / Dog on the same jackals). Tracking and
  smoothing will be needed later to produce one stable species per animal.
- Clip caveats: `nilgai_zoo` holds a small distant animal that is not confirmed to be a nilgai,
  and `peafowl_running` is mostly a herd of chital deer with a peafowl in it. Treat those two as unreliable.
  The `boar_berlin` file has broken frame-rate metadata, handled by reading sequentially.
- Clip counts are small, so these are indications, not measured accuracy.

### Not done yet
- No proper measurement on real Sindh or camera-trap footage. The clips are short, and the still
  images from iNaturalist are cleaner than real deployment footage, so real performance will likely be lower.

## Base paper

The project follows Velpula et al. 2026, "Multimodal Deep Learning Based Wildlife Intrusion
Perception Using YOLOv12 and YAMNet" (`paper3.pdf`): YOLO visual detection, YAMNet audio, a fusion
layer, and an output layer with alerts and a CSV log. Week 1 builds the visual branch and the
output layer. Training settings follow the paper: 320x320 input, batch 16, 100 epochs.

## Day 4 — Pretrained or fine-tune?

Decision: **fine-tune.** On Day 3 the pretrained OIV7 model gave the exact species name for under
40% of images for 5 of the 8 species (leopard, nilgai, jackal, hyena, wild boar). It has no hyena
class at all. Threshold tuning or a class whitelist cannot fix a wrong class name. Only peafowl
and mugger worked as is.

## Day 5 — Training dataset, fine-tuning and threshold

Completed:
- Built a YOLO-format dataset from the Day 2 photos (`scripts/build_yolo_dataset.py`,
  output `data/yolo_dataset/`): 319 images, 80/20 split per species (256 train / 63 val).
  Boxes are **pseudo-labels**: the Day 3 pretrained detection, renamed to our species (for
  example a "Cheetah" box on a leopard photo becomes a `leopard` box). Images with no live animal
  (Day 3 review) or no usable box were dropped.
- Fine-tuned YOLO11n at the paper's settings, CPU, 100 epochs (`scripts/train.py`, run in
  `runs/species_v1/`, weights `best.pt`). The run was interrupted at epoch 26 and resumed.
- Threshold sweep and a pretrained vs fine-tuned comparison on the same validation images
  (`scripts/day5_evaluate.py`, full tables in `data/results/day5_summary.md`)

| Train / val images per species | leopard | chinkara | wild boar | hyena | jackal | peafowl | nilgai | mugger |
|---|---|---|---|---|---|---|---|---|
| train | 32 | 42 | **14** | 30 | 25 | 43 | 41 | 29 |
| val | 8 | 10 | **4** | 7 | 6 | 11 | 10 | 7 |

### Results (validation split, 63 images, 76 boxes)

Overall **mAP@50 = 0.700, mAP@50-95 = 0.506**.

F1 is flat between conf 0.20 and 0.30 (0.63). **conf = 0.25** was chosen as the operating
threshold (precision 0.67, recall 0.61). Raising it to 0.50 gives precision 0.74 but recall drops to 0.51.

| Species | precision | recall | F1 | exact hit, pretrained (Day 3) | exact hit, fine-tuned |
|---|---|---|---|---|---|
| leopard | 0.67 | 0.67 | 0.67 | 12% | 88% |
| chinkara | 0.78 | 0.54 | 0.64 | 30% | 70% |
| wild boar | 0.50 | 0.40 | 0.44 | 50% | 50% |
| striped hyena | 0.43 | 0.38 | 0.40 | 0% | 57% |
| golden jackal | 1.00 | 0.83 | 0.91 | 17% | 83% |
| indian peafowl | 0.64 | 0.64 | 0.64 | 100% | **73%** |
| nilgai | 0.64 | 0.54 | 0.58 | 10% | 70% |
| mugger | 0.70 | 0.88 | 0.78 | 100% | 100% |
| **all** | 0.67 | 0.61 | 0.63 | **41%** | **75%** |

"Exact hit" = the image gets at least one box with the right species name at conf >= 0.25.

### Observations
- Fine-tuning fixed the naming problem: exact-species hits went from 41% to 75%. The biggest
  gains are on leopard, jackal, nilgai and hyena, which the pretrained model mislabelled.
- **Peafowl got worse** (100% -> 73%). The pretrained model saw millions of birds. Our model saw 43 peafowl photos.
- **Wild boar is the weakest class.** Only 14 training images. In the confusion matrix 3 of
  its 5 validation boxes are predicted as peafowl.
- About a quarter to a third of leopard, nilgai and hyena boxes are missed entirely ("background" in
  `runs/species_v1/confusion_matrix_normalized.png`).
- **These numbers are optimistic.** The validation boxes are pseudo-labels from the pretrained model,
  not hand-drawn. Images where the pretrained model found nothing (hard, small or camouflaged animals)
  are not in the dataset at all. The validation set is also tiny (4-11 images per species).

## Day 6 — Video detection pipeline

`scripts/video_pipeline.py` implements the visual branch and output layer of the base paper:
- OpenCV reads a video file or webcam
- Two detectors per processed frame (every 3rd frame, boxes reused in between): the fine-tuned
  species model, and the COCO `yolo11n` model restricted to `person` for the human-intrusion alert
- Output in `data/results/pipeline/`: annotated mp4 (downscaled to 960 px), a CSV with every
  detection (time, frame, label, confidence, box), and an alerts CSV (one alert per label per 10 s
  of video, typed WILDLIFE or HUMAN INTRUSION)

**Problem found and fixed.** The species model was trained only on animals, so it labelled
hikers as nilgai and peafowl with confidence up to 0.97. The pipeline now resolves overlapping
species and person boxes: if they cover the same object (intersection >= 60% of the smaller box),
the person box wins when the COCO model is confident (>= 0.5). Otherwise the person box is dropped,
since a weak "person" on an animal was also a false alarm.

Demo results at conf 0.25, after the fix:

| Clip | Detections | Alerts |
|---|---|---|
| leopard_india | leopard 141 (max 0.94), hyena 3 (max 0.29), person 2 | correct leopard alerts; 2 false hyena, 1 false person |
| peafowl_walking | peafowl 166 (max 0.98), mugger 4, person 2 | correct peafowl alerts; 1 false mugger, 1 false person |
| human_hiking | person 421 (max 0.95), wild boar 30, peafowl 8, leopard 2 | correct person alerts; nilgai false alarms gone (57 -> 0), peafowl down (99 -> 8), 5 false wildlife alerts left |

Remaining false alarms are mostly low confidence (0.25-0.4). The worst one left is a `wild_boar`
at 0.88 on a distant hiker that the COCO model does not detect at all, so the overlap rule cannot
remove it. The real fix is adding images of people and empty scenes as negatives to the training set.

## Day 7 — Prototype vs pretrained on test videos

`scripts/day7_videos.py` runs the full prototype (fine-tuned species model + COCO person model +
overlap rule) and the Day 3 pretrained OIV7 model on the same 14 test clips, one frame every
0.5 s, conf >= 0.25. Full table in `data/results/day7_video_summary.md`.

Frames with the correct label / a wrong species label / a false person:

| Clip | expected | pretrained OIV7 | prototype |
|---|---|---|---|
| leopard_india | leopard | 0 / 31 / 0 | **28 / 0 / 1** |
| leopard_tree | leopard | 0 / 2 / 0 | **9 / 0 / 0** |
| hyena_spotted | striped_hyena | 0 / 7 / 0 | **7 / 0 / 0** |
| jackals | golden_jackal | 19 / 45 / 0 | **38 / 35 / 0** |
| peafowl_walking | indian_peafowl | 30 / 0 / 0 | 30 / 0 / 0 |
| human_hiking | person | 48 / 3 / 0 | 45 / 8 / 0 |
| gazelle_hluhluwe | chinkara | **46 / 39 / 0** | 11 / 42 / 1 |
| peafowl_running | indian_peafowl | **6 / 1 / 0** | 0 / 44 / 0 |
| nilgai_zoo | nilgai | 0 / 20 / 0 | 0 / 26 / 9 |
| crocodile_nile | mugger | 0 / 3 / 7 | 0 / 0 / 9 |
| boar_berlin | wild_boar | 0 / 0 / 0 | 0 / 0 / 0 |
| boar_bulgaria | wild_boar | 0 / 6 / 0 | 0 / 0 / 1 |
| camtrap_general | none | 0 / 20 / 0 | 0 / 20 / 0 |
| camtrap_jaguarundi | none | 0 / 6 / 0 | 0 / 10 / 0 |

### Observations
- **Clear wins on the species the pretrained model could not name:** leopard (0 -> 28 and
  0 -> 9 frames), hyena (0 -> 7) and jackal (19 -> 38). Peafowl walking stays perfect.
- **Regressions:** the gazelle clip drops from 46 to 11 correct frames (now called jackal or nilgai),
  and peafowl_running drops from 6 to 0: the herd of chital deer in it is called nilgai and wild boar.
- **Nilgai is not recognised in the zoo clip** (labelled wild boar), and the COCO person model
  fires on it in 9 frames. On crocodile_nile the person model fires on a stork (9 frames).
- **Wild boar is still 0** on both clips (night and dusk footage). It has the fewest training
  images, and no night or IR images were in the training set.
- **No "unknown animal" handling.** Camera-trap clips with non-target animals (elk, jaguarundi)
  are forced into one of our 8 classes.

### Next steps (Week 2)
More data per species (200-300 images, boxes reviewed in Roboflow, night/IR images, people and
empty scenes as negatives), retrain on Colab (also YOLOv12 to match the base paper), then the
YAMNet audio branch and the fusion layer.

## Setup on a new machine

Large files are not in git (venv, photos, videos, weights). Rebuild them:

```
py install 3.12                                   (PyTorch has no wheels for Python 3.15 yet)
py -3.12 -m venv venv
venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu126
venv\Scripts\python.exe -m pip install -r requirements.txt
venv\Scripts\python.exe scripts\restore_dataset.py       (the exact 480 Day 2 photos, by observation id)
venv\Scripts\python.exe scripts\download_videos.py       (the 14 test clips)
venv\Scripts\python.exe scripts\build_yolo_dataset.py
venv\Scripts\python.exe scripts\train.py                 (about 15 min on a GTX 1660 Super)
```

Do not use `download_dataset.py` to restore: it samples photos at random, so the files would not
match the Day 3 detections and pseudo-labels.

## How to run

```
venv\Scripts\python.exe scripts\detect.py --source data\sample_images\leopard.jpg
venv\Scripts\python.exe scripts\train.py                 (add --resume to continue an interrupted run)
venv\Scripts\python.exe scripts\day5_evaluate.py
venv\Scripts\python.exe scripts\video_pipeline.py --source data\sample_videos\leopard_india.webm --conf 0.25
venv\Scripts\python.exe scripts\video_pipeline.py --source 0 --show --conf 0.25      (webcam)
venv\Scripts\python.exe scripts\day7_videos.py --conf 0.25
```

Annotated images go to `data/results/run/`, pipeline output to `data/results/pipeline/`.

## Project structure

```
FYP/
  venv/                     Python virtual environment
  paper3.pdf                base paper (Velpula et al. 2026)
  data/
    dataset/                Day 2 species photos
    yolo_dataset/           YOLO-format training set (data.yaml, 8 classes)
    sample_images/          test images
    sample_videos/          test clips (Day 3 / Day 7)
    results/                Day 3/5/7 summaries, annotated images, pipeline output
  runs/species_v1/          fine-tuned model (weights/best.pt) and training plots
  scripts/
    detect.py               YOLO detection on an image or video
    download_dataset.py, check_dataset.py, flag_evidence.py   Day 2 dataset
    evaluate_pretrained.py, day3_adjusted.py, evaluate_videos.py   Day 3 evaluation
    build_yolo_dataset.py   Day 5 dataset from pseudo-labels
    train.py                Day 5 fine-tuning
    day5_evaluate.py        Day 5 threshold sweep and comparison
    video_pipeline.py       Day 6 video pipeline (species + person, alerts, CSV log)
    day7_videos.py          Day 7 prototype vs pretrained on test clips
    make_report.py, make_week1_report.py   PDF reports
  requirements.txt
```

## Tech stack (from project proposal)

YOLOv11, OpenCV, ByteTrack, Python, FastAPI, React.js, TailwindCSS,
Chart.js, Firebase Firestore, EmailJS, YAMNet, Librosa. Training on
Google Colab, deployment on Vercel + Render.
