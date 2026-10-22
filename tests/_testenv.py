"""
Gemeinsame Wegwerf-Umgebung für die Unit-Tests: Master-Schlüssel, Daten-DB und Statistik-DB in einem
temporären Ordner. Muss importiert werden, BEVOR database/stats/providers geladen werden.
"""
import base64
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix="yatb_test_")
MASTER_FILE = os.path.join(TMP, "master_key")
with open(MASTER_FILE, "w") as fh:
    fh.write(base64.b64encode(os.urandom(32)).decode())

os.environ["YATB_MASTER_KEY_FILE"] = MASTER_FILE
os.environ["YATB_DB_FILE"] = os.path.join(TMP, "module.db")
os.environ["YATB_STATS_DIR"] = os.path.join(TMP, "stats")
os.environ.pop("KEY_ENCRYPTION_SECRET", None)
os.environ.pop("YATB_PROVIDERS_FILE", None)

BOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)
