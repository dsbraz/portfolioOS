# Repository Guidelines

Scope note: at this stage, this guide covers local development workflows only.

## Project Structure & Module Organization
This repository is split into two apps plus infrastructure:
- `Client/`: Angular frontend (`src/` for app code, `public/` for static assets, `angular.json` for build/test targets).
- `Server/`: FastAPI backend (`app/controllers/` for routes, `app/application/` for business operations, `app/repositories/` for persistence, `app/domain/` for models/schemas, `app/infrastructure/` for framework adapters, `alembic/` for migrations).
- `docker-compose.yml`: local stack (client, server, PostgreSQL).

Keep frontend and backend changes scoped to their folders; shared API contracts should be updated in both sides in the same PR.

## Application Layers & Responsibilities
Use clear boundaries between layers and keep dependencies pointing inward.

### Backend (`Server/app`)
- `controllers/` (Presentation/API layer): define HTTP routes, validate/parse request/response contracts, map errors to HTTP status codes. Keep controllers thin; no business rules here.
- `application/` (Application layer): single-purpose classes that implement business operations. Each use case has an `execute` method. Every entity has its own dedicated use cases (e.g. `CreateStartup`, `ListStartups`).
- `domain/` (Domain layer): entities, business rules, and shared validators. Keep business logic framework-light even when persistence models use SQLAlchemy.
  - `domain/validators.py`: shared domain validation functions (e.g. `validate_period_not_future`).
- `infrastructure/` (Adapter layer): concrete implementations of domain protocols for external concerns (e.g. `BcryptPasswordHasher`, `JwtTokenGenerator`).
- `repositories/` (Persistence layer): database access and persistence implementations. Never leak ORM or infra details into domain models.
- `alembic/`: schema evolution only. Migrations must reflect domain/infrastructure changes and be versioned with code.

Backend flow (required): `controllers -> application -> domain -> repos`.

### Frontend (`Client/src`)
- `pages`/route components (Presentation layer): compose screens and user interactions.
- `components` (UI layer): reusable visual building blocks with minimal business logic.
- `services` (Application/data-access layer): API communication, orchestration, and state transitions used by pages/components.
- `models` (Domain contract layer): explicit interfaces/types shared across features to avoid ad-hoc payloads, plus pure cross-feature functions (`formatters.ts`, `participation.ts`).
- `directives` (Behaviour layer): reusable input/DOM behaviour (e.g. `currency-input.ts`).
- `guards` (Auth layer): route protection (e.g. `auth.guard.ts`).
- `interceptors` (HTTP layer): cross-cutting HTTP concerns (e.g. `auth.interceptor.ts` for JWT injection).

### Layering Rules
- In backend, follow the chain strictly: `controllers -> application -> domain -> repos`.
- Route handlers call use cases for business behavior; dependency wiring in controller modules composes repositories and use cases.
- Domain logic should stay isolated from transport concerns and remain easily testable in isolation.
- Keep modules cohesive: each file/class should have a single clear reason to change.

### Backend Import Boundaries
- **Application layer must never import `fastapi`** — no `HTTPException`, no `status`, no `Depends`. Use cases work with domain models, repositories, infrastructure adapters, primitive types, and `dict`s.
- **Application layer must never import schemas** (`app.domain.schemas.*`). Schema validation and serialization belong in controllers.
- **Domain models and exceptions** (`app.domain.models.*`, `app.domain.exceptions`) are the shared language between layers.

### Error Handling Convention
- **Use cases** raise domain exceptions for business-rule violations: `ValueError` for invalid input, `ConflictError` (`app.domain.exceptions`) for state conflicts (e.g. duplicates).
- **Use cases** return `None` for not-found scenarios (e.g. `get_by_id` returns `Model | None`).
- **Controllers** catch domain exceptions and map them to HTTP status codes (`ValueError` → 400, `ConflictError` → 409, `None` → 404).
- **Controllers** own all existence checks: use FastAPI dependencies like `_verify_startup_exists` for parent-resource validation, or inline checks for entity lookups.

### Controller ↔ Use Case Data Flow
- **Input**: controllers convert schemas to domain models or `dict`s before calling use cases (e.g. `Startup(**data.model_dump())`, `data.model_dump(exclude_unset=True)`).
- **Output**: use cases return domain models; controllers convert to response schemas (e.g. `Response.model_validate(entity)`).
- **Entity resolution**: controllers look up and validate entities exist, then pass resolved domain objects to use case methods (e.g. `use_case.execute(entity, updates)` not `use_case.execute(entity_id, updates)`).

## Build, Test, and Development Commands
- Development environment standard: use Docker (`docker compose`) as the default and official workflow for local development.
- Do not install Python or Node dependencies on the host machine; use containers for dependency installation and execution.
- `docker compose up --build`: start full local environment (frontend on `:4200`, backend on `:8000`, Postgres on `:5432`).
- `docker compose exec client npx ng serve`: run frontend dev server inside container.
- `docker compose exec client npx ng build`: create frontend build in `Client/dist/`.
- `docker compose exec client npx ng test`: run frontend unit tests (Vitest via Angular builder).
- `docker compose exec server uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`: run backend locally inside container.
- `docker compose exec server pytest`: run backend automated tests.
- `docker compose exec server alembic upgrade head`: apply database migrations.
- `docker compose build server client`: rebuild images after changing Python/Node dependencies.

## Coding Style & Naming Conventions
- Language policy:
  - All source code, identifiers, comments, and technical documentation must be written in EN-US.
  - Commit messages must be written in PT-BR (keeping Conventional Commit prefixes such as `feat:`, `fix:`).
  - All user-facing UI content (labels, buttons, messages, validation feedback, dialogs, page text) must be written in PT-BR.
- Python: follow PEP 8, 4-space indentation, `snake_case` for functions/modules, `PascalCase` for classes.
- TypeScript/Angular: 2-space indentation, `camelCase` for variables/methods, `PascalCase` for classes/components.
- Angular component files should use standard suffixes (`*.ts`, `*.html`, `*.scss`, `*.spec.ts`).
- Prefer small, focused controllers/use cases and explicit names like `health_controller.py`, `register_user.py`.

## Theming & Color Conventions

The app implements the **BRQ design system**. `Client/src/styles.scss` is the single
source of truth and is layered in this order — do not reorder:

1. `mat.theme()` — emits the Material 3 `--mat-sys-*` tokens from palettes generated
   out of the BRQ seeds (`_theme-colors.scss`, produced by
   `ng generate @angular/material:theme-color`).
2. **BRQ tokens** (`--color-*`, `--font-*`, `--space-*`, `--radius-*`) — the brand itself.
3. **M3 bridge** — remaps the `--mat-sys-*` roles the brand has an opinion about onto
   the BRQ tokens, so Material components inherit the brand without template changes.

Keep the token layer in sync with `foundation.css` in the px-operations redesign
(same brand system, accessibility fixes already applied).

### Accent contract (non-negotiable)
- **Purple `#7f2ec9` is the FUNCTIONAL accent** — links, focus, active nav, chart
  series 1. The only accent that clears AA for text (6.7:1 on white). It is
  **never a button fill**.
- **Orange `#ee7c38` is the BRAND accent** — highlights and fills, never small text
  on light (2.8:1 fails AA).
- **The primary button is BLACK**, inverting to white on dark surfaces. There is no
  purple button. This is why the bridge maps `--mat-sys-primary` to `--color-primary`.
- On dark surfaces purple must be raised to `--color-accent-on-dark` (`#a94fd6`);
  `#7f2ec9` only reaches 2.8:1 on `#121212`, under the 3:1 WCAG 1.4.11 requires.
- Keep accents scarce. Avatars, badges and other chrome stay neutral.

### Typography — three families, three roles
- **Aspekta** (`--font-display`, local in `public/fonts/`) — headings only.
- **Inter** (`--font-body`) — every piece of text that carries information: table
  headers and cells, KPI labels, form labels, navigation, body copy.
- **Geist Mono** (`--font-mono`) — decorative only: tags, eyebrows and big numbers
  (KPI values, numeric table cells). Putting mono on a table header or a data label
  is the classic error.
  - **Exception — `.section-title`.** A section eyebrow that groups fields
    (`QUANTITATIVOS`) is a *structure heading*, not a data label, and stays in Inter.
    The mono eyebrow is the decorative kind (tag, chip, page kicker).

### Component families
- **`.tag`** is a static LABEL: no hover, never a link or action.
- **Chips** are INTERACTIVE (filters): rounded, hover, `aria-pressed`.
- **`.pill`** is a static STATUS: pairs a solid text tone with its precomputed tint,
  always beside an icon or label — state is never signalled by color alone.
- Rule of thumb: rounded + hover = action; tinted label = descriptor.

### Shared building blocks
Reach for these before writing a new one. Each exists because the pattern was
duplicated and drifted.

| Piece | Where | Use it for |
| --- | --- | --- |
| `.field` + `.field-label` | `styles.scss` | The boxed form field: a static label ABOVE the box, never a Material floating label. `.field-affix` carries the unit (`R$`, `%`). |
| `.section-title` | `styles.scss` | Section eyebrow. Typography only — the vertical rhythm belongs to the context that stacks it. |
| `.page-status` | `styles.scss` | Loading / error block on internal pages. |
| `.pill`, `.tag` | `styles.scss` | Status and label (see Component families). |
| `app-dialog-header` | `components/dialog-header/` | Every dialog title. Keeps `mat-dialog-title` on the `<h2>` so Material's `aria-labelledby` wiring survives, and adds the close button. |
| `app-read-view` | `components/read-view/` | Read-only view of a record: `ReadSection[]` of label/value pairs rendered as `dl`/`dt`/`dd`. |
| `appCurrencyInput` | `directives/currency-input.ts` | pt-BR currency mask. Display is formatted, the control stays numeric. Requires `type="text" inputmode="decimal"`. |
| `models/formatters.ts` | — | `formatCurrencyBRL`, `formatPercent`, `formatInteger`, `formatIsoDate`. They return `null` for absence so the caller decides how to show it. |

### Read mode is not a disabled form
**Never render a record with `form.disable()`.** A disabled control paints its text
with the inactive-control colour — measured at **2,46:1** in light and **3,53:1** in
dark, against **18,7:1** for the label beside it. WCAG 1.4.3 exempts inactive
components, so automated audits stay silent while the actual content is unreadable.

Use `app-read-view`. Its sections must mirror the edit form's groups, in the same
order, so reading and editing present the record the same way.

Two rules the component encodes:
- Absence is announced. A bare `—` says nothing to a screen reader, so it is
  `aria-hidden` beside a `.visually-hidden` "Não informado".
- **Zero is data, not absence.** Formatters test `== null`, never `!value` — a `||`
  would erase a zeroed cash balance, which is the month that matters most.
  Blank strings are normalised to `null` by each dialog, not by the component.

### States: loading, empty, error
Every data-backed screen renders **three** branches. A page that shows nothing while
loading is indistinguishable from "there is no data" — for a person and for any agent
reading the DOM.

```
@if (loading())      → .page-status role="status" + "Carregando…"
@else if (data)      → content (which may itself be an empty state with text)
@else                → .page-status with the failure message
```

`aria-busy` goes on the page container, which always exists. A live region created
together with its content is usually not announced.

### Responsiveness
- **Intrinsic first.** `repeat(auto-fit, minmax(Xrem, 1fr))` over breakpoints. Set
  `row-gap`/`column-gap` separately — grid `gap` applies to both axes, and columns
  usually need more.
- **Container queries when the sidebar is in play.** Viewport width is not available
  width: with the sidebar docked, a 1470px viewport leaves 1158px of content. A media
  query would have to hardcode that 312px discount and would be wrong whenever the
  sidebar's state changes.
- Pick thresholds by **measuring** the content in the DOM, not by estimating.

### Machine-readable UI
The app is read by assistive tech and by agents. Both use the same contract.

- Tables are real `<table mat-table>` with `<caption>` and `scope="col"` on every
  header — never the `<mat-table>` div form.
- **Every row action needs a name that identifies its row**:
  `[attr.aria-label]="'Ações de ' + deal.company"`. Three identical unnamed
  `more_vert` buttons are indistinguishable.
- **A row that navigates carries a real named link** (the `row-opener` pattern),
  never a bare click handler on the `<tr>`. A clickable row is not a control: it
  has no role, no name and no keyboard path, so an agent has to guess from the
  row's text. Put the link on the identifying cell — the entity's own name is
  the accessible name.
- **A panel that hands over a value shows it as selectable text.** No step of a
  flow may depend on the clipboard: `navigator.clipboard` is invisible to an
  agent and can reject at runtime, so Copy is a convenience that must tolerate
  failure, never the only way out.
- A tab's `aria-controls` must reference an element that EXISTS. Keep all tabpanels
  mounted and toggle `[hidden]`; rendering only the active one leaves dangling
  references. `[hidden]` is a user-agent rule of minimal specificity, so any `display`
  on the panel's class beats it — declare `&[hidden] { display: none; }` explicitly.
- No data in `<canvas>`/`<svg>` alone. Charts pair with a text legend carrying the
  values.
- Status is text, never colour alone.
- **A focus ring inside a scrolling container must be inset.** `overflow-x: auto`
  also turns `overflow-y` into `auto`, so the box clips on all four sides — an
  outward `outline-offset` gets cut off, and a clipped focus ring is an invisible
  one (2.4.7). Use `outline-offset: -2px` inside `.table-shell` / `.section-tabs`,
  or any new scroller.
- Check WHICH element is actually focusable before styling focus. Material puts
  `role="button"` and `tabindex="0"` on `.mat-sort-header-container`, not on the
  `th` — a rule aimed at the cell styles nothing.

### Rules that keep it sober
- Cards use `--radius-md` (8px). Full rounding is only for buttons, chips and search.
- The sidebar is EDITORIAL: the active item is strong ink over a NEUTRAL fill with a
  purple icon and rail — never a tinted pill.
- Charts assign `--chart-1..5` **in order and never cycle**; a 6th series becomes
  `--chart-other`. The dark palette is a deliberate CVD-safe reassignment.

### Mechanics
- Never hardcode hex/rgb in component SCSS or TypeScript. Reference tokens.
- **Alias Material roles to semantic tokens, never to the raw gray scale.** Tokens like
  `--color-gray-75` do not invert, so a Material surface pointed at one renders a light
  fill under light text in dark mode.
- Dark mode responds to both `[data-theme="dark"]` and `prefers-color-scheme`. Anything
  that switches with the theme (including image assets) must follow that same signal —
  `<picture media>` alone desyncs the moment an explicit toggle exists.
- The theme has **three** states (`ThemeService`): `system | light | dark`. `system` must
  leave `data-theme` OFF the root — stamping it always disables the
  `prefers-color-scheme` branch and the app stops reacting to the OS.
- **Material injects its component styles AFTER `styles.scss`**, so an equal-specificity
  rule loses. Redefining a **custom property in scope** wins where out-specifying does
  not:
  ```scss
  .mat-mdc-form-field { --mat-sys-primary: var(--color-focus); }
  ```
  Some paths ignore the token bridge entirely (the corner scale leaked three times;
  the menu shadow is hardcoded MDC elevation) — check the computed value, don't assume.
- Native `input[type=number]` spin buttons are hidden globally: they collide with a `%`
  suffix and let the scroll wheel rewrite a value. Hiding them is visual only — number
  inputs still need `(wheel)="$event.target.blur()"` to stop the wheel editing them.
- When binding dynamic colors from TypeScript to templates, use the **CSS custom property
  bridge pattern**:
  - Template: `[style.--_my-color]="colorValue"` (sets a scoped custom property inline).
  - SCSS: `background-color: var(--_my-color);` (consumes the property in stylesheet).
  - This avoids Angular style sanitization issues and keeps styling in CSS where it belongs.
- For transparent variants, use `color-mix(in srgb, var(--_my-color) 10%, transparent)`.
  **Exception:** a surface that CARRIES text must use a precomputed solid tint —
  `color-mix` resolves to `color(srgb ...)` and defeats contrast auditing.

### Gates
Before considering any visual work done:
1. **Accessibility (WCAG 2.2 AA)** — run the audit script from the `brq-secao` skill in
   the browser; zero `fail`. Then the interactive checks: keyboard, visible focus,
   `Escape`, ARIA state, `prefers-reduced-motion`.
2. **Craft** — review by image at 375 / 768 / 1440, in both themes.

**When measuring contrast, composite the alpha.** A colour like
`color(srgb 0.07 0.07 0.07 / 0.38)` is not a 7% grey — dropping the alpha channel
reports a passing ratio for text that fails. Blend against the actual surface first.
The `brq-secao` audit script has this bug; do not trust its numbers on any element
whose colour carries an alpha.

**Two traps when measuring in a browser:**
- An unfocused tab throttles repaint, so enter animations never complete and elements
  measure at their initial transform (a dialog reads as permanently `scale(0.8)`).
  Neutralise transitions before measuring.
- `resize_window` does not change `innerWidth` in this environment. To check a narrow
  layout, render the page in a same-origin `<iframe>` of the target width. Note the
  sidenav stays in `over` mode inside an iframe, so anything depending on the docked
  sidebar must be checked in the top-level window.

## Testing Guidelines
- Frontend tests live beside source as `*.spec.ts` and should be run with `docker compose exec client npx ng test`.
- Backend tests live under `Server/tests/` using `test_*.py` naming, organized by type:
  - `integration/`: API-level tests (routes end-to-end with test database).
  - `unit/`: isolated use-case and domain logic tests (mocked dependencies).
  - `architecture/`: fitness functions that enforce layer boundaries.
- Add tests for new behavior and regressions; prioritize route-level tests for API endpoints and critical UI flows.
- Follow TDD by default:
  1. Write a failing test that describes expected behavior.
  2. Implement the minimal code to pass.
  3. Refactor while keeping tests green.
- Every bug fix should start with a regression test reproducing the issue.
- Avoid merging feature work without automated test coverage for the new behavior.

## Engineering Principles
- Apply Clean Code practices:
  - Small functions/classes with descriptive names.
  - Early returns and low nesting to keep flow readable.
  - Avoid duplicated logic; extract shared behavior deliberately.
  - Prefer explicit code over implicit side effects.
- Apply Clean Architecture when it adds clarity and testability:
  - Business rules isolated from frameworks and I/O concerns.
  - External details (DB, HTTP, UI) plugged into core logic via interfaces.
  - Framework choices should not dictate domain model design.
- Balance pragmatism and purity: do not over-engineer, but preserve clear boundaries for code that is expected to evolve.

## Commit & Pull Request Guidelines
Adopt Conventional Commits:
- `feat: add portfolio endpoint`
- `fix: handle missing database_url`
- All commits must be authored solely by the repository owner. Never add `Co-Authored-By` trailers or any other attribution to AI agents/assistants.

PRs should include:
- Clear summary and scope.
- Linked issue/ticket (if available).
- Test evidence (`docker compose exec client npx ng test`, `docker compose exec server pytest`, API checks, or manual verification steps).
- Screenshots/GIFs for UI changes.

## Security & Configuration Tips
- Keep secrets only in `.env` (already gitignored); never commit credentials.
- Validate `DATABASE_URL` and related env vars before running migrations.
