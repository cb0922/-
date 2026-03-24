#!/usr/bin/env python3
"""
比赛通知爬虫 - 智能启动器
功能：自动检测并安装依赖，支持断点续传和重试
"""
import sys
import os
import subprocess
import time

def print_header():
    print("=" * 60)
    print("       比赛通知爬虫 - 启动器")
    print("=" * 60)

def check_python():
    """检查 Python 版本"""
    print("\n[1/3] 检查 Python 环境...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"错误：需要 Python 3.8+，当前版本 {version.major}.{version.minor}")
        return False
    print(f"  Python {version.major}.{version.minor}.{version.micro} 正常")
    return True

def check_module_complete(module_name):
    """深度检查模块是否完整安装"""
    try:
        if module_name == "PyQt6":
            # PyQt6 需要特殊检查：只 import PyQt6 不够，需要检查 QtWidgets
            __import__(module_name)
            from PyQt6.QtWidgets import QApplication
            return True
        else:
            __import__(module_name)
            return True
    except ImportError:
        return False

def check_and_install_deps():
    """检查并安装依赖（带重试）"""
    print("\n[2/3] 检查依赖环境...")
    
    # 核心依赖列表（按重要性排序）
    # 格式: (检测名, 安装包名, 是否需要深度检查)
    required_packages = [
        ("PyQt6", "PyQt6>=6.4.0", True),
        ("aiohttp", "aiohttp>=3.8.0", False),
        ("beautifulsoup4", "beautifulsoup4>=4.11.0", False),
        ("pandas", "pandas>=1.5.0", False),
        ("openpyxl", "openpyxl>=3.0.0", False),
        ("tqdm", "tqdm>=4.64.0", False),
    ]
    
    # 检查每个包
    missing = []
    need_reinstall = []  # 安装损坏需要重装
    
    for module, package, deep_check in required_packages:
        if deep_check:
            is_ok = check_module_complete(module)
        else:
            try:
                __import__(module)
                is_ok = True
            except ImportError:
                is_ok = False
        
        if is_ok:
            print(f"  {module}: 已安装")
        else:
            # 检查是否是部分安装（PyQt6常见）
            try:
                __import__(module)
                print(f"  {module}: 安装不完整，需要修复")
                need_reinstall.append((module, package))
            except ImportError:
                print(f"  {module}: 未安装")
                missing.append(package)
    
    # 先修复损坏的安装
    if need_reinstall:
        print(f"\n[修复] 检测到 {len(need_reinstall)} 个损坏的依赖包...")
        for module, package in need_reinstall:
            print(f"\n  正在修复 {module}...")
            success = install_with_retry(package, force_reinstall=True)
            if not success:
                print(f"\n错误：{module} 修复失败")
                return False
    
    # 再安装缺失的依赖
    if missing:
        print(f"\n[安装] 需要安装 {len(missing)} 个依赖包...")
        print("提示：如果下载慢，可以按 Ctrl+C 取消，手动运行：")
        print("      pip install -r requirements_gui.txt -i https://pypi.tuna.tsinghua.edu.cn/simple")
        print()
        
        for package in missing:
            success = install_with_retry(package)
            if not success:
                print(f"\n错误：{package} 安装失败")
                return False
    
    if not missing and not need_reinstall:
        print("  所有依赖已就绪！")
    else:
        print("\n  ✓ 依赖处理完成！")
    
    return True

def install_with_retry(package, max_retries=3, force_reinstall=False):
    """带重试的安装函数"""
    package_name = package.split(">=")[0]
    
    for attempt in range(1, max_retries + 1):
        print(f"\n[{attempt}/{max_retries}] 正在安装 {package_name}...")
        
        # 尝试多个镜像源
        mirrors = [
            "https://pypi.tuna.tsinghua.edu.cn/simple",  # 清华
            "https://mirrors.aliyun.com/pypi/simple",     # 阿里云
            "https://pypi.org/simple",                     # 官方
        ]
        
        for mirror in mirrors:
            cmd = [
                sys.executable, "-m", "pip", "install",
                package,
                "-i", mirror,
                "--timeout", "120",
                "--retries", "3"
            ]
            
            # 如果是修复模式，强制重装
            if force_reinstall:
                cmd.append("--force-reinstall")
                cmd.append("--no-cache-dir")
            
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode == 0:
                    print(f"  安装成功！")
                    return True
                else:
                    # 检查是否已经安装
                    if "already satisfied" in result.stdout or "already satisfied" in result.stderr:
                        if force_reinstall:
                            print(f"  已安装但可能损坏，尝试强制重装...")
                            continue  # 强制重装时继续尝试
                        print(f"  已安装")
                        return True
                    
                    if "清华" in mirror:
                        print(f"  清华镜像失败，尝试阿里云...")
                    elif "阿里云" in mirror:
                        print(f"  阿里云镜像失败，尝试官方源...")
                    else:
                        # 简化错误输出
                        err = result.stderr[:150] if result.stderr else "未知错误"
                        print(f"  安装输出: {err}...")
                        
            except subprocess.TimeoutExpired:
                print(f"  安装超时，尝试其他镜像...")
            except Exception as e:
                print(f"  错误: {e}")
        
        if attempt < max_retries:
            print(f"  等待 3 秒后重试...")
            time.sleep(3)
    
    return False

def start_gui():
    """启动 GUI"""
    print("\n[3/3] 启动 GUI 界面...")
    
    try:
        # 再次检查 PyQt6（完整检查）
        from PyQt6.QtWidgets import QApplication
        print("  PyQt6 检查通过")
    except ImportError as e:
        print(f"\n  ✗ PyQt6 组件缺失: {e}")
        print("  正在尝试自动修复...")
        
        # 自动尝试修复
        success = install_with_retry("PyQt6>=6.4.0", force_reinstall=True)
        if success:
            print("  ✓ 修复完成，重新启动中...")
            time.sleep(1)
            # 递归调用自己重新尝试
            return start_gui()
        else:
            print("\n  ✗ 自动修复失败")
            print("  请手动运行以下命令修复：")
            print("    pip uninstall PyQt6 -y")
            print("    pip install PyQt6>=6.4.0 -i https://pypi.tuna.tsinghua.edu.cn/simple")
            return False
    
    # 启动主程序
    try:
        import app_gui
        app_gui.main()
        return True
    except Exception as e:
        print(f"\n  ✗ 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 关键：切换到脚本所在目录，确保工作目录正确
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"工作目录已切换至: {script_dir}")
    
    print_header()
    
    # 检查 Python
    if not check_python():
        input("\n按回车键退出...")
        return 1
    
    # 检查并安装依赖
    if not check_and_install_deps():
        print("\n" + "=" * 60)
        print("依赖安装失败，可能的解决方案：")
        print("1. 检查网络连接")
        print("2. 使用代理或 VPN")
        print("3. 手动安装：pip install -r requirements_gui.txt")
        print("=" * 60)
        input("\n按回车键退出...")
        return 1
    
    # 启动 GUI
    if not start_gui():
        input("\n按回车键退出...")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
