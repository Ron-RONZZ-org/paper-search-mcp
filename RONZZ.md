# ronzz fork notes

This repository is the ronzz.ORG fork of
[`openags/paper-search-mcp`](https://github.com/openags/paper-search-mcp).

- **Source of truth:** `forgejo.ronzz.org/ronzz-org/paper-search-mcp`
- **Mirror (CI):** `github.com/Ron-RONZZ-org/paper-search-mcp`
- **Container:** `ghcr.io/ron-ronzz-org/paper-search-mcp:sha-<short>` (linux/arm64)

## Differences from upstream

- Sci-Hub uses a mirror list (`sci-hub.ru`, `sci-hub.st`, `sci-hub.se`), not a
  single URL. Upstream defaults to `sci-hub.se`, which does not resolve from
  `ronzz-linux-server-2`; on 2026-11-19 `sci-hub.st` answered a DDoS-Guard 403
  from this host while `sci-hub.ru` served PDFs. The per-call
  `scihub_base_url` argument is tried first and then the list.
- `.github/workflows/image.yml` builds and publishes the arm64 image and runs
  two boot smokes (tool inventory, streamable-http startup).
- `PAPER_SEARCH_MCP_ALLOWED_HOSTS` / `PAPER_SEARCH_MCP_ALLOWED_ORIGINS`
  (comma-separated) widen FastMCP's DNS-rebinding allowlist. FastMCP pins a
  localhost-only list when the server object is constructed (its default host
  is `127.0.0.1`), so setting `--host 0.0.0.0` later is not enough: a client
  on a container network sending `Host: paper-search:8000` gets HTTP 421.
- Sci-Hub downloads try a **mirror list** in order: `sci-hub.ru`,
  `sci-hub.st`, `sci-hub.se`. A per-call `scihub_base_url` / `base_url` is
  tried first and then the list. `PAPER_SEARCH_MCP_SCIHUB_MIRRORS`
  (comma-separated) replaces the built-in list. A mirror that returns a PDF
  which does not match the expected title/DOI is skipped and its file deleted.

## Updating from upstream

```bash
git remote add upstream https://github.com/openags/paper-search-mcp.git  # once
git fetch upstream
git merge upstream/main
```

Keep the Sci-Hub default change on top; resolve conflicts in
`paper_search_mcp/server.py` and `paper_search_mcp/academic_platforms/sci_hub.py`.
