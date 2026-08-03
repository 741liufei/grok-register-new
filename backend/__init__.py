# -*- coding: utf-8 -*-
"""Lightweight FastAPI web console for Grok Register."""

__all__ = ["create_app", "main"]


def create_app():
    from .app import create_app as _create_app

    return _create_app()


def main(host: str = "127.0.0.1", port: int = 8787):
    from .app import serve

    serve(host=host, port=port)
