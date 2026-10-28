## Fine-tuned model on the validation split (63 images, 76 boxes)

### Box-level precision / recall vs confidence threshold (IoU >= 0.5)

| conf | precision | recall | F1 |
|---|---|---|---|
| 0.10 | 0.54 | 0.70 | 0.61 |
| 0.20 | 0.62 | 0.63 | 0.63 |
| 0.25 | 0.67 | 0.61 | 0.63 |
| 0.30 | 0.68 | 0.59 | 0.63 |
| 0.40 | 0.71 | 0.55 | 0.62 |
| 0.50 | 0.74 | 0.51 | 0.60 |
| 0.60 | 0.77 | 0.49 | 0.60 |
| 0.70 | 0.80 | 0.47 | 0.60 |

Best F1 at conf = **0.25** -> chosen operating threshold.

### Per species at conf = 0.25

| Species | GT boxes | precision | recall | F1 |
|---|---|---|---|---|
| leopard | 9 | 0.67 | 0.67 | 0.67 |
| chinkara | 13 | 0.78 | 0.54 | 0.64 |
| wild_boar | 5 | 0.50 | 0.40 | 0.44 |
| striped_hyena | 8 | 0.43 | 0.38 | 0.40 |
| golden_jackal | 6 | 1.00 | 0.83 | 0.91 |
| indian_peafowl | 14 | 0.64 | 0.64 | 0.64 |
| nilgai | 13 | 0.64 | 0.54 | 0.58 |
| mugger | 8 | 0.70 | 0.88 | 0.78 |

### Exact species hit rate on the same validation images (conf >= 0.25)

| Species | images | pretrained OIV7 (Day 3) | fine-tuned |
|---|---|---|---|
| leopard | 8 | 1 (12%) | 7 (88%) |
| chinkara | 10 | 3 (30%) | 7 (70%) |
| wild_boar | 4 | 2 (50%) | 2 (50%) |
| striped_hyena | 7 | 0 (0%) | 4 (57%) |
| golden_jackal | 6 | 1 (17%) | 5 (83%) |
| indian_peafowl | 11 | 11 (100%) | 8 (73%) |
| nilgai | 10 | 1 (10%) | 7 (70%) |
| mugger | 7 | 7 (100%) | 7 (100%) |
| **all** | 63 | 26 (41%) | 47 (75%) |