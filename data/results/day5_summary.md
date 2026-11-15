## Fine-tuned model on the validation split (63 images, 76 boxes)

### Box-level precision / recall vs confidence threshold (IoU >= 0.5)

| conf | precision | recall | F1 |
|---|---|---|---|
| 0.10 | 0.66 | 0.67 | 0.67 |
| 0.20 | 0.72 | 0.62 | 0.67 |
| 0.25 | 0.75 | 0.62 | 0.68 |
| 0.30 | 0.75 | 0.62 | 0.68 |
| 0.40 | 0.77 | 0.61 | 0.68 |
| 0.50 | 0.75 | 0.53 | 0.62 |
| 0.60 | 0.81 | 0.51 | 0.63 |
| 0.70 | 0.87 | 0.45 | 0.59 |

Best F1 at conf = **0.40** -> chosen operating threshold.

### Per species at conf = 0.40

| Species | GT boxes | precision | recall | F1 |
|---|---|---|---|---|
| leopard | 9 | 0.75 | 0.67 | 0.71 |
| chinkara | 13 | 0.73 | 0.62 | 0.67 |
| wild_boar | 5 | 1.00 | 0.20 | 0.33 |
| striped_hyena | 8 | 0.80 | 1.00 | 0.89 |
| golden_jackal | 6 | 1.00 | 0.33 | 0.50 |
| indian_peafowl | 14 | 0.80 | 0.57 | 0.67 |
| nilgai | 13 | 0.67 | 0.62 | 0.64 |
| mugger | 8 | 0.83 | 0.62 | 0.71 |

### Exact species hit rate on the same validation images (conf >= 0.25)

| Species | images | pretrained OIV7 (Day 3) | fine-tuned |
|---|---|---|---|
| leopard | 8 | 1 (12%) | 7 (88%) |
| chinkara | 10 | 3 (30%) | 8 (80%) |
| wild_boar | 4 | 2 (50%) | 2 (50%) |
| striped_hyena | 7 | 0 (0%) | 7 (100%) |
| golden_jackal | 6 | 1 (17%) | 2 (33%) |
| indian_peafowl | 11 | 11 (100%) | 8 (73%) |
| nilgai | 10 | 1 (10%) | 8 (80%) |
| mugger | 7 | 7 (100%) | 6 (86%) |
| **all** | 63 | 26 (41%) | 48 (76%) |