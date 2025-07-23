#!/usr/bin/env python3
"""
BetterGit Demo Script
Shows the major features of BetterGit in action.
"""

import subprocess
import sys
import os
import time
from pathlib import Path


def run_bettergit(cmd, description="", expect_input=False):
    """Run a BetterGit command and display the result."""
    print(f"\n🔸 {description}")
    print(f"Command: bit {cmd}")
    print("-" * 60)
    
    try:
        if expect_input:
            # For commands that expect user input, we'll show what would happen
            print("(This command would prompt for user input)")
            return
            
        # Use bytes mode and decode manually to handle encoding issues
        result = subprocess.run(
            f"bit {cmd}",
            shell=True,
            capture_output=True,
            timeout=10
        )
        
        # Safe decode function to handle multiple encodings
        def safe_decode(data):
            if not data:
                return ""
            for encoding in ['utf-8', 'cp1252', 'latin1']:
                try:
                    return data.decode(encoding)
                except (UnicodeDecodeError, AttributeError):
                    continue
            # Last resort: decode with replacement characters
            return str(data, 'utf-8', errors='replace')
        
        stdout = safe_decode(result.stdout)
        stderr = safe_decode(result.stderr)
        
        if stdout:
            print(stdout)
        if stderr:
            print(f"Error: {stderr}")
            
        if result.returncode == 0:
            print("✅ Command completed successfully")
        else:
            print("❌ Command failed")
            
    except subprocess.TimeoutExpired:
        print("⏰ Command timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    time.sleep(1)  # Small delay for readability


def main():
    """Run the BetterGit demonstration."""
    print("🚀 BetterGit Feature Demonstration")
    print("=" * 60)
    
    # Create demo directory
    demo_dir = Path("bettergit-demo")
    if demo_dir.exists():
        import shutil
        import stat
        
        # Handle Windows file permission issues
        def handle_remove_readonly(func, path, exc):
            if exc[1].errno == 5:  # Access denied
                os.chmod(path, stat.S_IWRITE)
                func(path)
            else:
                raise
        
        try:
            shutil.rmtree(demo_dir, onerror=handle_remove_readonly)
        except Exception as e:
            print(f"Warning: Could not remove existing directory: {e}")
            print("Continuing with existing directory...")
    
    if not demo_dir.exists():
        demo_dir.mkdir()
    
    os.chdir(demo_dir)
    
    print(f"Using demo directory: {demo_dir.absolute()}")
    
    # 1. Initialize repository
    run_bettergit("init --no-remote", "Initialize a new repository")
    
    # 2. Show status
    run_bettergit("status", "Check repository status")
    
    # 3. List components
    run_bettergit("list", "List all repository components")
    
    # 4. Create some files and save
    with open("example.py", "w") as f:
        f.write("""#!/usr/bin/env python3
def hello_world():
    print("Hello from BetterGit!")

if __name__ == "__main__":
    hello_world()
""")
    
    with open("README.md", "a") as f:
        f.write("\n\n## Features\n\n- Easy to use\n- Safe operations\n- Modern workflow\n")
    
    print("\n🔸 Created example.py and updated README.md")
    
    # 5. Save changes
    run_bettergit('save "Add example code and update README" --all', "Save changes")
    
    # 6. Create another file and save
    with open("config.yml", "w") as f:
        f.write("""app:
  name: "BetterGit Demo"
  version: "1.0.0"
  debug: false
""")
    
    run_bettergit('save "Add configuration file" --all', "Save configuration file")
    
    # 7. Show history
    run_bettergit("history", "Show action history")
    
    # 8. List saves
    run_bettergit("list saves", "List recent saves (commits)")
    
    # 9. Show graph
    run_bettergit("graph", "Show commit graph")
    
    # 10. Create a branch and switch
    subprocess.run("git branch feature-demo", shell=True, capture_output=True, encoding="utf-8")
    run_bettergit("switch feature-demo", "Switch to feature branch")
    
    # 11. Make changes on branch
    with open("feature.py", "w") as f:
        f.write("""# New feature implementation
def new_feature():
    return "This is a new feature!"
""")
    
    run_bettergit('save "Add new feature" --all', "Save feature changes")
    
    # 12. Switch back to main
    run_bettergit("switch main", "Switch back to main branch")
    
    # 13. List branches
    run_bettergit("list branches", "List all branches")
    
    # 14. Show final status
    run_bettergit("status", "Final repository status")
    
    # 15. Show cleanup preview
    run_bettergit("cleanup --dry-run", "Preview cleanup actions")
    
    # 16. Show configuration command (don't run it as it opens an editor)
    print(f"\n🔸 Configuration management")
    print(f"Command: bit config")
    print("-" * 60)
    print("(This command opens the configuration file in your default editor)")
    print("You can use it to customize accounts, defaults, and integrations.")
    time.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎉 BetterGit demonstration completed!")
    print("\nThis demo showed:")
    print("✅ Repository initialization")
    print("✅ Status checking")
    print("✅ File staging and commits (saves)")
    print("✅ History tracking")
    print("✅ Branch management")
    print("✅ Visual commit graph")
    print("✅ Repository cleanup")
    print("✅ Configuration management")
    
    print(f"\nDemo repository created at: {Path.cwd().absolute()}")
    print("You can explore it further with BetterGit commands!")


if __name__ == "__main__":
    main()
