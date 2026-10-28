## Pretrained vs prototype on the test clips (conf >= 0.25, frame every 0.5s)

Each cell: frames with the correct label / frames with a wrong species label / frames with a false person.

| Clip | expected | frames | pretrained OIV7 | prototype | prototype labels (count) |
|---|---|---|---|---|---|
| boar_berlin | wild_boar | 22 | 0 / 0 / 0 | 0 / 0 / 0 | - |
| boar_bulgaria | wild_boar | 21 | 0 / 6 / 0 | 0 / 0 / 1 | person (1) |
| camtrap_general | none | 20 | 0 / 20 / 0 | 0 / 20 / 0 | nilgai (31), wild_boar (10) |
| camtrap_jaguarundi | none | 30 | 0 / 6 / 0 | 0 / 10 / 0 | wild_boar (8), leopard (5) |
| crocodile_nile | mugger | 42 | 0 / 3 / 7 | 0 / 0 / 9 | person (13) |
| gazelle_hluhluwe | chinkara | 46 | 46 / 39 / 0 | 11 / 42 / 1 | golden_jackal (29), nilgai (14), chinkara (14) |
| human_hiking | person | 50 | 48 / 3 / 0 | 45 / 8 / 0 | person (83), wild_boar (6), indian_peafowl (2) |
| hyena_spotted | striped_hyena | 7 | 0 / 7 / 0 | 7 / 0 / 0 | striped_hyena (7) |
| jackals | golden_jackal | 49 | 19 / 45 / 0 | 38 / 35 / 0 | chinkara (63), golden_jackal (56), nilgai (14) |
| leopard_india | leopard | 31 | 0 / 31 / 0 | 28 / 0 / 1 | leopard (28), person (1) |
| leopard_tree | leopard | 18 | 0 / 2 / 0 | 9 / 0 / 0 | leopard (9) |
| nilgai_zoo | nilgai | 42 | 0 / 20 / 0 | 0 / 26 / 9 | wild_boar (26), person (9) |
| peafowl_running | indian_peafowl | 46 | 6 / 1 / 0 | 0 / 44 / 0 | nilgai (102), wild_boar (37) |
| peafowl_walking | indian_peafowl | 30 | 30 / 0 / 0 | 30 / 0 / 0 | indian_peafowl (33) |