"""
Canvas Parser for Obsidian Canvas files

This module provides functionality to parse Obsidian Canvas files and extract
structured information including nodes, edges, and their relationships.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class CanvasParser:
    """Parser for Obsidian Canvas files with enhanced functionality for RAG."""
    
    COLOR_LEGEND = {
        "0": "Референс на переменную или блок информации (нет цвета)",
        "1": "Сущность / Класс / Страница", 
        "2": "Оранжевый — Внешние сервисы и API",
        "3": "Желтый — ...",
        "4": "Действие / Кнопка / Переход",
        "5": "Голубой — ...",
        "6": "Фиолетовый — Технические спецификации (фреймворки, библиотеки)"
    }
    
    def __init__(self, vault_root: str):
        """Initialize parser with vault root path."""
        self.vault_root = Path(vault_root)
        if not self.vault_root.exists():
            raise ValueError(f"Vault root does not exist: {vault_root}")
    
    def clean_node(self, node: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and structure node data."""
        result = {
            "id": node["id"],
            "type": node["type"]
        }
        
        if "text" in node:
            result["text"] = node["text"]
        
        if "color" in node:
            result["color"] = node["color"]
        else:
            result["color"] = "0"
        
        if "file" in node:
            result["file"] = node["file"]
        
        return result
    
    def clean_edge(self, edge: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and structure edge data."""
        result = {
            "id": edge["id"],
            "fromNode": edge["fromNode"],
            "toNode": edge["toNode"]
        }
        
        if "label" in edge:
            result["label"] = edge["label"]
        
        return result
    
    def parse_canvas_file(self, canvas_path: str) -> Dict[str, Any]:
        """
        Parse a Canvas file and return structured data.
        
        Args:
            canvas_path: Relative path to Canvas file from vault root
            
        Returns:
            Dictionary containing parsed canvas data
        """
        full_path = self.vault_root / canvas_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Canvas file not found: {canvas_path}")
        
        if not full_path.suffix == '.canvas':
            raise ValueError(f"File is not a Canvas file: {canvas_path}")
        
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Canvas file: {e}")
        
        # Parse nodes and edges
        nodes = [self.clean_node(n) for n in data.get("nodes", [])]
        edges = [self.clean_edge(e) for e in data.get("edges", [])]
        
        result = {
            "color_legend": self.COLOR_LEGEND,
            "canvas_path": canvas_path,
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": self._get_node_type_counts(nodes),
                "color_distribution": self._get_color_distribution(nodes)
            }
        }
        
        return result
    
    def find_canvas_file(self, canvas_filename: str) -> Optional[str]:
        """
        Recursively search for a Canvas file by name in the vault.
        
        Args:
            canvas_filename: Name of the canvas file (e.g., "Documentation-rag_MDD.canvas")
            
        Returns:
            Relative path to the first matching canvas file, or None if not found
        """
        # Ensure the filename has .canvas extension
        if not canvas_filename.endswith('.canvas'):
            canvas_filename += '.canvas'
        
        # Search recursively through vault
        for canvas_path in self.vault_root.rglob(canvas_filename):
            if canvas_path.is_file():
                # Return relative path from vault root
                relative_path = canvas_path.relative_to(self.vault_root)
                return str(relative_path).replace('\\', '/')
        
        return None

    def parse_canvas_auto(self, canvas_filename: str) -> Dict[str, Any]:
        """
        Parse Canvas file with automatic file search.
        
        Args:
            canvas_filename: Name of the canvas file (will be found automatically)
            
        Returns:
            Parsed canvas data
            
        Raises:
            ValueError: If canvas file is not found or invalid
        """
        # Find the canvas file automatically
        found_path = self.find_canvas_file(canvas_filename)
        if not found_path:
            raise ValueError(f"Canvas file not found: {canvas_filename}")
        
        # Use existing parse_canvas_file method with found path
        return self.parse_canvas_file(found_path)
    
    def _get_node_type_counts(self, nodes: List[Dict]) -> Dict[str, int]:
        """Get count of each node type."""
        type_counts = {}
        for node in nodes:
            node_type = node["type"]
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
        return type_counts
    
    def _get_color_distribution(self, nodes: List[Dict]) -> Dict[str, int]:
        """Get distribution of colors across nodes."""
        color_counts = {}
        for node in nodes:
            color = node.get("color", "0")
            color_counts[color] = color_counts.get(color, 0) + 1
        return color_counts
    
    def get_file_nodes(self, canvas_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract all file-type nodes from canvas data."""
        file_nodes = []
        for node in canvas_data.get("nodes", []):
            if node.get("type") == "file" and "file" in node:
                file_nodes.append(node)
        return file_nodes
    
    def read_referenced_files(self, canvas_data: Dict[str, Any]) -> Dict[str, str]:
        """Read content of all files referenced in the canvas."""
        file_contents = {}
        file_nodes = self.get_file_nodes(canvas_data)
        
        for node in file_nodes:
            file_path = node["file"]
            try:
                full_path = self.vault_root / file_path
                if full_path.exists() and full_path.is_file():
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_contents[file_path] = f.read()
                else:
                    file_contents[file_path] = f"[File not found: {file_path}]"
            except Exception as e:
                file_contents[file_path] = f"[Error reading file: {e}]"
        
        return file_contents
    
    def get_contextual_text_for_node(self, node_id: str, canvas_data: Dict[str, Any]) -> str:
        """
        Generate contextual text for a node including its type and content.
        Simplified for better performance and reduced context size.
        """
        nodes = {n["id"]: n for n in canvas_data.get("nodes", [])}
        
        if node_id not in nodes:
            return ""
        
        node = nodes[node_id]
        context_parts = []
        
        # Add node type and color context
        color = node.get("color", "0")
        color_meaning = self.COLOR_LEGEND.get(color, "Unknown")
        context_parts.append(f"Node Type: {color_meaning}")
        
        # Add node content
        if "text" in node:
            context_parts.append(f"Content: {node['text']}")
        
        if "file" in node:
            context_parts.append(f"File Reference: {node['file']}")
        
        return " | ".join(context_parts)
