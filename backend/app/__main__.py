"""Allow `python -m app` when the backend package is on Python's path."""
from app.cli import main

raise SystemExit(main())
