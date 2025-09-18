# src/scenes/scene3_country_house.py

SCENE3_MARTHA = {
    "id": "martha_scene",
    "start": "intro_1",
    "nodes": {
        # ---- Intro ----
        "intro_1": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ["Depuis des heures, Tony roule sur les routes de campagne. ",
                     "Le jet privé décolle bientôt, mais la balle du flic l’a bien touché. ",
                     "Il recommence à perdre du sang.",
                     ],
            "next": "tony_intro"
        },
        "tony_intro": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Putain... je vais pas tenir. Je perds trop de sang... Faut que je m'arrête."
            ],
            "next": "house_arrival"
        },
        "house_arrival": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony s’arrête devant une maison isolée. Moteur coupé...",
            "next": "cinematic_arrival_top"
        },
        "cinematic_arrival_top": {
            "type": "wait_scene",
            "event": "arrival_from_top",
            "next": "tony_gets_out"
        },
        "tony_gets_out": {
            "type": "wait_scene",
            "event": "tony_exit_car",
            "next": "martha_comes_out"
        },
        "martha_comes_out": {
            "type": "wait_scene",
            "event": "martha_exit_house",
            "next": "martha_meets"
        },
        "martha_meets": {
            "type": "line",
            "speaker": "Martha",
            "text": [
                "Harold ? Harold, c’est toi ? Tu rentres bien tôt ce soir... Oh, excusez-moi, je croyais que c'était mon mari ! ",
                "Mon Dieu, vous êtes blessé !"
            ],
            "next": "tony_beg"
        },
        "tony_beg": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Ne vous inquiétez pas, c’est rien... juste une égratignure. ",
                "J’ai juste besoin de quelques heures pour me reposer, après je repartirai.",
            ],
            "next": "choice_martha"
        },

        # ---- Choice for Martha ----
        "choice_martha": {
            "type": "choice",
            "prompt": "Que proposez-vous à Tony ?",
            "options": [
                { "id": "living_room", "label": "Entrez, reposez-vous dans le salon", "correct": False },
                { "id": "cellar",      "label": "Je n'ai qu'une cabane à proposer",    "correct": True  },
                { "id": "leave",       "label": "Désolée, vous ne pouvez pas rester ici", "correct": "neutral" }
            ],
            "next": "branch_martha_lines"
        },

        # Branch depending on choice (immediate lines)
        "branch_martha_lines": {
            "type": "branch_choice_3way",
            "if_correct": "martha_cellar_line",
            "if_wrong":   "martha_living_line",
            "if_neutral": "martha_leave_line"
        },

        "martha_living_line": {
            "type": "line",
            "speaker": "Martha",
            "text": "Venez, le salon est là. Je vais chercher des pansements.",
            "next": "decide_sleep"
        },
        "martha_cellar_line": {
            "type": "line",
            "speaker": "Martha",
            "text": "Il y a une cabane un peu plus loin, personne ne vous y trouvera.",
            "next": "decide_sleep"
        },
        "martha_leave_line": {
            "type": "line",
            "speaker": "Martha",
            "text": "Désolée... vous ne pouvez pas rester ici.",
            "next": "leave_tony_nowhere"
        },
        "leave_tony_nowhere": {
            "type": "line",
            "speaker": "Tony",
            "text": "... Je comprends, mais je n'ai nulle part où aller...",
            "next": "ignore_effects_redirect"
        },

        # ---- Decision follow / ignore ----
        # If Tony trusts you (trust >= threshold), he follows your suggestion.
        # If he DOESN'T trust you (trust < threshold) and you suggested 1 or 2,
        # he overrides with choice 3 and we play the "mistrust" cinematic.
        "decide_sleep": {
            "type": "decision_follow_3way",
            "if_follow_correct": "follow_cellar",
            "if_follow_wrong":   "follow_living",
            "if_follow_neutral": "follow_leave",
            "if_ignore_correct": "ignore_start",   # NEW path
            "if_ignore_wrong":   "ignore_start",   # NEW path
            "if_ignore_neutral": "ignore_start"    # NEW path
        },

        # ---- FOLLOW BRANCH (Living room) ----
        "follow_living": {
            "type": "effects",
            "effects": {"trust": -14, "police_gap": -3},
            "next": "cin_martha_step_right"
        },
        "cin_martha_step_right": {
            "type": "wait_scene",
            "event": "martha_step_right",
            "next": "line_martha_invite"
        },
        "line_martha_invite": {
            "type": "line",
            "speaker": "Martha",
            "text": "Entrez donc, j'ai de quoi vous soigner.",
            "next": "line_tony_accept"
        },
        "line_tony_accept": {
            "type": "line",
            "speaker": "Tony",
            "text": "... Si vous le dites",
            "next": "cin_tony_enter_living"
        },
        "cin_tony_enter_living": {
            "type": "wait_scene",
            "event": "tony_enter_living",
            "next": "line_martha_thinks"
        },
        "line_martha_thinks": {
            "type": "line",
            "speaker": "Martha",
            "text": ["Je me demande quand Harold rentre, il m'a dit qu'il était à la poursuite d'un voleur. ", 
            "Le monde dans lequel on vit... À mon époque ...",
            ],
            "next": "cin_martha_back_home"
        },
        "cin_martha_back_home": {
            "type": "wait_scene",
            "event": "martha_back_home",
            "next": "cin_dark_sirens"
        },
        "cin_dark_sirens": {
            "type": "wait_scene",
            "event": "night_cut_with_sirens",
            "next": "line_narrator_wakeup"
        },
        "line_narrator_wakeup": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ["Tony se réveille quelques heures plus tard en sursaut. En entendant le bruit des sirènes, il se précipite pour fuir la maison. ",
             "En passant par le salon, il remarque un détail qu'il n'avait pas vu la veille à cause de la fatigue : le portrait d'un vieil homme en uniforme de police... Harold.",
            ],
            "next": "line_tony_mistrust"
        },
        "line_tony_mistrust": {
            "type": "line",
            "speaker": "Tony",
            "text": "Je le savais, je ne peux faire confiance qu'à moi-même !",
            "next": "end"
        },

        # ---- FOLLOW BRANCH (Cellar) ----
        "follow_cellar": {
            "type": "effects",
            "effects": {"trust": +10, "police_gap": +2},
            "next": "line_tony_ok_cellar"
        },
        "line_tony_ok_cellar": {
            "type": "line",
            "speaker": "Tony",
            "text": "(C'est l'endroit parfait pour me reposer et semer les flics !). Merci infiniment.",
            "next": "cin_cellar_tony_leave"
        },
        "cin_cellar_tony_leave": {
            "type": "wait_scene",
            "event": "cellar_tony_turn_disappear",
            "next": "cin_cellar_car_start_drive"
        },
        "cin_cellar_car_start_drive": {
            "type": "wait_scene",
            "event": "cellar_start_bg_drive",
            "next": "line_martha_thinks_cellar"
        },

        # Duplicate of the “thinks” line so we can branch differently for cellar path
        "line_martha_thinks_cellar": {
            "type": "line",
            "speaker": "Martha",
            "text": "Je me demande quand Harold rentre, il m'a dit qu'il était à la poursuite d'un voleur. Le monde dans lequel on vit... À mon époque...",
            "next": "cin_martha_back_home_cellar"
        },
        "cin_martha_back_home_cellar": {
            "type": "wait_scene",
            "event": "martha_back_home",
            "next": "cin_cellar_dark_sirens"
        },

        # Darken (while the car sequence can still be running), then sirens
        "cin_cellar_dark_sirens": {
            "type": "wait_scene",
            "event": "night_cut_with_sirens",
            "next": "line_cellar_narrator_wakeup"
        },
        "line_cellar_narrator_wakeup": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony se réveille quelques heures plus tard en sursaut. En entendant le bruit des sirènes, il se précipite et fuit en voiture.",
            "next": "line_tony_cellar_sirens"
        },
        "line_tony_cellar_sirens": {
            "type": "line",
            "speaker": "Tony",
            "text": "Le bruit venait du côté de la maison de la vieille... Heureusement que j'ai passé la nuit ici, au moins ils ne m'ont pas vu.",
            "next": "cellar_bonus_effects"
        },
        "cellar_bonus_effects": {
            "type": "effects",
            "effects": {"trust": +3, "police_gap": +1},
            "next": "end"
        },

        # ---- FOLLOW BRANCH (Leave) ----
        "follow_leave": {
            "type": "effects",
            "effects": {"trust": +2, "police_gap": -1},
            "next": "cinematic_leave_car"
        },
        "cinematic_leave_car": {
            "type": "wait_scene",
            "event": "tony_sleeps_car",
            "next": "exit_car"
        },

                "ignore_start": {
            "type": "effects",
            "effects": {"trust": -6, "police_gap": 0},
            "next": "ignore_tony_line"
        },
        "ignore_tony_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "C’est gentil de votre part, mais je ne veux pas vous déranger. Je vais passer la nuit dans ma voiture.",
            "next": "ignore_martha_line"
        },
        "ignore_martha_line": {
            "type": "line",
            "speaker": "Martha",
            "text": "Dans ce cas, vous pouvez rester ici à côté de la maison. Si vous avez besoin de quoi que ce soit, n’hésitez pas à frapper à la porte.",
            "next": "ignore_anim_martha_back"
        },
        "ignore_anim_martha_back": {
            "type": "wait_scene",
            "event": "mistrust_martha_turn_back_disappear",
            "next": "ignore_anim_tony_turn"
        },
        "ignore_anim_tony_turn": {
            "type": "wait_scene",
            "event": "mistrust_tony_turn_other_and_disappear",
            "next": "ignore_dark"
        },
        "ignore_dark": {
            "type": "wait_scene",
            "event": "night_cut_with_sirens",
            "next": "ignore_wakeup"
        },
        "ignore_wakeup": {
            "type": "wait_scene",
            "event": "wakeup_car_only",
            "next": "ignore_tony_alarm"
        },
        "ignore_tony_alarm": {
            "type": "line",
            "speaker": "Tony",
            "text": "Merde, ils m’ont déjà trouvé ? Est-ce que la vieille les a appelés ? Vaudrait mieux se barrer tout de suite.",
            "next": "ignore_car_speed"
        },
        "ignore_car_speed": {
            "type": "wait_scene",
            "event": "car_speed_away_fast",
            "next": "end"
        },

        # ---- LOW-TRUST OVERRIDE (Player suggested 1 or 2; Tony picks 3) ----
        "mistrust_override_start": {
            "type": "line",
            "speaker": "Tony",
            "text": "C’est gentil de votre part, mais je ne veux pas vous déranger. Je vais passer la nuit dans ma voiture.",
            "next": "ignore_effects_redirect"
        },
        "ignore_effects_redirect": {
            "type": "effects",
            "effects": {"trust": -8, "police_gap": 0},
            "next": "ignore_martha_line"
        },
        "mistrust_martha_reply": {
            "type": "line",
            "speaker": "Martha",
            "text": "Dans ce cas, vous pouvez restez ici à côté de la maison. Si vous avez besoin de quoi que ce soit, n’hésitez pas à frapper à la porte",
            "next": "mistrust_cin_martha_turn"
        },
        "mistrust_cin_martha_turn": {
            "type": "wait_scene",
            "event": "mistrust_martha_turn_back_disappear",
            "next": "mistrust_cin_tony_wait_disappear"
        },
        "mistrust_cin_tony_wait_disappear": {
            "type": "wait_scene",
            "event": "mistrust_tony_turn_other_and_disappear",
            "next": "cin_dark_sirens"
        },

        # After sirens, show only the car, no Tony nor Martha
        "mistrust_wakeup_car_only": {
            "type": "wait_scene",
            "event": "wakeup_car_only",
            "next": "mistrust_tony_thinks"
        },
        "mistrust_tony_thinks": {
            "type": "line",
            "speaker": "Tony",
            "text": "Merde, ils m’ont déjà trouvé ? Est-ce que la vieille les a appelés ? Vaudrait mieux se barrer tout de suite.",
            "next": "mistrust_car_speed_off"
        },
        "mistrust_car_speed_off": {
            "type": "wait_scene",
            "event": "car_speed_away_fast",
            "next": "end"
        },

        # ---- Exit texts (still available for other branches) ----
        "exit_chase": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ["Harold aperçoit la voiture de Tony et découvre que c'est celle du braqueur qu'il recherche. ",
             "Tony prend peur, s’enfuit par la fenêtre se situant à l'arrière de la maison et se précipite vers sa voiture. ",
             "Harold le poursuit en voiture de police.",
            ],
            "next": "end"
        },
        "exit_safe": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Quelques heures plus tard, Tony repart discrètement dans sa voiture. Harold n’a rien remarqué.",
            "next": "end"
        },
        "exit_car": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony passe la nuit dans sa voiture, mal au point, puis repart au petit matin. Harold n'a rien remarqué.",
            "next": "end"
        },

        "end": { "type": "end" }
    }
}