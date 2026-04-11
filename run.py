"""Launcher that loads torch before streamlit to avoid DLL conflict on Windows."""
import torch  # noqa: F401 — must load before streamlit
from streamlit.web import cli as stcli
import sys

if __name__ == "__main__":
    sys.argv = ["streamlit", "run", "app/main.py"]
    stcli.main()
