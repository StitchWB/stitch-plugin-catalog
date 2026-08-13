# `_template/` — starter plugin

A minimal, **data-only** plugin package you copy to start a new community
method. It passes the catalog validator (`scripts/validate_package.py`) as-is.

This is a **template**, not a published plugin — it lives at the repo root
under `_template/`, not under `plugins/`, so the catalog index
(`catalog.json`) and the no-argument validator run skip it.

## Copy and go

```bash
# from the catalog root:
cp -r _template plugins/<your-id>/<your-version>
# then edit plugin.json → id, name, version, service, capabilities, outputs
# edit scenario.json → real URL, real selectors, real step flow
# edit selectors.json → mirror the selector groups your scenario uses
# edit profile.json → persona hints for your target service
```

After editing, validate locally (requires the open-core app repo on
`PYTHONPATH` — see the catalog README's "Validation locally" section):

```bash
python scripts/validate_package.py plugins/<your-id>/<your-version>
```

## Files

| file            | purpose                                                       |
| --------------- | ------------------------------------------------------------- |
| `plugin.json`   | Manifest — identity, engine version, capabilities, outputs. |
| `scenario.json` | ScenarioV2 steps — the registration recipe (goto → fill → click → extract → account.save). |
| `selectors.json`| Named selector groups for the v1.1 selector-pack channel.    |
| `profile.json`  | Spoofer persona hints (screen, hardware, WebGL, geolocation). |

## What the template demonstrates

- **`kind: "data"`** — every community plugin is data-only (JSON, no code).
  This is the trust tier that makes PR review safe.
- **`engine.api: 2`** — the catalog validator rejects `api > 2`.
- **`entry`** — for `kind: "data"` the manifest must list `scenario`,
  `selectors`, and `profile` (all string filenames relative to the package dir).
- **`capabilities`** — must be in the catalog whitelist prefixes:
  `imap.otp`, `captcha.solve`, `stripe.fill_checkout`, `account.save`,
  `extract`, `branch`, `totp.register`. The template uses `extract` and
  `account.save`.
- **`signature: ""`** — community plugins are unsigned. The empty string is
  the correct value; the app marks unsigned packages as `community` trust.
- **`selector_candidates`** — every step that interacts with the page carries
  weighted candidates. Higher weight = more specific/reliable. The engine
  tries them in weight order. `goto` and `account.save` steps have no
  selectors (empty list) because they don't target a page element.
- **`sensitive: true`** — steps that touch credentials (`fill_password`,
  `save_account`) are marked sensitive. Their telemetry artifacts
  (screenshots, HTML) are stripped before upload. The validator **rejects**
  a `fill` step whose value contains `${account.password}` but is not
  `sensitive: true`.
- **`meta.to`** on `extract` — stores the extracted text in a runtime
  variable named `welcome_text` for later steps to reference.
- **`meta.outputs`** on `account.save` — documents which account fields the
  terminal step persists.

## StepKind v2 reference

Valid `kind` values in `scenario.json` steps:

```
goto  click  fill  press  waitFor  assert  manual.pause  proxy.switch
extract  branch  imap.otp  captcha.solve  stripe.fill_checkout
totp.register  account.save  noop
```

Unknown kinds are tolerated (mapped to `noop` = skip-in-place), but the
catalog validator flags them — stick to the known kinds above.

## Value templates

| placeholder             | meaning                                  |
| ----------------------- | ---------------------------------------- |
| `${account.email}`      | generated signup email                   |
| `${account.password}`   | generated signup password                |
| `${account.name}`       | display name derived from email          |
| `${verification_code}`  | OTP pulled by an `imap.otp` step         |
| `${welcome_text}`       | custom value from an `extract` step's `meta.to` |

## Selector candidate kinds

| kind     | value format                          |
| -------- | ------------------------------------- |
| `testid` | `data-testid` attribute value         |
| `css`    | CSS selector                          |
| `attr`   | `attr=value` (aria-label, placeholder, id, …) |
| `text`   | visible text to match                 |
| `aria`   | aria-label value                      |
| `xpath`  | XPath expression                     |

## Weight semantics

Higher weight = more specific / more reliable. The engine tries candidates
in weight order. Rule of thumb:

- `testid` / `attr data-id` → **1.0**
- specific `css` → **0.8**
- `attr` (aria-label, placeholder) → **0.5–0.7**
- `text` / `aria` → **0.4–0.5**
- generic `css` → **0.2–0.3**

Keep multilingual fallbacks (e.g. English + Russian text variants) at lower
weights.
