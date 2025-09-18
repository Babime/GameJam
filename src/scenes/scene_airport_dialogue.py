# src/scenes/scene_airport_dialogue.py
#
# We now use the same intro cinematic for BOTH routes:
#   Narrateur intro → wait_scene 'airport_intro' → Tony line → wait_scene 'airport_run'
# After that, you can branch to "caught" vs "escaped" endings later.
#

SCENE_AIRPORT_CAUGHT = {
    "id": "airport_caught",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony arrive à l’aéroport, haletant, fatigué, blessé…",
            "next": "cin_intro"
        },
        "cin_intro": {
            "type": "wait_scene",
            "event": "airport_intro",   # car drives in; Tony appears
            "next": "tony_line"
        },
        "tony_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "Est ce que j'ai réussi ?",
            "next": "cin_run"
        },
        "cin_run": {
            "type": "wait_scene",
            "event": "airport_run_caught",
            "next": "tony_merde"
        },
        "tony_merde": {
            "type": "line",
            "speaker": "Tony",
            "text": "merde, Merde, MERDE, MEEEEEERDE !!!",
            "next": "harold_arrest"
        },
        "harold_arrest": {
            "type": "line",
            "speaker": "Harold",
            "text": "Tony, tu es en état d’arrestation, tout ce que tu diras sera retenu contre toi, sale crapule !",
            "next": "end"
        },
        "end": {"type": "end"}
    }
}

SCENE_AIRPORT_ESCAPED = {
    "id": "airport_escaped",
    "start": "intro",
    "nodes": {
        "intro": {
            "type": "line",
            "speaker": "Narrateur",
            "text": "Tony atteint l’aéroport. L’avion est là — il a une chance.",
            "next": "cin_intro"
        },
        "cin_intro": {
            "type": "wait_scene",
            "event": "airport_intro",  # car drives in; Tony appears
            "next": "tony_line"
        },
        "tony_line": {
            "type": "line",
            "speaker": "Tony",
            "text": "Est ce que j'ai réussi ?",
            "next": "cin_run"
        },
        "cin_run": {
            "type": "wait_scene",
            "event": "airport_run",
            "next": "flyaway_harold"
        },
        "flyaway_harold": {
           "type": "line",
           "speaker": "Harold (mari de Martha)",
           "text": "Merde, et dire que j'ai failli l'attraper",
           "next": "flyaway_tony"
       },
       "flyaway_tony": {
           "type": "line",
           "speaker": "Tony",
           "text": "HAHAHAHA, libertééé",
           "next": "end"
       },
        "end": {"type": "end"}
    }
}