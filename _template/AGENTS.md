# AGENTS.md - шаблон каталога

- Ты в catalog-полосе: **data-only** плагины (JSON-рецепты, без кода) —
  trust tier, который делает PR-ревью безопасным.
- Инструменты: `catalog-lint` (валидация catalog.json) и `catalog-snapshot`
  (снапшот пакета в контролируемый org); локально — `scripts/validate_package.py`.
- Публикация — PR в этот репо; CI проверяет схему, step-kinds, селекторы,
  sensitive-флаги и capability-белый список.
- Запрещённые step-kinds (captcha, stripe и другие engine-reserved) валидатор
  отклонит — они живут только в подписанном gated-канале.
- Копируй `_template/` в `plugins/<id>/<version>/` и редактируй; полное
  описание — README.md корня.
