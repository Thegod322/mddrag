"""
Documentation RAG MCP Server

A Model Context Protocol (MCP) server that provides:
1. Canvas parsing and search for Obsidian documentation
2. External documentation management (libraries, frameworks, tools)
"""

from .canvas_parser import CanvasParser
from .rag_engine import RAGEngine
from .external_docs_engine import ExternalDocsEngine

__version__ = "0.2.0"
__all__ = ["CanvasParser", "RAGEngine", "ExternalDocsEngine"]
