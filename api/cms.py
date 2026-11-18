"""Vercel ASGI entry point for the separate CMS preview project."""
import sys
from pathlib import Path

CMS_ROOT = Path(__file__).resolve().parents[1] / 'cms' / 'checkpoint-3'
sys.path.insert(0, str(CMS_ROOT))

from app import app  # noqa: E402
