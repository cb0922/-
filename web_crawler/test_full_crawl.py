#!/usr/bin/env python3
"""
完整爬取测试脚本
"""
import sys
import os
import subprocess
import time
from datetime import datetime

def test_crawl():
    """测试爬取"""
    print("=" * 70)
    print("完整爬取测试")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 统计网址数
    import csv
    with open('urls.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        urls = list(reader)
    
    total = len(urls)
    print(f"总网址数: {total}")
    print(f"预计时间: {total * 3}秒 - {total * 10}秒 (约 {total * 3 // 60}-{total * 10 // 60} 分钟)")
    print()
    
    # 开始爬取
    start_time = time.time()
    
    cmd = [
        sys.executable, "-u", "enhanced_crawler.py",
        "--urls", "urls.csv",
        "--mode", "all",
        "--output", "./full_test_output"
    ]
    
    print(f"命令: {' '.join(cmd)}")
    print()
    
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore',
        bufsize=1
    )
    
    # 实时读取输出
    output_lines = []
    while True:
        line = process.stdout.readline()
        if not line:
            break
        
        line = line.strip()
        output_lines.append(line)
        print(line)
        
        # 每100行显示一次进度
        if len(output_lines) % 100 == 0:
            elapsed = time.time() - start_time
            print(f"\n[进度] 已输出 {len(output_lines)} 行，已用时 {elapsed:.1f} 秒\n")
    
    process.wait()
    
    elapsed = time.time() - start_time
    print()
    print("=" * 70)
    print(f"爬取结束")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总用时: {elapsed:.1f} 秒 ({elapsed/60:.1f} 分钟)")
    print(f"返回码: {process.returncode}")
    print("=" * 70)
    
    # 检查输出
    check_output()
    
    return process.returncode == 0

def check_output():
    """检查输出文件"""
    print("\n输出文件检查:")
    
    output_dirs = [
        'full_test_output',
        'full_test_output/data',
        'full_test_output/pdfs',
        'full_test_output/word_reports',
        'reports',
        'pdfs/competitions'
    ]
    
    for d in output_dirs:
        if os.path.exists(d):
            files = os.listdir(d)
            print(f"  {d}/: {len(files)} 个文件")
        else:
            print(f"  {d}/: 不存在")

if __name__ == "__main__":
    success = test_crawl()
    sys.exit(0 if success else 1)
