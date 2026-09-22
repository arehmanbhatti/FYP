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
