#!/usr/bin/env python3
"""
Простая проверка MCP протокола напрямую через stdio
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_protocol():
    """Тестируем MCP протокол без интерактивного ввода"""
    print("=== ТЕСТ MCP ПРОТОКОЛА ===")
    print()
    
    # Запускаем сервер
    server_path = Path(__file__).parent / "run_server.py"
    
    try:
        print(f"Запуск сервера: {server_path}")
        process = subprocess.Popen(
            [sys.executable, str(server_path)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).parent)
        )
        
        # Отправляем команды по MCP протоколу
        commands = [
            # 1. Инициализация
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "clientInfo": {"name": "test-client", "version": "1.0.0"}
                }
            },
            # 2. Уведомление об инициализации
            {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            },
            # 3. Запрос списка инструментов
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
        ]
        
        responses = []
        
        # Отправляем команды
        for i, cmd in enumerate(commands):
            print(f"\nОтправка команды {i+1}: {cmd['method']}")
            cmd_json = json.dumps(cmd) + "\n"
            process.stdin.write(cmd_json)
            process.stdin.flush()
            
            # Читаем ответ (только для запросов с id)
            if "id" in cmd:
                try:
                    response_line = process.stdout.readline()
                    if response_line.strip():
                        response = json.loads(response_line.strip())
                        responses.append(response)
                        print(f"Ответ получен: {response.get('id', 'no-id')}")
                        
                        # Если это ответ на tools/list, показываем инструменты
                        if cmd["method"] == "tools/list" and "result" in response:
                            tools = response["result"].get("tools", [])
                            print(f"\n🔧 НАЙДЕНО ИНСТРУМЕНТОВ: {len(tools)}")
                            for tool in tools:
                                print(f"   • {tool['name']}")
                            
                            # Проверяем print_mdd
                            print_mdd_found = any(t["name"] == "print_mdd" for t in tools)
                            if print_mdd_found:
                                print("\n✅ ИНСТРУМЕНТ print_mdd НАЙДЕН!")
                            else:
                                print("\n❌ ИНСТРУМЕНТ print_mdd НЕ НАЙДЕН!")
                        
                except json.JSONDecodeError as e:
                    print(f"Ошибка JSON: {e}")
                    print(f"Raw: {response_line}")
                except Exception as e:
                    print(f"Ошибка чтения ответа: {e}")
        
        # Проверяем stderr на ошибки
        await asyncio.sleep(0.1)  # Даем время на stderr
        
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        
        if stderr:
            print(f"\n⚠️  ОШИБКИ СЕРВЕРА:")
            print(stderr)
        else:
            print(f"\n✅ Сервер работает без ошибок в stderr")
        
        print(f"\n📊 РЕЗУЛЬТАТ ТЕСТА:")
        print(f"   - Команд отправлено: {len(commands)}")
        print(f"   - Ответов получено: {len(responses)}")
        print(f"   - Код завершения: {process.returncode}")
        
    except subprocess.TimeoutExpired:
        print("Timeout - сервер завис")
        process.kill()
    except Exception as e:
        print(f"Ошибка тестирования: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mcp_protocol())
