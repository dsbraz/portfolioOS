# Repository Guidelines

Scope note: at this stage, this guide covers local development workflows only.

## Project Structure & Module Organization
This repository is split into two apps plus infrastructure:
- `Client/`: Angular frontend (`src/` for app code, `public/` for static assets, `angular.json` for build/test targets).
- `Server/`: FastAPI backend (`app/controllers/` for routes, `app/services/` for business orchestration, `app/repositories/` for persistence, `app/domain/` for models/schemas, `alembic/` for migrations).
- `docker-compose.yml`: local stack (client, server, PostgreSQL).

Keep frontend and backend changes scoped to their folders; shared API contracts should be updated in both sides in the same PR.

## Application Layers & Responsibilities
Use clear boundaries between layers and keep dependencies pointing inward.

### Backend (`Server/app`)
- `controllers/` (Presentation/API layer): define HTTP routes, validate/parse request/response contracts, map errors to HTTP status codes. Keep controllers thin; no business rules here.
- `services/` (Application/Domain services layer): implement business operations, orchestrate domain rules, and coordinate repository ports.
- `domain/` (Domain layer): entities and business rules; keep business logic framework-light even when persistence models use SQLAlchemy.
- `repos/` or `repositories/` (Persistence layer): database access and persistence implementations. Never leak ORM or infra details into domain models.
- `alembic/`: schema evolution only. Migrations must reflect domain/infrastructure changes and be versioned with code.

Backend flow (required): `controllers -> service -> domain -> repos`.

### Frontend (`Client/src`)
- `pages`/route components (Presentation layer): compose screens and user interactions.
- `components` (UI layer): reusable visual building blocks with minimal business logic.
- `services` (Application/data-access layer): API communication, orchestration, and state transitions used by pages/components.
- `models`/`types` (Domain contract layer): explicit interfaces/types shared across features to avoid ad-hoc payloads.

### Layering Rules
- In backend, follow the chain strictly: `controllers -> service -> domain -> repos`.
- Route handlers must call services for business behavior; dependency wiring in controller modules can compose repositories/services.
- Domain logic should stay isolated from transport concerns and remain easily testable in isolation.
- Prefer dependency inversion (interfaces/protocols) when crossing boundaries.
- Keep modules cohesive: each file/class should have a single clear reason to change.

### Backend Import Boundaries
- **Services must never import `fastapi`** — no `HTTPException`, no `status`, no `Depends`. Services work exclusively with domain models, primitive types, and `dict`s.
- **Services must never import schemas** (`app.domain.schemas.*`). Schema validation and serialization belong in controllers.
- **Domain models and exceptions** (`app.domain.models.*`, `app.domain.exceptions`) are the shared language between layers.

### Error Handling Convention
- **Services** raise domain exceptions for business-rule violations: `ValueError` for invalid input, `ConflictError` (`app.domain.exceptions`) for state conflicts (e.g. duplicates).
- **Services** return `None` for not-found scenarios (e.g. `get_by_id` returns `Model | None`).
- **Controllers** catch domain exceptions and map them to HTTP status codes (`ValueError` → 400, `ConflictError` → 409, `None` → 404).
- **Controllers** own all existence checks: use FastAPI dependencies like `_verify_startup_exists` for parent-resource validation, or inline checks for entity lookups.

### Controller ↔ Service Data Flow
- **Input**: controllers convert schemas to domain models or `dict`s before calling services (e.g. `Startup(**data.model_dump())`, `data.model_dump(exclude_unset=True)`).
- **Output**: services return domain models; controllers convert to response schemas (e.g. `Response.model_validate(entity)`).
- **Entity resolution**: controllers look up and validate entities exist, then pass resolved domain objects to service methods (e.g. `service.update(entity, updates)` not `service.update(entity_id, updates)`).

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
- Prefer small, focused controllers/services and explicit names like `health_controller.py`.

## Theming & Color Conventions
- The app uses Angular Material 3 with `mat.theme()` (`primary: azure`, `tertiary: blue`, light mode).
- All colors must be defined as CSS custom properties (design tokens). Two categories:
  - **M3 system tokens** (`--mat-sys-*`): use for standard UI roles (surface, text, containers, outline, elevation).
  - **App-level tokens** (`--app-*`): defined in `Client/src/styles.scss` for domain-specific colors (status indicators, kanban columns) that M3 doesn't cover natively.
- Never hardcode hex/rgb colors in component SCSS or TypeScript. Reference tokens instead.
- When binding dynamic colors from TypeScript to templates, use the **CSS custom property bridge pattern**:
  - Template: `[style.--_my-color]="colorValue"` (sets a scoped custom property inline).
  - SCSS: `background-color: var(--_my-color);` (consumes the property in stylesheet).
  - This avoids Angular style sanitization issues and keeps styling in CSS where it belongs.
- For transparent variants of a color, use `color-mix(in srgb, var(--_my-color) 10%, transparent)` instead of hex suffix hacks.

## Testing Guidelines
- Frontend tests live beside source as `*.spec.ts` and should be run with `docker compose exec client npx ng test`.
- Backend tests should be added under `Server/tests/` using `test_*.py` naming.
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
