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

## Package layout / структура пакета

```
plugins/<id>/<version>/
├── plugin.json     # manifest: id, service(+services), version, kind=data,
│                   #   engine{min,api}, depends, capabilities, outputs
├── scenario.json   # ScenarioV2 steps + weighted selector_candidates
├── selectors.json  # named selector groups (selector-pack channel)
└── profile.json    # spoofer persona hints
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
