# Git Hooks Setup

## Automatic Version Update on Commit

A Git pre-commit hook has been installed to automatically update the Perisai version information on every commit.

### What it does

When you run `git commit`, the hook automatically:

1. **Counts total commits** in the repository
2. **Gets today's date** (YYYY-MM-DD format)
3. **Updates README.md** with new version: `**Version:** Perisai v.XXXX (as of YYYY-MM-DD)`
4. **Updates telegram_bot.py** `/start` command with: `<b>Perisai v.XXXX</b> (as of YYYY-MM-DD)`
5. **Stages both files** to be included in your commit automatically

### How it works

The hook is located at: `.git/hooks/pre-commit`

**Format:** `Perisai v.XXXX` where XXXX is the zero-padded commit count
- Example: Perisai v.0001 (1st commit), Perisai v.0363 (363rd commit)

### Usage

Just commit normally - no changes needed:

```bash
git add .
git commit -m "Your commit message"
```

The hook runs automatically before the commit is finalized, updates version info, and includes the updates in your commit.

### Troubleshooting

If the hook doesn't run:

1. **Verify it's executable:**
   ```bash
   ls -la .git/hooks/pre-commit
   ```
   Should show `-rwxr-xr-x` (executable)

2. **If not executable, fix it:**
   ```bash
   chmod +x .git/hooks/pre-commit
   ```

3. **Skip the hook temporarily** (if needed):
   ```bash
   git commit --no-verify -m "Your message"
   ```

### Manual Version Update

If you need to manually update the version:

```bash
./update_version.sh
```

Or just commit again and the hook will update automatically on the next commit.

### Customization

To modify the hook behavior, edit `.git/hooks/pre-commit` and adjust:
- Version format string
- Which files to update
- Additional actions on commit

### Files Updated by Hook

- ✅ `README.md` - Top section version line
- ✅ `telegram_bot.py` - `/start` command welcome message

Both updates preserve the rest of the file content and only replace the version string.
