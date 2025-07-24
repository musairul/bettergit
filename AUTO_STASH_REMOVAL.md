# Auto-Stash Feature Removal

## Summary
The automatic stashing feature has been completely removed from BetterGit due to issues where it was breaking functionality. 

## Changes Made

### Code Changes
1. **`_switch_branch()` function** - Removed auto-stash logic before switching branches
2. **`pull` command** - Removed auto-stash logic before pulling changes
3. **`sync` command** - Removed auto-stash logic during synchronization

### Documentation Updates
1. **README.md** - Removed references to automatic stashing
2. **specification.md** - Removed "Automatic Stashing" section  
3. **USAGE_GUIDE.md** - Removed auto-stashing from safety features
4. **IMPLEMENTATION_SUMMARY.md** - Removed auto-stashing from features list

## Impact
- Users will now need to manually stash changes before operations that require a clean working directory
- The `bit stash` command is still available for manual stashing
- All other safety features (undo system, confirmation prompts) remain intact
- Operations that previously auto-stashed will now fail with Git's standard error messages if there are uncommitted changes

## Manual Stashing
Users can still stash changes manually using:
```bash
bit stash "message"     # Stash with a message
bit stash              # Stash without a message
git stash pop          # Restore stashed changes
```

## Date
Auto-stash feature removed on July 23, 2025
