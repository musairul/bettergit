#!/usr/bin/env python3
"""
Setup script to enable better Unicode support for BetterGit on Windows.
Run this before using BetterGit for the best experience.
"""

import os
import sys
import subprocess


def setup_unicode_support():
    """Configure environment for better Unicode support."""
    print("🔧 Setting up Unicode support for BetterGit...")
    
    # Set environment variables for UTF-8 support
    env_vars = {
        'PYTHONIOENCODING': 'utf-8',
        'PYTHONUTF8': '1',
    }
    
    print("\n📝 Setting environment variables:")
    for var, value in env_vars.items():
        os.environ[var] = value
        print(f"  {var}={value}")
    
    # Try to configure console for UTF-8 (Windows)
    if sys.platform == 'win32':
        print("\n🪟 Configuring Windows console...")
        try:
            # Try to set console to UTF-8 mode
            subprocess.run(['chcp', '65001'], check=True, capture_output=True)
            print("  ✅ Console set to UTF-8 mode (CP 65001)")
        except subprocess.CalledProcessError:
            print("  ⚠️  Could not change console code page")
        except FileNotFoundError:
            print("  ⚠️  chcp command not found")
    
    print("\n🧪 Testing Unicode support...")
    
    # Test Unicode characters
    test_chars = ['✓', '✗', '⚠', 'ℹ', '🌿', '📝', '❓', '✅', '📋', '💾', '🌐', '👤', '📦', '📊', '🔑', '🔒']
    working_chars = []
    failing_chars = []
    
    for char in test_chars:
        try:
            char.encode(sys.stdout.encoding or 'utf-8')
            print(f"  {char} - ✓", end="")
            working_chars.append(char)
        except (UnicodeEncodeError, LookupError):
            print(f"  ? - ✗", end="")
            failing_chars.append(char)
        print()
    
    print(f"\n📊 Results:")
    print(f"  ✅ Working: {len(working_chars)}/{len(test_chars)} Unicode characters")
    print(f"  ❌ Failed: {len(failing_chars)}/{len(test_chars)} Unicode characters")
    
    if len(working_chars) >= len(test_chars) * 0.8:  # 80% success rate
        print("\n🎉 Great! Your terminal has good Unicode support.")
        print("   BetterGit will use beautiful Unicode symbols.")
    else:
        print("\n⚠️  Limited Unicode support detected.")
        print("   BetterGit will use ASCII fallback symbols.")
    
    print("\n💡 Tips for better Unicode support:")
    print("   1. Use Windows Terminal instead of Command Prompt")
    print("   2. Use a font that supports Unicode (e.g., Cascadia Code, Fira Code)")
    print("   3. Set your terminal to UTF-8 encoding")
    
    print("\n🚀 Setup complete! You can now use BetterGit:")
    print("   bit --help")
    print("   bit status")
    print("   bit list")


if __name__ == "__main__":
    setup_unicode_support()
