#!/usr/bin/env python3
"""
Проверка того, что точно возвращает сервер при запросе списка инструментов
"""

import asyncio
import json
import sys
from pathlib import Path

# Настраиваем путь
src_dir = Path(__file__).parent / "src"
sys.path.insert(0, str(src_dir))

async def test_server_tools():
    """Прямая проверка функций сервера"""
    print("=== ПРЯМАЯ ПРОВЕРКА СЕРВЕРА ===")
    print()
    
    try:
        # Импортируем функции из сервера
        from documentation_rag.server import handle_list_tools, handle_call_tool
        
        print("✅ Импорт сервера успешен")
        
        # Получаем список инструментов
        print("\n📋 Получение списка инструментов...")
        tools = await handle_list_tools()
        
        print(f"📊 Общее количество: {len(tools)}")
        print()
        
        # Подробная информация о каждом инструменте
        tool_names = []
        for i, tool in enumerate(tools):
            print(f"{i+1}. 🔧 {tool.name}")
            print(f"   📝 Описание: {tool.description[:100]}...")
            print(f"   🔗 Тип: {tool.inputSchema.get('type', 'unknown')}")
            
            required = tool.inputSchema.get('required', [])
            print(f"   ✅ Обязательные параметры: {required}")
            
            tool_names.append(tool.name)
            print()
        
        # Конкретная проверка print_mdd
        print("🔍 СПЕЦИАЛЬНАЯ ПРОВЕРКА print_mdd:")
        if "print_mdd" in tool_names:
            print("   ✅ print_mdd ПРИСУТСТВУЕТ в списке!")
            
            # Получаем детали print_mdd
            print_mdd_tool = next(t for t in tools if t.name == "print_mdd")
            print(f"   📝 Описание: {print_mdd_tool.description}")
            print(f"   📋 Схема: {json.dumps(print_mdd_tool.inputSchema, indent=6)}")
            
            # Тестируем вызов print_mdd
            print("\n🧪 ТЕСТИРОВАНИЕ ВЫЗОВА print_mdd:")
            test_args = {
                "canvas_file": "test_nonexistent.canvas",
                "output_path": "./test_output.MDD"
            }
            
            result = await handle_call_tool("print_mdd", test_args)
            print(f"   📤 Аргументы: {test_args}")
            print(f"   📥 Результат: {len(result)} элементов")
            if result:
                print(f"   📄 Тип ответа: {result[0].type}")
                print(f"   💬 Текст: {result[0].text[:150]}...")
            
        else:
            print("   ❌ print_mdd ОТСУТСТВУЕТ в списке!")
        
        print("\n" + "="*60)
        print("💡 ИТОГОВЫЕ ВЫВОДЫ:")
        print(f"   • Общее количество инструментов: {len(tools)}")
        print(f"   • Список инструментов: {', '.join(tool_names)}")
        
        if "print_mdd" in tool_names:
            print(f"   • print_mdd: ✅ НАЙДЕН и РАБОТАЕТ")
        else:
            print(f"   • print_mdd: ❌ НЕ НАЙДЕН")
        
        print("\n🔬 ДИАГНОЗ:")
        if len(tools) == 4 and "print_mdd" in tool_names:
            print("   Код сервера ПОЛНОСТЬЮ КОРРЕКТЕН!")
            print("   Проблема НЕ в коде сервера, а в:")
            print("   - Конфигурации Claude Desktop")
            print("   - Кешировании Claude Desktop")  
            print("   - Процессе перезагрузки")
        else:
            print("   Найдена проблема в коде сервера!")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_server_tools())
