#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Web console entry (FastAPI).

Starts the FastAPI application from backend.app.

  python -m backend.server
  python -m backend.server --host 0.0.0.0 --port 8787
"""
from __future__ import annotations

from backend.app import main

if __name__ == "__main__":
    main()
