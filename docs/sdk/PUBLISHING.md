# Publishing the SDKs (maintainer guide)

Both packages are verified build-clean (Phase II.3, 2026-07-20):
Python sdist+wheel pass `twine check`; TypeScript builds dual CJS/ESM with
type declarations and passes require/import smoke tests.

Publishing is a **manual, credentialed step** — never run by automation.

## Python → PyPI (`astroos`)

```bash
cd sdks/python
python -m pip install --upgrade build twine
python -m build            # dist/astroos-<ver>.tar.gz + .whl
python -m twine check dist/*
python -m twine upload dist/*        # needs PyPI API token (~/.pypirc or prompt)
```

Verify: `pip install astroos` in a clean venv, then
`python -c "from astroos import AstroOSClient"`.

## TypeScript → npm (`@astroos/sdk`)

```bash
cd sdks/typescript/astroos
npm ci        # or npm install
npm publish   # prepublishOnly runs the dual CJS/ESM/types build; needs npm login
```

Verify: `npm install @astroos/sdk` in a clean directory; both
`require("@astroos/sdk")` and `import("@astroos/sdk")` must resolve.

## Checklist per release

1. Bump `version` in `sdks/python/pyproject.toml` and
   `sdks/typescript/astroos/package.json` (lockstep — see VERSIONING.md).
2. Update quickstarts in `docs/sdk/` if the API surface changed.
3. Tag: SDK releases ride the platform tag (e.g., `v2.2.0`).
4. Publish Python, then npm, then smoke-test both installs.
