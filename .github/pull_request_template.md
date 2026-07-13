## Summary

-

## Release Risk

- [ ] Public API change
- [ ] Native bridge change
- [ ] Wheel/platform change
- [ ] Docs-only change
- [ ] No release risk

## Checks

- [ ] `uv run python scripts/bump_version.py --check`
- [ ] `uv run ruff check .`
- [ ] `uv run mypy python`
- [ ] `uv run coverage run -m pytest`
- [ ] `uv run coverage report`
- [ ] `uv run --group docs mkdocs build --strict`
- [ ] Native bridge built locally when needed
- [ ] Docker E2E considered when packaging/runtime changed

## Notes

-
