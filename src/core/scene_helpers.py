from scenes.scene_airport_dialogue import SCENE_AIRPORT_CAUGHT, SCENE_AIRPORT_ESCAPED

def select_airport_scene(gvars):
    caught = (gvars.trust < 10) or (gvars.police_gap < 6)
    gvars.flags["ending"] = "caught" if caught else "escaped"
    return SCENE_AIRPORT_CAUGHT if caught else SCENE_AIRPORT_ESCAPED