#!/usr/bin/env python3
"""
极简版GUI - 用于测试核心流程
"""
import sys
import os
import subprocess
import json
from datetime import datetime

# PyQt6导入
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QTextEdit, QComboBox, QCheckBox,
        QMessageBox, QProgressBar
    )
    from PyQt6.QtCore import Qt, QThread, pyqtSignal
except ImportError:
    print("错误: 需要安装PyQt6")
    print("运行: pip install PyQt6")
    sys.exit(1)


class SimpleCrawlerThread(QThread):
    """简化版爬虫线程"""
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, mode="all"):
        super().__init__()
        self.mode = mode
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
    def run(self):
        """运行爬虫"""
        try:
            self.log_signal.emit("=" * 50)
            self.log_signal.emit("开始爬虫测试...")
            self.log_signal.emit(f"模式: {self.mode}")
            self.log_signal.emit(f"工作目录: {self.script_dir}")
            
            # 使用start_crawler.py作为入口
            crawler_script = os.path.join(self.script_dir, "start_crawler.py")
            urls_file = os.path.join(self.script_dir, "urls.csv")
            output_dir = os.path.join(self.script_dir, "output")
            
            # 检查文件
            if not os.path.exists(urls_file):
                self.finished_signal.emit(False, f"URL文件不存在: {urls_file}")
                return
                
            self.log_signal.emit(f"URL文件: {urls_file}")
            self.log_signal.emit(f"爬虫脚本: {crawler_script}")
            self.log_signal.emit(f"输出目录: {output_dir}")
            
            # 构建命令 - 使用列表形式避免shell解析问题
            cmd = [
                sys.executable,
                crawler_script,
                "--urls", urls_file,
                "--mode", self.mode,
                "--output", output_dir,
                "--no-auto-remove"
            ]
            
            cmd_str = ' '.join(cmd)
            self.log_signal.emit(f"命令: {cmd_str}")
            self.log_signal.emit("-" * 50)
            
            # Windows环境变量
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # 启动子进程
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            self.log_signal.emit("启动子进程...")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                cwd=self.script_dir,
                env=env,
                creationflags=creationflags
            )
            
            self.log_signal.emit(f"子进程PID: {process.pid}")
            
            # 读取输出
            line_count = 0
            while True:
                line = process.stdout.readline()
                if not line:
                    # 检查进程是否结束
                    ret = process.poll()
                    if ret is not None:
                        break
                    continue
                    
                line = line.strip()
                if line:
                    self.log_signal.emit(line)
                    line_count += 1
                    
                    # 如果在GUI事件中处理太多日志会导致卡顿，限制一下
                    if line_count % 100 == 0:
                        self.msleep(10)
            
            # 等待进程结束
            return_code = process.wait(timeout=30)
            self.log_signal.emit("-" * 50)
            self.log_signal.emit(f"子进程结束，返回码: {return_code}")
            
            if return_code == 0:
                self.finished_signal.emit(True, f"爬虫完成！处理了{line_count}行输出")
            else:
                self.finished_signal.emit(False, f"爬虫失败，返回码: {return_code}")
                
        except Exception as e:
            import traceback
            error_msg = f"异常: {str(e)}\n{traceback.format_exc()}"
            self.log_signal.emit(error_msg)
            self.finished_signal.emit(False, str(e))


class SimpleMainWindow(QMainWindow):
    """极简主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("爬虫测试 - 极简版")
        self.setMinimumSize(800, 600)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 标题
        title = QLabel("比赛通知爬虫 - 极简测试版")
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 控制区
        control_layout = QHBoxLayout()
        
        # 模式选择
        control_layout.addWidget(QLabel("模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["all", "doc", "html"])
        control_layout.addWidget(self.mode_combo)
        
        # 开始按钮
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.setStyleSheet("background: #4CAF50; color: white; padding: 10px;")
        self.start_btn.clicked.connect(self.start_crawl)
        control_layout.addWidget(self.start_btn)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)  # 无限进度
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # 日志显示
        layout.addWidget(QLabel("日志:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("font-family: Consolas, monospace; font-size: 11px;")
        layout.addWidget(self.log_text)
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
        self.thread = None
        
    def start_crawl(self):
        """开始爬取"""
        self.log_text.clear()
        self.start_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.statusBar().showMessage("运行中...")
        
        mode = self.mode_combo.currentText()
        self.thread = SimpleCrawlerThread(mode)
        self.thread.log_signal.connect(self.append_log)
        self.thread.finished_signal.connect(self.crawl_finished)
        self.thread.start()
        
    def append_log(self, text):
        """添加日志"""
        self.log_text.append(text)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
    def crawl_finished(self, success, message):
        """爬取完成"""
        self.start_btn.setEnabled(True)
        self.progress.setVisible(False)
        
        if success:
            self.statusBar().showMessage(f"完成: {message}")
            QMessageBox.information(self, "完成", message)
        else:
            self.statusBar().showMessage(f"失败: {message}")
            QMessageBox.critical(self, "错误", message)


def main():
    app = QApplication(sys.argv)
    window = SimpleMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
