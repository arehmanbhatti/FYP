## Species models on the v2 held-out test split

Test split: 269 animal photos (341 boxes) and 248 negative images. 47 test images that v1 had already seen were left out. Threshold for each model chosen on the v2 validation split.

| Model | conf (from val) | mAP@50 | mAP@50-95 | precision | recall | F1 | exact-species hit | false alarm on negatives | recall on synthetic IR |
|---|---|---|---|---|---|---|---|---|---|
| v1 (Week 1, YOLO11n) | 0.50 | 0.439 | 0.317 | 0.77 | 0.50 | 0.60 | 62% | 49% (121/248) | 0.29 |
| v2 (YOLO11n) | 0.40 | 0.791 | 0.613 | 0.91 | 0.70 | 0.79 | 81% | 17% (41/248) | 0.59 |
| v2 (YOLO12n) | 0.50 | 0.757 | 0.586 | 0.94 | 0.66 | 0.78 | 75% | 8% (19/248) | 0.54 |

exact-species hit = share of test photos where the right species is named at the chosen conf. false alarm = share of negative images (no target species) that get any species box. Synthetic IR = the same test photos made grayscale, dark and noisy.

### Per species (test split): precision / recall / recall on synthetic IR

| Species | v1 (Week 1, YOLO11n) | v2 (YOLO11n) | v2 (YOLO12n) |
|---|---|---|---|
| leopard | 0.82 / 0.68 / 0.50 | 0.88 / 0.90 / 0.88 | 0.97 / 0.88 / 0.72 |
| chinkara | 0.95 / 0.56 / 0.20 | 0.92 / 0.63 / 0.59 | 0.98 / 0.62 / 0.58 |
| wild_boar | 0.50 / 0.23 / 0.19 | 0.86 / 0.61 / 0.61 | 0.83 / 0.48 / 0.35 |
| striped_hyena | 0.68 / 0.41 / 0.43 | 0.97 / 0.81 / 0.78 | 0.97 / 0.86 / 0.84 |
| golden_jackal | 0.67 / 0.24 / 0.03 | 0.78 / 0.55 / 0.30 | 0.82 / 0.42 / 0.30 |
| indian_peafowl | 0.62 / 0.52 / 0.31 | 0.94 / 0.65 / 0.46 | 0.93 / 0.58 / 0.46 |
| nilgai | 0.81 / 0.64 / 0.35 | 0.97 / 0.67 / 0.55 | 0.95 / 0.71 / 0.53 |
| mugger | 0.92 / 0.46 / 0.31 | 0.92 / 0.85 / 0.58 | 0.95 / 0.69 / 0.46 |

### False alarms by negative type (images with any species box / images)

| Negative type | v1 (Week 1, YOLO11n) | v2 (YOLO11n) | v2 (YOLO12n) |
|---|---|---|---|
| confuser animals | 104 / 187 | 39 / 187 | 19 / 187 |
| empty habitat scenes | 9 / 41 | 2 / 41 | 0 / 41 |
| people / everyday (COCO128) | 8 / 20 | 0 / 20 | 0 / 20 |
