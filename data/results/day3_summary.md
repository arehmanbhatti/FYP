## Outcome per species at conf >= 0.25

| Species | n | exact | family | generic | wrong | none | mean conf (exact) |
|---|---|---|---|---|---|---|---|
| leopard | 60 | 6 | 31 | 3 | 4 | 16 | 0.43 |
| chinkara | 60 | 20 | 31 | 1 | 1 | 7 | 0.66 |
| wild_boar | 60 | 8 | 0 | 10 | 10 | 32 | 0.53 |
| striped_hyena | 60 | 0 | 25 | 12 | 14 | 9 | - |
| golden_jackal | 60 | 6 | 22 | 3 | 14 | 15 | 0.44 |
| indian_peafowl | 60 | 54 | 0 | 0 | 0 | 6 | 0.61 |
| nilgai | 60 | 7 | 38 | 6 | 2 | 7 | 0.51 |
| mugger | 60 | 36 | 0 | 0 | 0 | 24 | 0.67 |

## Exact-class hit rate vs threshold (% of images)

| Species | 0.1 | 0.25 | 0.3 | 0.5 | 0.7 |
|---|---|---|---|---|---|
| leopard | 10% | 10% | 10% | 2% | 0% |
| chinkara | 33% | 33% | 33% | 32% | 13% |
| wild_boar | 15% | 13% | 12% | 7% | 3% |
| striped_hyena | 0% | 0% | 0% | 0% | 0% |
| golden_jackal | 13% | 10% | 7% | 3% | 2% |
| indian_peafowl | 92% | 90% | 87% | 68% | 30% |
| nilgai | 13% | 12% | 12% | 5% | 2% |
| mugger | 67% | 60% | 55% | 43% | 30% |

## Any plausible (exact + family) rate vs threshold (% of images)

| Species | 0.1 | 0.25 | 0.3 | 0.5 | 0.7 |
|---|---|---|---|---|---|
| leopard | 65% | 62% | 58% | 23% | 5% |
| chinkara | 85% | 85% | 83% | 78% | 20% |
| wild_boar | 15% | 13% | 12% | 7% | 3% |
| striped_hyena | 45% | 42% | 38% | 22% | 8% |
| golden_jackal | 52% | 47% | 42% | 27% | 17% |
| indian_peafowl | 92% | 90% | 87% | 68% | 30% |
| nilgai | 77% | 75% | 70% | 40% | 8% |
| mugger | 67% | 60% | 55% | 43% | 30% |

## False detections at conf >= 0.25 (per detection)

| Species | wrong animal class | human | background objects |
|---|---|---|---|
| leopard | Owl (3), Squirrel (1), Carnivore (1) | Person (1), Human face (1) | Tree (30), Plant (17), Mobile phone (1), Flowerpot (1) |
| chinkara | Cattle (1), Kangaroo (1) | - | Plant (19), Tree (18), Skull (2), Grape (1) |
| wild_boar | Dog (3), Raccoon (2), Snake (2), Bull (1), Fox (1) | Man (1) | Plant (71), Tree (17), Flower (3), Insect (2), Mushroom (2) |
| striped_hyena | Brown bear (7), Lion (5), Raccoon (2), Cheetah (2), Deer (1) | - | Plant (21), Tree (7) |
| golden_jackal | Kangaroo (5), Deer (4), Squirrel (3), Cat (1), Pig (1) | - | Plant (16), Tree (10), Ruler (1), Street light (1) |
| indian_peafowl | Ostrich (1), Turkey (1), Parrot (1) | - | Tree (30), Plant (18), Flower (4), Wheel (3), Window (3) |
| nilgai | Rhinoceros (1), Kangaroo (1), Koala (1) | - | Tree (36), Plant (14), Palm tree (1) |
| mugger | Bird (2) | - | Plant (24), Tree (13), Flower (11), Insect (1) |