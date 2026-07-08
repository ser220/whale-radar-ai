from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "whale_radar.db"

DATA_DIR.mkdir(parents=True, exist_ok=True)
