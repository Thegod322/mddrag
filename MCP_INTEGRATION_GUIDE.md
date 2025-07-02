vault_file = os.path.expanduser('~/.vaultpicker/active_vault.json')
vault_file = os.path.expanduser('~/.vaultpicker/active_vault.json')

# VaultPicker & MCP: Минималистичная интеграция

**VaultPicker** (VS Code extension) всегда пишет активный vault в файл:
- Windows: `%USERPROFILE%\.vaultpicker\active_vault.json`
- Linux/Mac: `~/.vaultpicker/active_vault.json`

**MCP-сервер** (Python) может автоматически подставлять этот путь в свои инструменты, чтобы пользователь не вводил его вручную.

## Пример автоподстановки vault path в MCP tool

```python
from mcp.server.fastmcp import FastMCP
import os, json

mcp = FastMCP("My Vault Tools")

def get_current_vault_path() -> str | None:
    vault_file = os.path.expanduser('~/.vaultpicker/active_vault.json')
    if os.path.exists(vault_file):
        with open(vault_file, encoding='utf-8') as f:
            try:
                vault = json.load(f)
                return vault.get('path')
            except Exception:
                return None
    return None

@mcp.tool()
def do_something_with_vault(some_param: str, vault_path: str = None) -> str:
    if not vault_path:
        vault_path = get_current_vault_path()
    if not vault_path:
        return "Vault path not found!"
    # ...логика работы с vault_path...
    return f"Работаю с vault: {vault_path}, параметр: {some_param}"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

**Пояснения:**
- Пользователь или LLM вызывает инструмент без vault_path — он подставляется автоматически.
- Не нужно вручную копировать путь из VaultPicker.
- MCP читает файл только на чтение.

---
Этот подход делает интеграцию максимально простой и удобной для пользователя и LLM.
