# ronzz fork notes

This repository is the ronzz.ORG fork of
[`openags/paper-search-mcp`](https://github.com/openags/paper-search-mcp).

- **Source of truth:** `forgejo.ronzz.org/ronzz-org/paper-search-mcp`
- **Mirror (CI):** `github.com/Ron-RONZZ-org/paper-search-mcp`
- **Container:** `ghcr.io/ron-ronzz-org/paper-search-mcp:sha-<short>` (linux/arm64)

## Differences from upstream

- The default Sci-Hub mirror is `https://sci-hub.st`. Upstream defaults to
  `https://sci-hub.se`, which does not resolve from `ronzz-linux-server-2`.
  The per-call `scihub_base_url` argument still overrides it.
- `.github/workflows/image.yml` builds and publishes the arm64 image and runs
  two boot smokes (tool inventory, streamable-http startup).

## Updating from upstream

```bash
git remote add upstream https://github.com/openags/paper-search-mcp.git  # once
git fetch upstream
git merge upstream/main
```

Keep the Sci-Hub default change on top; resolve conflicts in
`paper_search_mcp/server.py` and `paper_search_mcp/academic_platforms/sci_hub.py`.
