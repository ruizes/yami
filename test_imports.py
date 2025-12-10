#!/usr/bin/env python3
"""Test script to debug import issues"""

import sys
import traceback

print("Python version:", sys.version)
print()

# Test basic imports
try:
    import tkinter
    print("✓ tkinter imported successfully")
except Exception as e:
    print("✗ Error importing tkinter:")
    traceback.print_exc()

print()

try:
    import customtkinter
    print("✓ customtkinter imported successfully")
except Exception as e:
    print("✗ Error importing customtkinter:")
    traceback.print_exc()

print()

try:
    import vlc
    print("✓ vlc imported successfully")
except Exception as e:
    print("✗ Error importing vlc:")
    traceback.print_exc()

print()

try:
    import mutagen
    print("✓ mutagen imported successfully")
except Exception as e:
    print("✗ Error importing mutagen:")
    traceback.print_exc()

print()

try:
    import PIL
    print("✓ PIL imported successfully")
except Exception as e:
    print("✗ Error importing PIL:")
    traceback.print_exc()

print()

try:
    import spotdl
    print("✓ spotdl imported successfully")
except Exception as e:
    print("✗ Error importing spotdl:")
    traceback.print_exc()

print()
print("=" * 50)
print("Testing yami module imports...")

# Test importing yami modules
try:
    sys.path.insert(0, '.')
    from yami.music import MusicPlayer
    print("✓ yami.music imported successfully")
except Exception as e:
    print("✗ Error importing yami.music:")
    traceback.print_exc()
