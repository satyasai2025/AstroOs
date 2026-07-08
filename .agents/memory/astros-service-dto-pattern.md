---
name: AstroOS service DTO pattern
description: Services return frozen dataclass DTOs; routers convert to Pydantic schemas. Schemas never enter the service layer.
---

## Rule
Service layer (`apps/api/services/`) must never import from `apps/api/schemas/`. Router layer converts DTOs → Pydantic schemas.

## Why
Importing Pydantic HTTP transport schemas into the service layer violates Clean Architecture's dependency rule. Services are an inner layer; schemas are an outer (HTTP adapter) concern. The violation makes services aware of HTTP serialization details they should not know about.

## How to apply
- `apps/api/services/dtos.py` — frozen Python `@dataclass` DTOs: `AuthTokensDTO`, `UserDTO`, `AuthResultDTO`.
- Services return DTOs.
- `apps/api/routers/auth.py` contains `_dto_to_*_response()` converter functions that map DTOs → Pydantic schemas before returning from route handlers.
- Any new service must follow the same pattern. Add new DTOs to `dtos.py`, new converters to the relevant router.
