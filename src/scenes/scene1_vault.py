SCENE1_VAULT = {
    "id": "vault_room",
    "start": "intro_1",
    "nodes": {
        # ---- Intro until the door ----
        "intro_1": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ("Banque. Le braquage a mal tourné. Les sirènes hurlent. "
                     "Tony est blessé, plongé dans le noir. Dans son oreillette : Lukas, flic corrompu."),
            "next": "radio_1"
        },
        "radio_1": {
            "type": "line",
            "speaker": "Lukas",
            "text": [
                "Tony, ils sont à tes trousses. Faut bouger, maintenant."
            ],
            "next": "radio_2"
        },
        "radio_2": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "J’me suis fait tirer par un putain de garde.",
                "J’ai laissé tomber ma trousse de secours, mais je vois rien bordel !",
            ],
            "next": "choice_button_0"
        },

        # ---- Choice about the medkit (single-line menu) ----
        "choice_button_0": {
            "type": "choice",
            "prompt": "Tu la vois ou pas ?",
            "options": [
                { "id": "medicine_yes", "label": "Oui",  "correct": True  },   # helpful
                { "id": "medicine_no",  "label": "Non",  "correct": False }   # harmful
            ],
            "next": "branch_medkit_lines"
        },

        # Branch to separate lines depending on player's answer
        "branch_medkit_lines": {
            "type": "branch_choice_correct",
            "if_correct": "lucas_medkit_yes",
            "if_wrong":   "lucas_medkit_no"
        },

        # Lukas speaks (YES branch)
        "lucas_medkit_yes": {
            "type": "line",
            "speaker": "Lukas",
            "text": [
                "Attends…",
                "Oui, je la vois ! Juste à ta droite !"
            ],
            "next": "announce_follow_medkit_help"
        },

        # Lukas speaks (NO branch)
        "lucas_medkit_no": {
            "type": "line",
            "speaker": "Lukas",
            "text": [
                "Laisse tomber la trousse. File à la porte !"
            ],
            "next": "announce_follow_medkit_harm"
        },

        # Deterministic follow/ignore based on trust (>=60 = follow)
        "decide_medkit": {
            "type": "decision_follow",
            "if_follow_and_correct": "announce_follow_medkit_help",
            "if_follow_and_wrong":   "announce_follow_medkit_harm",
            "if_ignore_and_correct": "announce_ignore_medkit_help",
            "if_ignore_and_wrong":   "announce_ignore_medkit_harm"
        },

        # --- Announce then effects + cinematics for MEDKIT stage ---
        "announce_follow_medkit_help": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à Lucas.",
            "next": "med_follow_helpful_effects"
        },
        "med_follow_helpful_effects": {
            "type": "effects",
            # follow helpful: increase trust and police gap
            "effects": {"trust": +6, "police_gap": +2},
            "next": "cinematic_to_kit"
        },

        "announce_follow_medkit_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à Lucas.",
            "next": "med_follow_harm_effects"
        },
        "med_follow_harm_effects": {
            "type": "effects",
            # follow harmful: decrease trust and increase police gap
            "effects": {"trust": -6, "police_gap": +2},
            "next": "cinematic_stop_near_medkit"
        },

        # NEW: stop well before medkit, yell, THEN go pick it up like the helpful path, THEN go to door
        "cinematic_stop_near_medkit": {
            "type": "wait_scene",
            "event": "go_near_medkit_pause",
            "next": "tony_yells_seen_medkit"
        },
        "tony_yells_seen_medkit": {
            "type": "line",
            "speaker": "Tony",
            "text": "LUCAS ENFOIRÉ DE MERDE TU LA VOIS PAS ALOS QU'ELLE EST SUR MON CHEMIN !!",
            "next": "cinematic_pick_medkit_after_yell"
        },
        "cinematic_pick_medkit_after_yell": {
            "type": "wait_scene",
            "event": "go_to_medkit",
            "next": "cinematic_to_door"
        },

        "announce_ignore_medkit_help": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à Lucas.",
            "next": "med_ignore_helpful_effects"
        },
        "med_ignore_helpful_effects": {
            "type": "effects",
            # ignore helpful: decrease trust and increase police gap
            "effects": {"trust": -4, "police_gap": +2},
            "next": "cinematic_to_door"
        },

        "announce_ignore_medkit_harm": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à Lucas.",
            "next": "med_ignore_harm_effects"
        },
        "med_ignore_harm_effects": {
            "type": "effects",
            # ignore harmful: heavily decrease trust and decrease police gap
            "effects": {"trust": -10, "police_gap": -2},
            "next": "cinematic_wander_medkit"
        },

        # --- Cinematics ---
        "cinematic_to_kit": {
            "type": "wait_scene",
            "event": "go_to_medkit",
            "next": "tony_moves"
        },
        "cinematic_wander_medkit": {
            "type": "wait_scene",
            "event": "wander_then_medkit",
            "next": "tony_moves"
        },
        "cinematic_to_door": {
            "type": "wait_scene",
            "event": "go_to_door",
            "next": "tony_moves"
        },

        # Tony reaches the door area
        "tony_moves": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Ok, j’avance.",
                "…Deux boutons sur la porte. Aucun marquage.",
                "J’appuie sur lequel ?"
            ],
            "next": "choice_button"
        },

        # ---- Door buttons choice (player's advice) ----
        "choice_button": {
            "type": "choice",
            "prompt": "Quel bouton indiquer à Tony ?",
            "options": [
                {"id": "trap_left",  "label": "GAUCHE (rouge)",  "correct": False},  # red = wrong
                {"id": "help_right", "label": "DROITE (verte)",  "correct": True}    # green = opens
            ],
            "next": "decide_buttons"
        },

        # Deterministic follow/ignore based on trust, then announce
        "decide_buttons": {
            "type": "decision_follow",
            "if_follow_and_correct": "announce_follow_buttons_ok",
            "if_follow_and_wrong":   "announce_follow_buttons_bad",
            "if_ignore_and_correct": "announce_ignore_buttons_right",
            "if_ignore_and_wrong":   "announce_ignore_buttons_wrong"
        },

        # --- FOLLOW & CORRECT ---
        "announce_follow_buttons_ok": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à Lucas.",
            "next": "follow_ok_effects"
        },
        "follow_ok_effects": {
            "type": "effects",
            "effects": {"trust": +8, "police_gap": +2},
            "next": "press_green_then_follow_ok"
        },
        "press_green_then_follow_ok": {
            "type": "wait_scene",
            "event": "press_green_open",
            "next": "follow_ok_line"
        },
        "follow_ok_line": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "*BIP* …Ça s’ouvre !",
                "Oh, c’était moins une."
            ],
            "next": "exit_line"
        },

        # --- FOLLOW & WRONG (press RED, wait 1s, narrator, harsh line, then GREEN) ---
        "announce_follow_buttons_bad": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony fait confiance à Lucas.",
            "next": "follow_bad_effects"
        },
        "follow_bad_effects": {
            "type": "effects",
            "effects": {"trust": -10, "police_gap": -2},
            "next": "press_red_then_pause"
        },
        "press_red_then_pause": {
            "type": "wait_scene",
            "event": "press_red_wait",
            "next": "narrator_red_nothing_follow"
        },
        "narrator_red_nothing_follow": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "*Rien ne se passe.*",
            "next": "tony_harsh_line"
        },
        "tony_harsh_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "…Je me rappellerai de ça, Lucas. Passe le bonsoir à ta femme et tes enfants.",
            "next": "press_green_to_open_after_red_follow"
        },
        "press_green_to_open_after_red_follow": {
            "type": "wait_scene",
            "event": "press_green_open",
            "next": "exit_line"
        },

        # --- IGNORE & CORRECT (Tony presses RED first, then GREEN with 'Ok ok') ---
        "announce_ignore_buttons_right": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à Lucas.",
            "next": "ignore_right_effects"
        },
        "ignore_right_effects": {
            "type": "effects",
            "effects": {"trust": +3, "police_gap": -2},
            "next": "press_red_then_pause_ignore_right"
        },
        "press_red_then_pause_ignore_right": {
            "type": "wait_scene",
            "event": "press_red_wait",
            "next": "narrator_red_nothing_ignore_right"
        },
        "narrator_red_nothing_ignore_right": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "*Rien ne se passe.*",
            "next": "tony_okok_green"
        },
        "tony_okok_green": {
            "type": "line",
            "speaker": "Tony",
            "text": "Ok ok, la verte… voilà !",
            "next": "press_green_to_open_after_red_ignore_right"
        },
        "press_green_to_open_after_red_ignore_right": {
            "type": "wait_scene",
            "event": "press_green_open",
            "next": "exit_line"
        },

        # --- IGNORE & WRONG (Tony goes directly to GREEN, then harsh line) ---
        "announce_ignore_buttons_wrong": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony ne fait pas confiance à Lucas.",
            "next": "ignore_wrong_effects"
        },
        "ignore_wrong_effects": {
            "type": "effects",
            "effects": {"trust": -6, "police_gap": +2},
            "next": "press_green_after_ignore_wrong"
        },
        "press_green_after_ignore_wrong": {
            "type": "wait_scene",
            "event": "press_green_open",
            "next": "ignore_wrong_line"
        },
        "ignore_wrong_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "…Je me rappellerai de ça, Lucas. Passe le bonsoir à ta femme et tes enfants.",
            "next": "exit_line"
        },

        # ---- Exit ----
        "exit_line": {
            "type": "line",
            "speaker": "Lucas",
            "text": "...",
            "next": "end"
        },
        "end": { "type": "end" }
    }
}