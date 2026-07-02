# Git Push Notes — Why pushes were timing out

## Root cause (July 2026)

**CAUSE A: Large binary files in git history exceeded GitHub's 100 MB per-file hard limit.**

Two raw dataset files were committed directly to the repo:

| File | Size | Status |
|---|---|---|
| `data/real/real_cardealer_auto_sales.csv` | 221 MB | over GitHub 100 MB limit |
| `data/real/real_retail_general.csv` | 161 MB | over GitHub 100 MB limit |

GitHub silently rejects any push pack containing objects over 100 MB.
The push would hang at the "uploading" stage and then time out.
No amount of `http.postBuffer` or protocol changes can work around a per-file size limit.

## Fix applied (2026-07-02)

1. Installed `git-filter-repo` (pip install git-filter-repo)
2. Created safety bundle: `../datacore_safety_backup_2026-07-02.bundle`
3. Rewrote history to remove `data/real/` from all commits:

```bash
git filter-repo --path data/real/ --invert-paths --force
```

4. Re-added remote (filter-repo removes it as a safety measure):

```bash
git remote add origin https://github.com/No6Name8/Project_DataCore.git
```

5. Force-pushed the rewritten history:

```bash
git push --force origin main
```

**Before:** 462 MB pack, 43 commits with `data/real/` in history  
**After:** ~58 MB pack, same 43 commits without `data/real/` in history

## Prevention

`data/real/` is now in `.gitignore`. Raw datasets should **never** be committed.

To re-download the validation datasets:

```bash
bash scripts/download_real_datasets.sh
```

## If this happens again

Signs: `git push` hangs and times out, never reaches "Writing objects".

Diagnose with:
```bash
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '$1=="blob" && $3 >= 10485760 {print $3, $4}' | sort -rn | head -20
```

Fix: repeat the filter-repo steps above.
