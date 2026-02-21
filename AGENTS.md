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
- `models`/`types` (Domain contract layer): explicit interfaces/types shared across features to avoid ad-hoc payloads.

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
