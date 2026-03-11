#!/usr/bin/env python3
"""
Clean up FUZZY/plots directory completely.
Removes all plot files and the directory itself.
"""

import os
import sys
import shutil
from pathlib import Path

def get_plots_directory():
    """Get the FUZZY/plots directory."""
    plots_dir = Path('./FUZZY/plots')
    if not plots_dir.exists():
        print(f"❌ Directory not found: {plots_dir}")
        return None
    return plots_dir

def main():
    plots_dir = get_plots_directory()
    
    if not plots_dir:
        sys.exit(1)
    
    print("\n" + "="*80)
    print("FUZZY/PLOTS CLEANUP TOOL - COMPLETE REMOVAL")
    print("="*80)
    
    print(f"\n📁 Directory: {plots_dir.absolute()}")
    
    # Count files
    all_files = list(plots_dir.glob('*'))
    file_count = len([f for f in all_files if f.is_file()])
    dir_count = len([f for f in all_files if f.is_dir()])
    
    print(f"\n📊 Contents:")
    print(f"  Files: {file_count}")
    print(f"  Subdirectories: {dir_count}")
    
    if file_count > 0:
        print(f"\n📄 Files to be deleted:")
        for f in sorted([f for f in all_files if f.is_file()]):
            size_kb = f.stat().st_size / 1024
            print(f"    - {f.name:50s} ({size_kb:7.1f} KB)")
    
    if dir_count > 0:
        print(f"\n📁 Subdirectories to be deleted:")
        for d in sorted([f for f in all_files if f.is_dir()]):
            print(f"    - {d.name}/")
    
    print("\n" + "-"*80)
    print("⚠️  WARNING: This will delete ALL contents of FUZZY/plots and remove the directory!")
    print("-"*80 + "\n")
    
    try:
        # Calculate total size
        total_size_kb = sum(f.stat().st_size for f in all_files if f.is_file()) / 1024
        
        # Remove entire directory
        shutil.rmtree(plots_dir)
        
        print("="*80)
        print("✅ CLEANUP COMPLETE!")
        print(f"  Deleted directory: {plots_dir.name}")
        print(f"  Files removed: {file_count}")
        print(f"  Freed space: {total_size_kb:.1f} KB")
        print("="*80 + "\n")
    except Exception as e:
        print(f"❌ Error during deletion: {e}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()

