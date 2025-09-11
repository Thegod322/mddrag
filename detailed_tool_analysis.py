#!/usr/bin/env python3
"""
Детальное сравнение реализации print_mdd с другими инструментами
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

from documentation_rag.server import handle_list_tools, handle_call_tool

async def compare_tools():
    """Сравниваем реализацию всех инструментов"""
    print("=== ДЕТАЛЬНЫЙ АНАЛИЗ ИНСТРУМЕНТОВ ===")
    print()
    
    # Получаем список инструментов
    tools = await handle_list_tools()
    
    print(f"Общее количество инструментов: {len(tools)}")
    print()
    
    # Анализируем каждый инструмент
    for i, tool in enumerate(tools, 1):
        print(f"--- ИНСТРУМЕНТ {i}: {tool.name} ---")
        print(f"Название: {tool.name}")
        print(f"Описание: {tool.description}")
        
        # Проверяем схему
        schema = tool.inputSchema
        print(f"Схема типа: {schema.get('type', 'НЕ УКАЗАН')}")
        
        properties = schema.get('properties', {})
        required = schema.get('required', [])
        
        print(f"Свойства ({len(properties)}):")
        for prop_name, prop_def in properties.items():
            is_required = prop_name in required
            req_status = "ОБЯЗАТЕЛЬНЫЙ" if is_required else "опциональный"
            print(f"  - {prop_name}: {prop_def.get('type', 'unknown')} ({req_status})")
        
        print(f"Обязательные параметры: {required}")
        
        # Тестируем вызов с пустыми параметрами для проверки обработки ошибок
        print("Тестирование обработки ошибок...")
        try:
            if tool.name == "get_modular_documentation":
                result = await handle_call_tool(tool.name, {"canvas_file": "nonexistent.canvas"})
            elif tool.name == "print_mdd":
                result = await handle_call_tool(tool.name, {"canvas_file": "nonexistent.canvas", "output_path": "./test.MDD"})
            elif tool.name == "get_file_content":
                result = await handle_call_tool(tool.name, {"file_path": "nonexistent.txt"})
            elif tool.name == "search_documentation":
                result = await handle_call_tool(tool.name, {"query": "test query"})
            else:
                result = [{"type": "text", "text": "Unknown tool"}]
            
            print(f"  Результат: {len(result)} элементов")
            if result:
                print(f"  Тип ответа: {result[0].type}")
                print(f"  Текст (первые 100 символов): {result[0].text[:100]}...")
            
        except Exception as e:
            print(f"  ОШИБКА при вызове: {e}")
        
        print()
        print("=" * 60)
        print()

if __name__ == "__main__":
    asyncio.run(compare_tools())
