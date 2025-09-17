SCENE3_MARTHA = {
    "id": "martha_scene",
    "start": "intro_1",
    "nodes": {
        # ---- Intro ----
        "intro_1": {
            "type": "line",
            "speaker": "Narrateur",
            "text": ("Depuis des heures, Tony roule sur les routes de campagne. "
                     "Le jet privé décolle bientôt, mais la balle du flic l’a bien touché. "
                     "Il recommence à perdre du sang."),
            "next": "tony_intro"
        },
        "tony_intro": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Putain... je vais pas tenir. Je perds trop de sang... Il faut que je m'arrête."
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
                "Harold ? Harold, c’est toi ? Tu rentres bien tôt ce soir... Oh, excusez-moi, je pensais que c'était mon mari !",
                "Mon Dieu, vous êtes blessé !"
            ],
            "next": "tony_beg"
        },
        "tony_beg": {
            "type": "line",
            "speaker": "Tony",
            "text": [
                "Ne vous inquiétez pas, c’est rien... juste une égratignure.",
                "J’ai juste besoin de quelques heures pour me reposer et je repartirai.",
            ],
            "next": "choice_martha"
        },

        # ---- Choice for Martha ----
        "choice_martha": {
            "type": "choice",
            "prompt": "Que proposez-vous à Tony ?",
            "options": [
                { "id": "living_room", "label": "Entrez, reposez-vous dans le salon", "correct": False }, # considerating wrong
                { "id": "cellar", "label": "Je n'ai qu'une cabane à proposer", "correct": True }, # considerating correct
                { "id": "leave", "label": "Désolée, vous ne pouvez pas rester ici", "correct": "neutral" } # considerating neutral
            ],
            "next": "branch_martha_lines"
        },

        # Branch depending on choice
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
            "next": "decide_sleep"
        },

        # ---- Decision follow / ignore ----
        "decide_sleep": {
            "type": "decision_follow_3way",
            "if_follow_correct": "follow_cellar",
            "if_follow_wrong":   "follow_living",
            "if_follow_neutral": "follow_leave",
            "if_ignore_correct": "ignore_cellar",
            "if_ignore_wrong":   "ignore_living",
            "if_ignore_neutral": "ignore_leave"
        },

        # ---- FOLLOW BRANCH ----
        # Living room (wrong)
        "follow_living": {
            "type": "effects",
            "effects": {"trust": -12, "police_gap": -3},
            "next": "cinematic_living_caught"
        },
        "cinematic_living_caught": {
            "type": "wait_scene",
            "event": "harold_arrives_chase",
            "next": "exit_chase"
        },

        # Cellar (correct)
        "follow_cellar": {
            "type": "effects",
            "effects": {"trust": +10, "police_gap": +2},
            "next": "cinematic_safe_cellar"
        },
        "cinematic_safe_cellar": {
            "type": "wait_scene",
            "event": "hide_in_cellar_safe",
            "next": "exit_safe"
        },

        # Leave (neutral)
        "follow_leave": {
            "type": "effects",
            "effects": {"trust": +6, "police_gap": -1},
            "next": "cinematic_leave_car"
        },
        "cinematic_leave_car": {
            "type": "wait_scene",
            "event": "tony_sleeps_car",
            "next": "exit_car"
        },

        # ---- IGNORE BRANCH ----
        # Living room ignored (Tony avoids trap)
        "ignore_living": {
            "type": "effects",
            "effects": {"trust": +2, "police_gap": +2},
            "next": "cinematic_ignore_living"
        },
        "cinematic_ignore_living": {
            "type": "wait_scene",
            "event": "avoid_livingroom_sleep_car",
            "next": "exit_car"
        },

        # Cellar ignored (Tony misses safe option)
        "ignore_cellar": {
            "type": "effects",
            "effects": {"trust": -6, "police_gap": -2},
            "next": "cinematic_ignore_cellar"
        },
        "cinematic_ignore_cellar": {
            "type": "wait_scene",
            "event": "reject_cellar_sleep_car",
            "next": "exit_car"
        },

        # Leave ignored (Tony insists to stay anyway in the cellar)
        "ignore_leave": {
            "type": "effects",
            "effects": {"trust": -8, "police_gap": 0},
            "next": "cinematic_force_cellar"
        },
        "cinematic_force_cellar": {
            "type": "wait_scene",
            "event": "force_cellar_stay",
            "next": "exit_safe"
        },

        # ---- Exit ----
        "exit_chase": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Harold aperçoit la voiture de Tony, il découvre que c'est la voiture du braqueur qu'il recherche. Tony prend peur et s’enfuit par la fenêtre se situant à l'arrière de la maison et se précipite vers sa voiture. Harold le poursuit en voiture de police.",
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
            "text": "Tony passe la nuit dans sa voiture, mal en point, avant de repartir. Harold ne s’est aperçu de rien.",
            "next": "end"
        },

        "end": { "type": "end" }
    }
}
