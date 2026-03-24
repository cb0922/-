#!/usr/bin/env python3
"""
GUI问题诊断工具
"""
import sys
import os
import subprocess

# 确保在正确目录
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def check_file(filepath, desc):
    """检查文件是否存在"""
    exists = os.path.exists(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {desc}: {filepath}")
    return exists

def test_crawler_cli():
    """测试命令行爬虫"""
    print("\n[1] 测试命令行爬虫...")
    
    cmd = [
        sys.executable, "-u", "enhanced_crawler_v3_safe.py",
        "--urls", "urls.csv",
        "--mode", "doc",
        "--output", "./test_output"
    ]
    
    print(f"  命令: {' '.join(cmd)}")
    print(f"  工作目录: {os.getcwd()}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=script_dir
        )
        print(f"  返回码: {result.returncode}")
        
        if result.returncode == 0:
            print("  ✓ CLI测试通过")
        else:
            print("  ✗ CLI测试失败")
            print(f"  错误输出:\n{result.stderr[:500]}")
            
        # 显示输出前20行
        lines = result.stdout.split('\n')[:20]
        print("  输出预览:")
        for line in lines:
            if line.strip():
                print(f"    {line}")
                
    except subprocess.TimeoutExpired:
        print("  ⚠ 测试超时（60秒）")
    except Exception as e:
        print(f"  ✗ 测试异常: {e}")

def test_document_handler():
    """测试文档处理器"""
    print("\n[2] 测试文档处理器...")
    
    try:
        sys.path.insert(0, script_dir)
        from core.document_handler import DocumentHandler
        
        handler = DocumentHandler(output_dir="test_output/documents")
        print("  ✓ DocumentHandler初始化成功")
        
        # 检查输出目录
        for doc_type in ['PDF', 'Word', 'Excel', 'PowerPoint', 'Archive', 'Text', 'WPS', 'Other']:
            dir_path = os.path.join("test_output/documents", doc_type)
            if os.path.exists(dir_path):
                print(f"  ✓ 目录存在: {doc_type}")
            else:
                print(f"  ⚠ 目录不存在: {doc_type}")
                
    except Exception as e:
        print(f"  ✗ DocumentHandler测试失败: {e}")
        import traceback
        traceback.print_exc()

def test_asyncio():
    """测试异步环境"""
    print("\n[3] 测试异步环境...")
    
    try:
        import asyncio
        import aiohttp
        
        async def test():
            return "asyncio OK"
        
        result = asyncio.run(test())
        print(f"  ✓ {result}")
        print(f"  ✓ aiohttp版本: {aiohttp.__version__}")
        
        # 检查nest_asyncio
        try:
            import nest_asyncio
            print("  ✓ nest_asyncio已安装")
        except ImportError:
            print("  ⚠ nest_asyncio未安装（可能需要）")
            
    except Exception as e:
        print(f"  ✗ 异步测试失败: {e}")

def check_permissions():
    """检查目录权限"""
    print("\n[4] 检查目录权限...")
    
    test_dirs = [".", "./output", "./test_output"]
    
    for dir_path in test_dirs:
        try:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # 测试写权限
            test_file = os.path.join(dir_path, "_test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"  ✓ {dir_path}: 可读写")
        except Exception as e:
            print(f"  ✗ {dir_path}: {e}")

def main():
    print("=" * 60)
    print("       GUI爬虫问题诊断工具")
    print("=" * 60)
    
    # 检查必要文件
    print("\n[0] 检查必要文件...")
    files_ok = True
    files_ok &= check_file("urls.csv", "URL文件")
    files_ok &= check_file("enhanced_crawler_v3_safe.py", "爬虫脚本(safe)")
    files_ok &= check_file("enhanced_crawler_v3.py", "爬虫脚本(v3)")
    files_ok &= check_file("app_gui.py", "GUI脚本")
    files_ok &= check_file("core/document_handler.py", "文档处理器")
    
    if not files_ok:
        print("\n  ✗ 部分必要文件缺失！")
    
    # 运行各项测试
    test_crawler_cli()
    test_document_handler()
    test_asyncio()
    check_permissions()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n建议:")
    print("1. 如果CLI测试失败，检查依赖: pip install -r requirements_gui.txt")
    print("2. 如果DocumentHandler失败，检查core目录是否完整")
    print("3. 如果权限检查失败，尝试以管理员身份运行")
    print("4. 查看test_output目录中的输出文件")

if __name__ == "__main__":
    main()
