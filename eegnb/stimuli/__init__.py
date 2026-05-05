from pathlib import Path

STIMULI_ROOT = Path(__file__).parent

FACE_HOUSE = STIMULI_ROOT / "visual" / "face_house"
CAT_DOG = STIMULI_ROOT / "visual" / "cats_dogs"
FLOC = STIMULI_ROOT / "visual" / "floc"

# Workspace-dependent stimuli (optional, might not exist for all users)
WORKSPACE_ROOT = Path.home() / "Workspace"
MINDEYE_STIMULI = WORKSPACE_ROOT / "data" / "rtmindeye_paper" / "rt3t" / "data" / "all_stimuli" / "special515"
RT_MINDEYE_DIR = WORKSPACE_ROOT / "rt_mindEye2"
