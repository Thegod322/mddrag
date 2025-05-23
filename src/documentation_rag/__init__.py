"""
Documentation RAG MCP Server - Lightweight Version

A Model Context Protocol (MCP) server that provides Canvas parsing and simple search
capabilities for Obsidian documentation without heavy dependencies.
"""

from .canvas_parser import CanvasParser

__version__ = "0.1.0-light"
__all__ = ["CanvasParser"]
