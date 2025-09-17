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
            "effects": {"trust": +10, "police_gap": +3},
            "next": "cinematic_to_garage"
        },
         # ---------------------------------

        "announce_follow_direction_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à John.",
            "next": "direction_follow_harm_effects"
        },
        "direction_follow_harm_effects": {
            "type": "effects",
            # follow harmful: decrease trust and decrease police gap
            "effects": {"trust": -10, "police_gap": -3},
            "next": "cinematic_to_police"
        },

        # ---------------------------------

        "announce_ignore_direction_help": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à John.",
            "next": "direction_ignore_helpful_effects"
        },
        "direction_ignore_helpful_effects": {
            "type": "effects",
            # ignore helpful: decrease trust but still get to safety
            "effects": {"trust": -5, "police_gap": +1},
            "next": "cinematic_wander_then_garage"
        },
         # ---------------------------------

        "announce_ignore_direction_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à John.",
            "next": "direction_ignore_harm_effects"
        },
        "direction_ignore_harm_effects": {
            "type": "effects",
            # ignore harmful: increase trust and get to safety
            "effects": {"trust": +5, "police_gap": +2},
            "next": "cinematic_to_garage"
        },

        # --- Cinematics ---
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

        # Police encounter (bad path)
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
            "effects": {"trust": -15, "police_gap": -5},
            "next": "cinematic_escape_police"
        },

        "cinematic_escape_police": {
            "type": "wait_scene",
            "event": "escape_to_garage",
            "next": "escape_tense"
        },

        # ---- Different endings ----
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
                "Bon, je prends la caisse quand même...",
                "Heureusement que j'ai appris à casser des vitres de voitures."
            ],
            "next": "escape_car"
        },

        "escape_car": {
            "type": "wait_scene",
            "event": "drive_away",
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