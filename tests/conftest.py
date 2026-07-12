import pathlib
import sys

# Make the repo root importable (app.backend.*) regardless of pytest rootdir.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
