#!/usr/bin/env python3
"""
比赛通知爬虫 - 一键修复工具
功能：清理并重新安装所有依赖，解决安装损坏问题
"""
import sys
import os
import subprocess
import time
import shutil
from pathlib import Path

def print_header():
    """打印标题"""
    print("=" * 65)
    print("           比赛通知爬虫 - 一键修复工具")
    print("=" * 65)
    print()
    print("本工具将：")
    print("  1. 备份您的数据")
    print("  2. 清理损坏的依赖")
    print("  3. 重新安装所有依赖")
    print("  4. 验证安装并启动程序")
    print()

def check_python():
    """检查Python环境"""
    print("\n[1/5] 检查 Python 环境...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ✗ 需要 Python 3.8+，当前版本 {version.major}.{version.minor}")
        return False
    print(f"  ✓ Python {version.major}.{version.minor}.{version.micro} 正常")
    return True

def backup_data():
    """备份用户数据"""
    print("\n[2/5] 备份用户数据...")
    
    backup_dirs = ['data', 'pdfs', 'output', 'word_reports']
    backup_time = time.strftime("%Y%m%d_%H%M%S")
    backup_base = f"backup_{backup_time}"
    
    backup_count = 0
    for dir_name in backup_dirs:
        if os.path.exists(dir_name) and os.path.isdir(dir_name):
            try:
                backup_path = f"{backup_base}/{dir_name}"
                shutil.copytree(dir_name, backup_path, dirs_exist_ok=True)
                print(f"  ✓ 已备份: {dir_name}/ -> {backup_path}/")
                backup_count += 1
            except Exception as e:
                print(f"  ! 备份 {dir_name} 失败: {e}")
    
    if backup_count > 0:
        print(f"  ✓ 数据已备份到: {backup_base}/")
    else:
        print("  - 暂无数据需要备份")
    return True

def clean_dependencies():
    """清理损坏的依赖"""
    print("\n[3/5] 清理损坏的依赖...")
    
    # 需要清理的包列表
    packages_to_clean = [
        'PyQt6', 'PyQt6-Qt6', 'PyQt6-sip',
        'aiohttp', 'aiosignal', 'async-timeout', 'attrs', 'charset-normalizer', 'frozenlist', 'multidict', 'yarl',
        'beautifulsoup4', 'soupsieve',
        'pandas', 'numpy', 'python-dateutil', 'pytz',
        'openpyxl', 'et-xmlfile',
        'tqdm', 'colorama',
        'requests', 'urllib3', 'certifi', 'idna'
    ]
    
    print("  正在清理旧依赖（可能需要几分钟）...")
    
    # 先尝试卸载可能损坏的包
    for package in packages_to_clean:
        try:
            cmd = [sys.executable, "-m", "pip", "uninstall", package, "-y", "-q"]
            subprocess.run(cmd, capture_output=True, timeout=30)
        except:
            pass
    
    # 清理 pip 缓存
    try:
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                      capture_output=True, timeout=30)
        print("  ✓ 已清理 pip 缓存")
    except:
        pass
    
    # 删除 __pycache__ 目录
    pycache_count = 0
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                try:
                    shutil.rmtree(os.path.join(root, dir_name))
                    pycache_count += 1
                except:
                    pass
    
    if pycache_count > 0:
        print(f"  ✓ 已清理 {pycache_count} 个缓存目录")
    
    print("  ✓ 依赖清理完成")
    return True

def install_dependencies():
    """安装所有依赖"""
    print("\n[4/5] 安装依赖（这可能需要几分钟，请耐心等待）...")
    
    # 依赖包列表（按优先级排序）
    dependencies = [
        ("PyQt6", "PyQt6>=6.4.0"),
        ("numpy", "numpy>=1.24.0"),  # pandas 依赖
        ("pandas", "pandas>=1.5.0"),
        ("aiohttp", "aiohttp>=3.8.0"),
        ("beautifulsoup4", "beautifulsoup4>=4.11.0"),
        ("openpyxl", "openpyxl>=3.0.0"),
        ("tqdm", "tqdm>=4.64.0"),
        ("requests", "requests>=2.28.0"),
        ("lxml", "lxml>=4.9.0"),  # beautifulsoup4 的解析器
    ]
    
    # 镜像源列表
    mirrors = [
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "https://mirrors.aliyun.com/pypi/simple",
        "https://pypi.org/simple",
    ]
    
    success_count = 0
    failed_packages = []
    
    for idx, (name, package) in enumerate(dependencies, 1):
        print(f"\n  [{idx}/{len(dependencies)}] 安装 {name}...")
        
        installed = False
        for mirror in mirrors:
            cmd = [
                sys.executable, "-m", "pip", "install",
                package,
                "-i", mirror,
                "--timeout", "180",
                "--retries", "5",
                "--no-cache-dir",  # 不使用缓存，确保干净安装
                "-q"  # 安静模式
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    print(f"    ✓ {name} 安装成功")
                    installed = True
                    success_count += 1
                    break
                else:
                    error_msg = result.stderr[:100] if result.stderr else "未知错误"
                    if "清华" in mirror:
                        print(f"    ! 清华镜像失败，尝试阿里云...")
                    elif "阿里云" in mirror:
                        print(f"    ! 阿里云镜像失败，尝试官方源...")
                    else:
                        print(f"    ! 官方源失败: {error_msg}")
                        
            except subprocess.TimeoutExpired:
                print(f"    ! 安装超时，尝试其他镜像...")
            except Exception as e:
                print(f"    ! 错误: {e}")
        
        if not installed:
            print(f"    ✗ {name} 安装失败")
            failed_packages.append(name)
    
    print(f"\n  ----------------------------------------")
    print(f"  安装结果: {success_count}/{len(dependencies)} 成功")
    
    if failed_packages:
        print(f"  失败: {', '.join(failed_packages)}")
        return False
    
    print("  ✓ 所有依赖安装完成！")
    return True

def verify_and_launch():
    """验证安装并启动"""
    print("\n[5/5] 验证安装...")
    
    # 验证关键依赖
    checks = [
        ("PyQt6", lambda: __import__('PyQt6') and __import__('PyQt6.QtWidgets', fromlist=['QApplication'])),
        ("aiohttp", lambda: __import__('aiohttp')),
        ("beautifulsoup4", lambda: __import__('bs4')),
        ("pandas", lambda: __import__('pandas')),
        ("openpyxl", lambda: __import__('openpyxl')),
    ]
    
    all_ok = True
    for name, check_func in checks:
        try:
            check_func()
            print(f"  ✓ {name}")
        except Exception as e:
            print(f"  ✗ {name}: {e}")
            all_ok = False
    
    if not all_ok:
        print("\n  ✗ 部分依赖验证失败")
        return False
    
    print("\n  ✓ 所有依赖验证通过！")
    print("\n" + "=" * 65)
    print("              修复完成！正在启动程序...")
    print("=" * 65)
    time.sleep(2)
    
    # 启动主程序
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        import app_gui
        app_gui.main()
    except Exception as e:
        print(f"\n  ✗ 启动失败: {e}")
        print("\n  请尝试手动运行: python 启动器.py")
        return False
    
    return True

def main():
    print_header()
    
    # 确认执行
    print("⚠️  这将清理并重新安装所有依赖。")
    print("    您的爬取数据会被自动备份。")
    print()
    choice = input("是否继续? (Y/n): ").strip().lower()
    if choice and choice not in ('y', 'yes'):
        print("\n已取消")
        input("按回车键退出...")
        return 0
    
    # 执行修复流程
    steps = [
        ("检查环境", check_python),
        ("备份数据", backup_data),
        ("清理依赖", clean_dependencies),
        ("安装依赖", install_dependencies),
        ("验证启动", verify_and_launch),
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"\n{'=' * 65}")
                print(f"  ✗ 步骤 '{step_name}' 失败")
                print(f"{'=' * 65}")
                print("\n建议:")
                print("  1. 检查网络连接")
                print("  2. 关闭代理/VPN后重试")
                print("  3. 手动运行: pip install -r requirements_gui.txt")
                input("\n按回车键退出...")
                return 1
        except KeyboardInterrupt:
            print("\n\n用户取消")
            return 1
        except Exception as e:
            print(f"\n  ✗ 错误: {e}")
            import traceback
            traceback.print_exc()
            input("\n按回车键退出...")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
