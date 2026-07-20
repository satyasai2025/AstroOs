# SDK Versioning & API Stability Policy

Applies to `astroos` (PyPI) and `@astroos/sdk` (npm).

## Version scheme

Semantic Versioning 2.0.0, kept in lockstep with the platform release
(current: **2.2.0**). Both SDKs always share the same version number.

- **MAJOR** — breaking change to any public SDK symbol or to the wire
  contract it encodes (renamed method, removed field, changed default).
- **MINOR** — new endpoints/methods/fields, fully backward compatible.
- **PATCH** — bug fixes, doc/type improvements, no API surface change.

## Public API surface

Python: everything exported by `astroos.__all__`.
TypeScript: everything exported from the package root (`dist/types/index.d.ts`).
Anything prefixed `_` is internal and may change without notice.

## Stability rules

1. Breaking changes require a major version and one minor release of prior
   deprecation warning wherever technically possible.
2. Deprecated symbols keep working for at least one major cycle; Python uses
   `DeprecationWarning`, TypeScript uses `@deprecated` TSDoc.
3. New platform endpoints appear in SDKs as minor releases; the SDK version
   documents the minimum platform version it targets.
4. Error taxonomy (`AstroOSError` subclasses / thrown error shapes) is part
   of the public API.

## Support window

Latest major receives features and fixes; previous major receives security
and correctness fixes for 6 months after the new major ships.
