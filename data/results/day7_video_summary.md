## Pretrained vs prototype on the test clips (conf >= 0.25, frame every 0.5s)

Each cell: frames with the correct label / frames with a wrong species label / frames with a false person.

| Clip | expected | frames | pretrained OIV7 | prototype | prototype labels (count) |
|---|---|---|---|---|---|
| boar_berlin | wild_boar | 22 | 0 / 0 / 0 | 1 / 4 / 0 | mugger (4), wild_boar (1) |
| boar_bulgaria | wild_boar | 21 | 0 / 6 / 0 | 1 / 0 / 1 | person (1), wild_boar (1) |
| camtrap_general | none | 20 | 0 / 20 / 0 | 0 / 19 / 0 | nilgai (38), indian_peafowl (6) |
| camtrap_jaguarundi | none | 30 | 0 / 6 / 0 | 0 / 7 / 0 | indian_peafowl (7), wild_boar (1) |
| crocodile_nile | mugger | 42 | 0 / 3 / 7 | 0 / 3 / 9 | person (13), striped_hyena (4) |
| gazelle_hluhluwe | chinkara | 46 | 46 / 39 / 0 | 0 / 46 / 0 | nilgai (46) |
| human_hiking | person | 50 | 48 / 3 / 0 | 46 / 3 / 0 | person (81), wild_boar (3) |
| hyena_spotted | striped_hyena | 7 | 0 / 7 / 0 | 6 / 1 / 0 | striped_hyena (6), wild_boar (1) |
| jackals | golden_jackal | 49 | 19 / 45 / 0 | 27 / 35 / 0 | nilgai (81), golden_jackal (37), chinkara (7) |
| leopard_india | leopard | 31 | 0 / 31 / 0 | 31 / 2 / 1 | leopard (31), wild_boar (2), person (1) |
| leopard_tree | leopard | 18 | 0 / 2 / 0 | 12 / 0 / 0 | leopard (15) |
| nilgai_zoo | nilgai | 42 | 0 / 20 / 0 | 20 / 7 / 9 | nilgai (21), person (9), wild_boar (5) |
| peafowl_running | indian_peafowl | 46 | 6 / 1 / 0 | 0 / 44 / 0 | nilgai (95) |
| peafowl_walking | indian_peafowl | 30 | 30 / 0 / 0 | 28 / 15 / 0 | indian_peafowl (29), mugger (15) |