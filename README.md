# Documentation RAG MCP Server

Сервер Model Context Protocol (MCP) для работы с RAG (Retrieval-Augmented Generation) на базе модульной документации из Obsidian Canvas.

## Возможности

- 📊 **Парсинг Canvas файлов**: Анализ структуры Obsidian Canvas с поддержкой цветового кодирования узлов
- 🔍 **Семантический поиск**: Индексация и поиск по документации с использованием векторных эмбеддингов
- 📁 **Чтение файлов**: Получение содержимого файлов из Obsidian vault
- 🎨 **Модульная документация**: Поддержка структурированной документации с типизированными узлами

## Цветовая схема узлов

- **Без цвета (0)**: Референс на переменную или блок информации
- **Красный (1)**: Сущность / Класс / Страница
- **Оранжевый (2)**: Пользовательская категория
- **Желтый (3)**: Пользовательская категория  
- **Синий (4)**: Действие / Кнопка / Переход
- **Голубой (5)**: Пользовательская категория
- **Фиолетовый (6)**: Пользовательская категория

## Установка

1. Убедитесь, что у вас установлен Python 3.8+

2. Установите зависимости:
```bash
cd C:\ClaudeHub\MCP\DoumentationRag
pip install -e .
```

3. Или установите зависимости напрямую:
```bash
pip install mcp chromadb sentence-transformers pydantic
```

## Настройка MCP

Добавьте сервер в конфигурацию Claude Desktop (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "documentation-rag": {
      "command": "python",
      "args": ["-m", "documentation_rag.server"],
      "cwd": "C:\\ClaudeHub\\MCP\\DoumentationRag\\src"
    }
  }
}
```

## Использование

### 1. Получение модульной документации

```python
# Парсинг Canvas файла
get_modular_documentation(
    vault_path="C:\\Path\\To\\Your\\Obsidian\\Vault",
    canvas_file="project.canvas"
)
```

### 2. Чтение файлов

```python
# Получение содержимого файла
get_file_content(
    vault_path="C:\\Path\\To\\Your\\Obsidian\\Vault", 
    file_path="docs/readme.md"
)
```

### 3. Индексация документации

```python
# Создание поискового индекса
index_documentation(
    vault_path="C:\\Path\\To\\Your\\Obsidian\\Vault",
    force_reindex=False
)
```

### 4. Семантический поиск

```python
# Поиск по документации
search_documentation(
    query="как создать natal chart",
    vault_path="C:\\Path\\To\\Your\\Obsidian\\Vault",
    limit=5
)
```

## Пример использования с Claude

После настройки MCP вы можете использовать инструменты в диалоге с Claude:

```
Пользователь: Проанализируй структуру моего проекта в Canvas файле project.canvas

Claude: Я помогу проанализировать ваш проект. Сначала мне нужно путь к вашему Obsidian vault.

[Использует get_modular_documentation для парсинга Canvas]
[Анализирует структуру узлов и связей]
[Предоставляет понятное описание архитектуры проекта]
```

## Структура проекта

```
DoumentationRag/
├── src/
│   └── documentation_rag/
│       ├── __init__.py
│       ├── server.py          # Основной MCP сервер
│       ├── canvas_parser.py   # Парсер Canvas файлов
│       └── rag_engine.py      # RAG движок с ChromaDB
├── pyproject.toml
└── README.md
```

## Технические детали

### Векторная база данных
- Использует **ChromaDB** для локального хранения векторов
- Модель эмбеддингов: `all-MiniLM-L6-v2` (быстрая и качественная)
- Индекс сохраняется в папке `.rag_index` внутри vault

### Чанкинг документов
- Автоматическое разбиение больших файлов на фрагменты
- Умное разделение по параграфам и предложениям
- Максимальный размер чанка: 1000 символов

### Контекстные эмбеддинги
- Узлы индексируются с учетом их связей и типа
- Включает информацию о цветовом кодировании
- Сохраняет структурные отношения между элементами

## Troubleshooting

### Проблема: "ModuleNotFoundError: No module named 'mcp'"
```bash
pip install mcp
```

### Проблема: "ChromaDB connection error"
- Убедитесь, что папка vault доступна для записи
- Проверьте права доступа к папке `.rag_index`

### Проблема: "Canvas file not found"
- Убедитесь, что путь к vault указан правильно
- Проверьте, что Canvas файл существует и доступен

## Разработка

Для разработки клонируйте репозиторий и установите в режиме разработки:

```bash
git clone <repository>
cd DoumentationRag
pip install -e ".[dev]"
```

Для форматирования кода:
```bash
black src/
```

Для проверки типов:
```bash
mypy src/
```

## Лицензия

MIT License - подробности в файле LICENSE.
