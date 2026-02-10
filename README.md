# agent-skills

Version-controlled source of truth for custom Codex skills.

## Intended Use

- Keep all editable skill content in this repository.
- Expose skills to Codex by symlinking from `~/.codex/skills/<skill-name>` to this repo.
- Do not maintain separate editable copies in both places.

This prevents drift between a local runtime copy and the Git-tracked source.

## Source of Truth Model

- Git source: this repo (`/Users/chris/projects/agent-skills`)
- Runtime location: `~/.codex/skills`
- Runtime entries should be symlinks pointing back to this repo.

## One-Time Setup (Per Skill)

Example for `childrens-book-creator`:

```bash
mv ~/.codex/skills/childrens-book-creator ~/.codex/skills/childrens-book-creator.bak-$(date +%Y%m%d-%H%M%S)
ln -s /Users/chris/projects/agent-skills/childrens-book-creator ~/.codex/skills/childrens-book-creator
ls -l ~/.codex/skills/childrens-book-creator
```

Expected output pattern:

```text
... ~/.codex/skills/childrens-book-creator -> /Users/chris/projects/agent-skills/childrens-book-creator
```

## Daily Workflow

1. Edit skill files in this repo only.
2. Test/use the skill through Codex (which reads the symlink target).
3. Commit and push changes from this repo.

## Add a New Skill

1. Create a new folder in this repo (for example, `my-skill/`).
2. Add `SKILL.md` (plus optional `agents/`, `scripts/`, `references/`, `assets/`).
3. Create/update the symlink in `~/.codex/skills/my-skill`.
4. Commit and push.

## Optional Drift Check

If a skill was copied instead of linked, compare trees:

```bash
diff -ru /Users/chris/projects/agent-skills/<skill-name>/ ~/.codex/skills/<skill-name>/
```

If they should be unified, replace the runtime folder with a symlink.

## Notes

- Symlinks are machine-local. Recreate them on a new machine.
- Keep real files in Git; avoid storing symlink-only skill folders as the sole source.
