# version si le joueur est attrapé
SCENE_AIRPORT_CAUGHT = {
    "id": "airport_caught",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony arrive à l’aéroport, haletant, fatigué, blessé…",
            "next": "check_outcome"
        },
        "check_outcome": {
            "type": "branch_condition",
            "branches": [
                {"cond": "police", "next": "caught_police"},
                {"cond": "escape", "next": "escape"}  # ne sera pas utilisé
            ]
        },
        "caught_police": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Alors qu’il approche de l’avion, une voiture de police surgit et bloque son passage.",
            "next": "caught_dialogue"
        },
        "caught_dialogue": {
            "type": "line",
            "speaker": "Police",
            "text": "Tony, tu es en état d’arrestation, tout ce que tu diras sera retenu contre toi, sale crapule !",
            "next": "end"
        },
        "escape": { "type": "line", "speaker": "Narrateur", "text": "", "next": "end"},
        "end": { "type": "end" }
    }
}

# version si le joueur s’échappe
SCENE_AIRPORT_ESCAPED = {
    "id": "airport_escaped",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony arrive à l’aéroport, haletant, fatigué, blessé…",
            "next": "check_outcome"
        },
        "check_outcome": {
            "type": "branch_condition",
            "branches": [
                {"cond": "police", "next": "caught_police"},  # ne sera pas utilisé
                {"cond": "escape", "next": "escape"}
            ]
        },
        "escape": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Grâce à ses choix et à son environnement, Tony parvient à monter dans l’avion et s’échapper.",
            "next": "end"
        },
        "caught_police": { "type": "line", "speaker": "Narrateur", "text": "", "next": "end"},
        "end": { "type": "end" }
    }
}
