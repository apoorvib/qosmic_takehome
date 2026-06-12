# CLAUDE.md — Claude Code adapter

**Read `AGENTS.md` first — it is the authoritative entry point.** This file only adds Claude Code-specific usage notes.

You are the Qosmic runtime audit agent. Given one Shopify URL, run Crawl → Reason → Write and produce `sample_output/<store>.md`.

## Claude Code specifics

- **Skills:** invoke the phase skills in order via the Skill tool — `crawl-storefront`, then `reason-audit`, then `write-report` (in `harness/skills/`).
- **Discovery:** use the **Playwright MCP** browser to open the homepage and read the nav during the crawl phase. You decide which surfaces matter; `extract.py` does the capture.
- **Screenshots:** in the reason phase, use the **Read tool on the saved PNGs** (`artifacts/<store>/**/screenshots/*.png`) for the visual-critique pass — you can see them; the crawl script cannot.
- **Scripts:** run `extract.py` and `validate.py` via the Bash tool (synchronous; wait for them, then read the artifacts).
- **WebSearch:** use it in the reason phase for the competitor analysis.

## Flow recap

```
crawl-storefront  → artifacts/<store>/ (manifest.json + page.json + screenshots)
reason-audit      → artifacts/<store>/reason/*.json
write-report      → sample_output/<store>.md
```

Everything else — the contract, the quality bars, the schemas, the safety rules — is in `AGENTS.md` and `harness/schemas/`.
