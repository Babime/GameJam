from pathlib import Path


# --- Gameplay defaults ---
INITIAL_TRUST        = 50   # was 0 — start skeptical but not hostile
INITIAL_POLICE_GAP   = 0
FOLLOW_THRESHOLD     = 55   # crossover point stays the same

# New: how "soft" the decision is around the threshold
FOLLOW_SIGMOID_K     = 0.35   # higher = sharper curve; 0.10–0.18 feels good
FOLLOW_PROB_FLOOR    = 0.05   # even at 0 trust there’s a 5% chance he'll follow
FOLLOW_PROB_CEIL     = 0.95   # even at 100 trust there's a 5% chance he'll balk

# --- Display ---
WIDTH  = 1366
HEIGHT = 768
FPS    = 60
TILE   = 16


SCENE_INTRO_BLACK_MS = 2000  

# --- Assets ---
PROJECT_ROOT       = Path(__file__).resolve().parents[2]  # <-- go up to repo root
ASSETS_DIR         = PROJECT_ROOT / "assets"
FONTS_DIR          = ASSETS_DIR / "fonts"
GENERAL_ASSET_DIR  = ASSETS_DIR / "general"
BANK_ASSET_DIR     = ASSETS_DIR / "bank"

# --- UI ---
FONT_PATH          = FONTS_DIR / "PressStart2P-Regular.ttf"
CORNER_IMG_PATH    = GENERAL_ASSET_DIR / "bottom_left_corner.png"
EDGE_IMG_PATH      = GENERAL_ASSET_DIR / "edge.png"

FONT_SIZE          = 32
LINE_HEIGHT_FACTOR = 1.6
PADDING_LEFT       = 20
PADDING_RIGHT      = 40
PADDING_TOP        = 20
PADDING_BOTTOM     = 20
BOX_FILL_COLOR     = (34, 34, 34)

# --- Gameplay defaults ---

INITIAL_POLICE_GAP  = 5
FOLLOW_THRESHOLD    = 60  # follow when trust >= 60

# --- Misc ---
RNG_SEED = 42

# --- bustshot
RIGHT_MARGIN = 40
BUSTSHOT_SCALE = 1/2.5  # draw at 40% of the current computed size