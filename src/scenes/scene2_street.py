SCENE2_STREET = {
    "id": "street_room",
    "start": "intro_1",
    "nodes": {
        # ---- Intro until the crossroads ----
        "intro_1": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ("Tony sort de la banque. L'allée est sombre, les sirènes se rapprochent. "
                     "Soudain, une silhouette apparaît, un homme."),
            "next": "radio_1"
        },
        "radio_1": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Qui… qui êtes-vous ? Faites comme si je n'étais pas là."
                "Je dois passer. Vite."
            ],
            "next": "radio_2"
        },
        "radio_2": {
            "type": "line",
            "speaker": "John",
            "text": [
                "Calmez-vous. Je peux sûrement vous aider à fuir plus vite.",
                "Je sais ce qui se trouve dans les alentours"
            ],
            "next": "choice_direction_0"
        },

        # ---- Choice about the direction (single-line menu) ----
        "choice_direction_0": {
            "type": "choice",
            "prompt": "Quelle direction conseiller ?",
            "options": [
                { "id": "direction_right", "label": "À droite (vers le garage)",  "correct": True  },   # helpful
                { "id": "direction_left",  "label": "À gauche (vers la police)",  "correct": False }   # harmful
            ],
            "next": "branch_direction_lines"
        },

        # Branch to separate lines depending on player's answer
        "branch_direction_lines": {
            "type": "branch_choice_correct",
            "if_correct": "john_direction_right",
            "if_wrong":   "john_direction_left"
        },

        # John speaks (RIGHT branch - helpful)
        "john_direction_right": {
            "type": "line",
            "speaker": "John",
            "text": [
                "Tournez à droite, il y a un garage ! Dépêchez-vous.",
                "Vous y trouverez ma voiture avec la clé dessous."
            ],
            "next": "decide_direction"
        },

        # John speaks (LEFT branch - harmful)
        "john_direction_left": {
            "type": "line",
            "speaker": "John",
            "text": [
                "Allez à gauche, c'est plus sûr ! Vous pourrez vous échapper par là.",
                "Je peux vous assurer que vous allez les semer."
            ],
            "next": "decide_direction"
        },

        # Deterministic follow/ignore based on trust (>=60 = follow)
        "decide_direction": {
            "type": "decision_follow",
            "if_follow_and_correct": "announce_follow_direction_help",
            "if_follow_and_wrong":   "announce_follow_direction_harm",
            "if_ignore_and_correct": "announce_ignore_direction_help",
            "if_ignore_and_wrong":   "announce_ignore_direction_harm"
        },

        # --- Announce then effects + cinematics for DIRECTION stage ---
        "announce_follow_direction_help": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à John.",
            "next": "direction_follow_helpful_effects"
        },
        "direction_follow_helpful_effects": {
            "type": "effects",
            # follow helpful: increase trust and police gap
            "effects": {"trust": +8, "police_gap": +3},
            "next": "cinematic_to_garage"
        },

        "announce_follow_direction_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à John.",
            "next": "direction_follow_harm_effects"
        },
        "direction_follow_harm_effects": {
            "type": "effects",
            # follow harmful: decrease trust and decrease police gap
            "effects": {"trust": -14, "police_gap": -3},
            # NEW chain (suggest WRONG + Tony follows = goes LEFT first, sees cops, bolts RIGHT & UP)
            "next": "cinematic_follow_wrong_down"
        },

        "announce_ignore_direction_help": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à John.",
            "next": "direction_ignore_helpful_effects"
        },
        "direction_ignore_helpful_effects": {
            "type": "effects",
            # ignore helpful: Tony goes opposite way first (to the LEFT), then flees to the GARAGE
            "effects": {"trust": +6, "police_gap": -1},
            "next": "cinematic_ignore_help_part1"
        },

        "announce_ignore_direction_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à John.",
            "next": "direction_ignore_harm_effects"
        },
        "direction_ignore_harm_effects": {
            "type": "effects",
            # ignore harmful 
            "effects": {"trust": -8, "police_gap": +2},
            "next": "cinematic_ignore_wrong_part1"
        },

        # --- Cinematics (shared) ---
        "cinematic_to_garage": {
            "type": "wait_scene",
            "event": "go_to_garage",
            "next": "escape_success"
        },
        "cinematic_wander_then_garage": {
            "type": "wait_scene",
            "event": "wander_then_garage",
            "next": "escape_tense"
        },
        "cinematic_to_police": {
            "type": "wait_scene",
            "event": "go_to_police",
            "next": "police_encounter"
        },

        # -------- Bad path encounter (generic) --------
        "police_encounter": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Putain ! LES FLICS !!",
                "Ce John ne s'en sortira pas comme ça !"
            ],
            "next": "police_chase"
        },
        "police_chase": {
            "type": "line",
            "speaker": "Tony",
            "text": "Je dois me dépêcher de retourner vers le garage ARGHH CE JOHN!",
            "next": "police_chase_effects"
        },
        "police_chase_effects": {
            "type": "effects",
            "effects": {"trust": -0, "police_gap": -0},
            "next": "cinematic_escape_police"
        },
        "cinematic_escape_police": {
            "type": "wait_scene",
            "event": "escape_to_garage",
            "next": "escape_tense"
        },

        # ---- Right-when-ignored (already present) ----
        "cinematic_ignore_wrong_part1": {
            "type": "wait_scene",
            "event": "garage_ignore_wrong_part1",
            "next": "tony_spots_lights"
        },
        "tony_spots_lights": {
            "type": "line",
            "speaker": "Tony",
            "text": "Mais il m'a pris pour un con lui, on voit les lumières à gauche. Mieux vaut tenter mon coup dans le garage, on sait jamais, je peux trouver une voiture !",
            "next": "cinematic_ignore_wrong_part2"
        },
        "cinematic_ignore_wrong_part2": {
            "type": "wait_scene",
            "event": "garage_ignore_wrong_part2",
            "next": "tony_found_car"
        },
        "tony_found_car": {
            "type": "line",
            "speaker": "Tony",
            "text": "Parfait une voiture !",
            "next": "escape_tense"
        },

        # ---- Ignore helpful (we suggested RIGHT, Tony went LEFT first) ----
        "cinematic_ignore_help_part1": {
            "type": "wait_scene",
            "event": "garage_ignore_wrong_part1",   # down to y=400
            "next": "tony_defies_stranger"
        },
        "tony_defies_stranger": {
            "type": "line",
            "speaker": "Tony",
            "text": "Mais il m'a pris pour un con lui, il croit vraimenet que je vais faire confiance à un inconnu ? Il me demande d'aller au garage, je vais à l'opposer",
            "next": "cinematic_ignore_help_left"
        },
        "cinematic_ignore_help_left": {
            "type": "wait_scene",
            "event": "ignore_help_go_left",         # left to x=290
            "next": "tony_police_spotted"
        },
        "tony_police_spotted": {
            "type": "line",
            "speaker": "Tony",
            "text": "Putain ! LES FLICS !!",
            "next": "cinematic_ignore_help_right_up"
        },
        "cinematic_ignore_help_right_up": {
            "type": "wait_scene",
            "event": "ignore_help_escape_right_up", # right FAST to x=890, then up to y=231
            "next": "tony_found_keys"
        },
        "tony_found_keys": {
            "type": "line",
            "speaker": "Tony",
            "text": "Parfait des clés de voiture !",
            "next": "escape_car_then_why"
        },

        # ---- NEW: Follow WRONG (we suggested LEFT, Tony trusts and goes LEFT first) ----
        "cinematic_follow_wrong_down": {
            "type": "wait_scene",
            "event": "garage_ignore_wrong_part1",   # down to y=400
            "next": "cinematic_follow_wrong_left"
        },
        "cinematic_follow_wrong_left": {
            "type": "wait_scene",
            "event": "ignore_help_go_left",         # left to x=290
            "next": "police_encounter_fw"
        },
        "police_encounter_fw": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Putain ! LES FLICS !!",
                "Ce John ne s'en sortira pas comme ça !"
            ],
            "next": "cinematic_follow_wrong_right"
        },
        "cinematic_follow_wrong_right": {
            "type": "wait_scene",
            "event": "ignore_help_escape_right",    # right FAST to x=890 (stop there)
            "next": "tony_spots_garage_hide"
        },
        "tony_spots_garage_hide": {
            "type": "line",
            "speaker": "Tony",
            "text": "Un garage ! parfait, heureusement que je sais volé une voiture !",
            "next": "cinematic_follow_wrong_up"
        },
        "cinematic_follow_wrong_up": {
            "type": "wait_scene",
            "event": "ignore_help_up",              # face up, then up to y=231
            "next": "escape_car_then_memory"
        },

        # ---- Different endings (shared) ----
        "escape_success": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "HOP, clé trouvée. Allez, je me tire d'ici !",
                "Ce John ne me l'a pas mise à l'envers..."
            ],
            "next": "escape_car"
        },
        "escape_tense": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Bon, je prends la caisse ...",
                "Heureusement que j'ai appris à casser des vitres de voitures."
            ],
            "next": "escape_car"
        },

        # Shared escape (used by success & tense)
        "escape_car": {
            "type": "wait_scene",
            "event": "drive_away",
            "next": "tony_final_response"
        },

        # Escape + epilogue beats (branches that want extra line after driving away)
        "escape_car_then_why": {
            "type": "wait_scene",
            "event": "drive_away",
            "next": "tony_why_helped"
        },
        "tony_why_helped": {
            "type": "line",
            "speaker": "Tony",
            "text": "Pourquoi il m'a aidé ?",
            "next": "tony_final_response"
        },

        "escape_car_then_memory": {
            "type": "wait_scene",
            "event": "drive_away",
            "next": "tony_memory_line"
        },
        "tony_memory_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "Je ne sais pas qui t'es mais, je m'en rappelerai ... ",
            "next": "tony_final_response"
        },

        # ---- Final ----
        "tony_final_response": {
            "type": "line",
            "speaker": "Tony",
            "text": "Pour l'instant, je les ai semé... On verra le reste.",
            "next": "end"
        },
        "end": { "type": "end" }
    }
}