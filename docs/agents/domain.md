# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root. In this repo it is a pointer to
  `docs/wiki/архитектура.md`; read that page and the wiki pages it links to.
- **`docs/wiki/index.md`** — catalog of the living project picture.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in. The directory does not
  exist yet; proceed silently.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest
creating them upfront.

## File structure

Single-context repo:

```
/
├── CONTEXT.md
├── docs/adr/
└── docs/wiki/
```

## Use the glossary's vocabulary

Use terms from `docs/wiki/глоссарий.md` (for example «менеджер», not «тренер»). Don't drift to
synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language
the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding.
