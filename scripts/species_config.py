"""
Day 2 - candidate target species for the wildlife detector.
Shortlist is based on the fauna of Sindh / Pakistan (Kirthar, Thar, Indus
riparian belt) named in the project proposal, plus humans (poaching /
intrusion alerts).

'oiv7' is the closest Open Images V7 class the pretrained model already knows
(None = no matching class, needs fine-tuning).
"""

PLACE_ID_PAKISTAN = 7076  # iNaturalist place id

# key -> (scientific name, common name, closest OIV7 class or None)
CANDIDATES = {
    "leopard":        ("Panthera pardus",          "Leopard",           "Leopard"),
    "sindh_ibex":     ("Capra aegagrus",           "Sindh ibex",        "Goat"),
    "chinkara":       ("Gazella bennettii",        "Chinkara gazelle",  "Antelope"),
    "wild_boar":      ("Sus scrofa",               "Wild boar",         "Pig"),
    "striped_hyena":  ("Hyaena hyaena",            "Striped hyena",     None),
    "golden_jackal":  ("Canis aureus",             "Golden jackal",     "Dog"),
    "indian_peafowl": ("Pavo cristatus",           "Indian peafowl",    "Bird"),
    "nilgai":         ("Boselaphus tragocamelus",  "Nilgai",            "Antelope"),
    "urial":          ("Ovis vignei",              "Urial",             "Sheep"),
    "mugger":         ("Crocodylus palustris",     "Mugger crocodile",  "Crocodile"),
    "bengal_fox":     ("Vulpes bengalensis",       "Bengal fox",        "Fox"),
}
