"""Launcher that loads torch before streamlit to avoid DLL conflict on Windows."""
import sys

if sys.platform == "win32":
    import torch  # noqa: F401 — must load before streamlit on Windows

from streamlit.web import cli as stcli

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app/main.py"]
    stcli.main()
