# Stitch Plugin Catalog — community methods / методы комьюнити

Community catalog of **data-only** registration-method plugins for
[Stitch Manager](https://github.com/WhiteBite/Stitch-Manager).
Каталог **data-only** плагинов методов регистрации для Stitch Manager.

Plugins here are **JSON data** (steps + selectors), never code — that is what
makes PR review safe: there is nothing to execute, only a recipe to read.
Плагины здесь — **данные** (шаги + селекторы), не код: ревью PR безопасно,
исполнять нечего, есть только рецепт для чтения.

## Trust model / модель доверия

- Community methods install **without a token**, marked `community` in the app.
  Методы комьюнити ставятся **без токена**, в приложении помечены `community`.
- Official gated methods (signed, telemetry, kill-switch) live in the private
  distribution channel, not here. Официальные методы — в закрытом канале.
- Every PR is validated by CI (schema, known step kinds, concrete selectors,
  sensitive flags, capability whitelist, no secrets-looking literals).

## Catalog index schema / схема индекса каталога

The root [`catalog.json`](catalog.json) is a flat index of plugin entries.
CI runs `catalog-lint` on every push and PR to validate it offline (no
network, no fetching). Корневой [`catalog.json`](catalog.json) — плоский
индекс записей плагинов; CI запускает `catalog-lint` на каждый push/PR
(офлайн, без сети).

```json
{
  "schema": "stitch.catalog/v1",
  "plugins": [
    {
      "id": "my-plugin",
      "version": "1.0.0",
      "source": { "type": "git", "url": "https://github.com/owner/repo.git" }
    },
    {
      "id": "another-plugin",
      "version": "2.3.1",
      "source": {
        "type": "release",
        "url": "https://github.com/owner/repo/releases/download/v2.3.1/plugin.zip",
        "sha256": "abcdef0123456789...64hexchars"
      }
    },
    { "id": "legacy-plugin", "version": "0.9.0" }
  ]
}
```

**Lint rules / правила проверки:**

1. JSON must parse and be a dict with a `plugins` list.
2. Each entry must have string `id` and string `version`.
3. `version` must be semver (`MAJOR.MINOR.PATCH` with optional `-prerelease`).
4. If `source` is present it must be an object with `type`:
   - `git` — requires `url` (str).
   - `release` — requires `url` (str) + `sha256` (hex64).
   - Unknown `type` → error.
5. Duplicate `id@version` pairs → error.
6. Legacy entries (no `source`) are accepted for backward compatibility.

Run locally / локально:

```bash
pip install git+https://github.com/WhiteBite/Stitch-Manager.git#subdirectory=python
python -m stitch_plugin_tools catalog-lint catalog.json
```

## Package layout / структура пакета

```
plugins/<id>/<version>/
├── plugin.json     # manifest: id, service(+services), version, kind=data,
│                   #   engine{min,api}, depends, capabilities, outputs
├── scenario.json   # ScenarioV2 steps + weighted selector_candidates
├── selectors.json  # named selector groups (selector-pack channel)
└── profile.json    # spoofer persona hints
```

## Start from `_template/` / начните с `_template/`

The repo ships a minimal, validator-passing starter plugin at
[`_template/`](_template/) — copy it and edit the JSON.
В репо есть минимальный шаблон-плагин в [`_template/](_template/) —
скопируйте и отредактируйте JSON.

```bash
cp -r _template plugins/<your-id>/<your-version>
# edit plugin.json (id, name, version, service, capabilities, outputs)
# edit scenario.json (real URL, real selectors, real step flow)
# edit selectors.json (mirror the selector groups your scenario uses)
# edit profile.json (persona hints for your target service)
```

The template's [`README.md`](_template/README.md) explains every field,
the StepKind v2 reference, selector candidate kinds, weight semantics,
and value placeholders. It is a **template**, not a published plugin —
it lives at the repo root (not under `plugins/`), so the catalog index
and the no-argument CI validator skip it. Validate it explicitly:
Шаблон — это **не опубликованный плагин**: он лежит в корне репо (не в
`plugins/`), поэтому индекс и CI-валидатор без аргументов его пропускают.

```bash
python scripts/validate_package.py _template   # validate the template itself
python scripts/validate_package.py plugins/<your-id>/<your-version>  # validate your copy
```

## Authoring quick-start / как написать метод

1. Install the open-source app; develop in `plugins-local/` with
   `STITCH_DEV_MODE=1`; failed runs produce a pending report **with a
   screenshot** (Settings → Telemetry) — fix selectors from evidence.
   Разрабатывайте в `plugins-local/` с `STITCH_DEV_MODE=1`; падение даёт
   репорт **со скриншотом** (Настройки → Телеметрия) — чините по доказательству.
2. Steps (StepKind v2): `goto click fill press waitFor assert manual.pause
   proxy.switch extract branch imap.otp captcha.solve stripe.fill_checkout
   account.save`.
3. Values: `${account.email}` `${account.password}` `${account.name}`
   `${verification_code}`; custom via `extract` → `to`.
4. Selector candidates are weighted (1.0 = most specific):
   `testid`/`attr data-id` 1.0 · specific `css` 0.8 · `attr` 0.6–0.8 ·
   `aria`/`text` 0.4–0.5 · generic 0.2. Keep multilingual fallbacks.
5. Behavior: `meta.on_failure: continue|skip|abort`, `meta.optional`,
   `meta.human_pause`, `meta.assert` + `meta.poll`.
6. Privacy: steps touching credentials MUST be `sensitive: true` — their
   artifacts never leave the user's machine. Шаги с кредами обязаны быть
   `sensitive: true` — их артефакты не покидают машину.
7. Shared logic lives in engine capabilities; shared sub-flows — in `depends`
   packages (see `aws-builder-id` in the private channel). Общее — в
   capabilities движка и depends-пакетах, не копипастой.

## Submit / как отправить на проверку

- In the app: Settings → Community → your package → **«Submit for review»**
  (opens a PR to this repo via your GitHub token), or
  В приложении: Настройки → Комьюнити → «Отправить на проверку» (оформляет PR).
- Or manually: fork, add `plugins/<id>/<version>/`, open a PR.
- Owner reviews the JSON diff; CI validates; merge → the index
  (`catalog.json`) is rebuilt automatically → the method appears in every
  app as a new community method. После merge индекс пересобирается сам,
  метод появляется у всех как новый метод комьюнити.

## Validation locally / локальная валидация

```bash
# from the open-core app repo python/ dir (or PYTHONPATH to it):
python <catalog>/scripts/validate_package.py plugins/<id>/<version>
```
