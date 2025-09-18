from scenes.scene_airport_dialogue import SCENE_AIRPORT_CAUGHT, SCENE_AIRPORT_ESCAPED

def select_airport_scene(gvars):
    if gvars.trust < 40 or gvars.police_gap < 0:
        return SCENE_AIRPORT_CAUGHT
    else:
        return SCENE_AIRPORT_ESCAPED
