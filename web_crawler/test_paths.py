#!/usr/bin/env python3
"""
Path fix test script
Verify all path handling is correct
"""
import os
import sys

def test_paths():
    print("=" * 60)
    print("Path Fix Test")
    print("=" * 60)
    
    # Test 1: App directory
    print("\n[Test 1] App Directory")
    app_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"  app_dir = {app_dir}")
    assert os.path.exists(app_dir), "App directory does not exist!"
    print("  [OK] Pass")
    
    # Test 2: urls.csv path
    print("\n[Test 2] urls.csv Path")
    urls_file = os.path.join(app_dir, "urls.csv")
    print(f"  urls_file = {urls_file}")
    if os.path.exists(urls_file):
        print("  [OK] File exists")
    else:
        print("  [WARN] File not found (will be created when adding URLs)")
    
    # Test 3: Output directory path
    print("\n[Test 3] Output Directory Path")
    output_dir = os.path.normpath(os.path.join(app_dir, "./output"))
    print(f"  output_dir = {output_dir}")
    print(f"  Is absolute: {os.path.isabs(output_dir)}")
    print("  [OK] Pass")
    
    # Test 4: Crawler script path
    print("\n[Test 4] Crawler Script Path")
    crawler_script = os.path.join(app_dir, "enhanced_crawler_v3.py")
    print(f"  crawler_script = {crawler_script}")
    if os.path.exists(crawler_script):
        print("  [OK] File exists")
    else:
        print("  [ERROR] File not found!")
        return False
    
    # Test 5: Core module path
    print("\n[Test 5] Core Module Path")
    core_dir = os.path.join(app_dir, "core")
    print(f"  core_dir = {core_dir}")
    if os.path.exists(core_dir):
        print("  [OK] Directory exists")
    else:
        print("  [ERROR] Directory not found!")
        return False
    
    # Test 6: Import test
    print("\n[Test 6] Module Import Test")
    try:
        sys.path.insert(0, app_dir)
        from app_gui import MainWindow, CrawlerWorker
        print("  [OK] app_gui imported successfully")
        
        # Test MainWindow.app_dir
        from PyQt6.QtWidgets import QApplication
        app = QApplication(sys.argv)
        window = MainWindow()
        print(f"  MainWindow.app_dir = {window.app_dir}")
        assert window.app_dir == app_dir, "app_dir mismatch!"
        print("  [OK] MainWindow.app_dir correct")
        
    except Exception as e:
        print(f"  [ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_paths()
    input("\nPress Enter to exit...")
    sys.exit(0 if success else 1)
