#!/usr/bin/env python3
"""
动态爬虫环境安装脚本
安装Playwright和浏览器依赖
"""
import subprocess
import sys


def install_playwright():
    """安装Playwright"""
    print("=" * 60)
    print("Installing Playwright for Dynamic Content Crawling")
    print("=" * 60)
    
    # 安装playwright包
    print("\n[1/2] Installing playwright package...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        print("  [OK] Package installed")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed to install package: {e}")
        return False
    
    # 安装浏览器
    print("\n[2/2] Installing browser binaries...")
    try:
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("  [OK] Chromium browser installed")
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] Failed to install browser: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Installation completed!")
    print("=" * 60)
    print("\nYou can now use --dynamic flag for JavaScript-heavy websites")
    return True


def check_playwright():
    """检查Playwright是否已安装"""
    try:
        import playwright
        print("[OK] Playwright is installed")
        return True
    except ImportError:
        print("[NOT FOUND] Playwright is not installed")
        return False


if __name__ == "__main__":
    if check_playwright():
        response = input("\nPlaywright is already installed. Reinstall? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled")
            sys.exit(0)
    
    success = install_playwright()
    sys.exit(0 if success else 1)
