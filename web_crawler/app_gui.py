#!/usr/bin/env python3
"""
Web Crawler Desktop Application
比赛通知爬虫桌面应用程序 - GUI界面
"""
import sys
import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit, QTableWidget, QTableWidgetItem,
    QTabWidget, QFileDialog, QMessageBox, QProgressBar, QSpinBox,
    QComboBox, QCheckBox, QGroupBox, QSplitter, QSystemTrayIcon, QMenu,
    QStatusBar, QToolBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings
from PyQt6.QtGui import QAction, QIcon, QFont, QPixmap, QKeySequence
import asyncio


class CrawlerWorker(QThread):
    """爬虫工作线程"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, urls_file, mode="all", use_dynamic=False, output_dir="./output",
                 use_proxy=False, proxy_file="proxies.json", auto_remove=False):
        super().__init__()
        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 使用传入的路径（应该是绝对路径）
        self.urls_file = urls_file
        self.mode = mode
        self.use_dynamic = use_dynamic
        self.output_dir = output_dir
        self.use_proxy = use_proxy
        self.proxy_file = proxy_file
        self.auto_remove = auto_remove
        
        # 调试信息
        print(f"[CrawlerWorker] urls_file: {self.urls_file}")
        print(f"[CrawlerWorker] output_dir: {self.output_dir}")
        print(f"[CrawlerWorker] script_dir: {self.script_dir}")
        
    def run(self):
        """运行爬虫"""
        try:
            self.progress_signal.emit("Starting crawler...")
            
            # 获取脚本所在目录（绝对路径，避免工作目录问题）
            script_dir = os.path.dirname(os.path.abspath(__file__))
            crawler_script = os.path.join(script_dir, "enhanced_crawler_v3_safe.py")
            
            # 确保爬虫脚本存在
            if not os.path.exists(crawler_script):
                # 尝试备用文件
                crawler_script = os.path.join(script_dir, "enhanced_crawler_v3.py")
            
            # 检查爬虫脚本是否存在
            if not os.path.exists(crawler_script):
                self.finished_signal.emit(False, f"Crawler script not found: {crawler_script}")
                return
            
            # 检查urls文件是否存在
            if not os.path.exists(self.urls_file):
                self.finished_signal.emit(False, f"URLs file not found: {self.urls_file}")
                return
            
            # 构建命令（添加 -u 禁用Python缓冲，确保实时输出）
            cmd = [
                sys.executable, "-u", crawler_script,
                "--urls", self.urls_file,
                "--mode", self.mode,
                "--output", self.output_dir
            ]
            
            if self.use_dynamic:
                cmd.append("--dynamic")
            
            if self.use_proxy:
                cmd.append("--proxy")
                cmd.extend(["--proxy-file", self.proxy_file])
            
            # 安全模式：禁用自动删除
            if not self.auto_remove:
                cmd.append("--no-auto-remove")
            
            self.progress_signal.emit(f"Command: {' '.join(cmd)}")
            
            # 执行爬虫（Windows优化版本）
            # 使用creationflags防止子进程窗口弹出
            creationflags = 0
            if sys.platform == 'win32':
                creationflags = subprocess.CREATE_NO_WINDOW
            
            # 设置环境变量，确保Python在正确的路径下找模块
            env = os.environ.copy()
            env['PYTHONPATH'] = self.script_dir
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore',
                bufsize=1,
                creationflags=creationflags,
                cwd=self.script_dir,  # 设置工作目录
                env=env  # 传递环境变量
            )
            
            # 实时输出（Windows兼容方式）
            import time
            
            try:
                while True:
                    # 检查进程是否结束
                    ret = process.poll()
                    
                    # 读取所有可用的输出
                    while True:
                        try:
                            line = process.stdout.readline()
                            if not line:
                                break
                            self.progress_signal.emit(line.strip())
                        except:
                            break
                    
                    # 如果进程已结束，退出循环
                    if ret is not None:
                        break
                    
                    # 短暂休眠，避免CPU占用过高
                    time.sleep(0.01)
                
                # 等待进程完全结束
                process.wait(timeout=5)
                
            except Exception as e:
                self.progress_signal.emit(f"[WARN] Process monitoring error: {e}")
            
            if process.returncode == 0:
                self.finished_signal.emit(True, "Crawl completed successfully!")
            else:
                self.finished_signal.emit(False, f"Crawl failed with code {process.returncode}")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        # 关键：获取程序根目录（脚本所在目录）- 必须在其他初始化之前
        self.app_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"[GUI] 程序目录: {self.app_dir}")
        
        self.setWindowTitle("比赛通知爬虫 - Competition Notice Crawler")
        self.setMinimumSize(1200, 800)
        
        # 设置应用图标
        self.set_app_icon()
        
        # 初始化设置
        self.settings = QSettings("CrawlerApp", "Settings")
        
        # 创建UI
        self.init_ui()
        
        # 加载保存的网址
        self.load_urls()
        
        # 检查定时任务
        self.setup_scheduler()
        
        # 加载设置
        self.load_settings()
        
    def set_app_icon(self):
        """设置应用图标"""
        # 创建默认图标
        self.setWindowIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
        
    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建标签页
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # 添加各个标签页
        self.tabs.addTab(self.create_control_tab(), "控制台")
        self.tabs.addTab(self.create_urls_tab(), "网址管理")
        self.tabs.addTab(self.create_schedule_tab(), "定时任务")
        self.tabs.addTab(self.create_results_tab(), "结果查看")
        self.tabs.addTab(self.create_settings_tab(), "设置")
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_toolbar(self):
        """创建工具栏"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 开始爬取按钮
        start_action = QAction("开始爬取", self)
        start_action.setShortcut(QKeySequence("Ctrl+R"))
        start_action.triggered.connect(self.start_crawl)
        toolbar.addAction(start_action)
        
        toolbar.addSeparator()
        
        # 查看报告按钮
        report_action = QAction("查看报告", self)
        report_action.triggered.connect(self.open_latest_report)
        toolbar.addAction(report_action)
        
        # 查看Word按钮
        word_action = QAction("查看Word", self)
        word_action.triggered.connect(self.open_latest_word)
        toolbar.addAction(word_action)
        
        # 查看PDF按钮
        pdf_action = QAction("查看文档", self)
        pdf_action.triggered.connect(self.open_pdf_folder)
        toolbar.addAction(pdf_action)
        
    def create_control_tab(self):
        """创建控制台标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 控制面板
        control_group = QGroupBox("爬取控制")
        control_layout = QVBoxLayout(control_group)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("爬取模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["all - 全部(文档+报告)", "doc - 仅下载文档", "html - 仅生成报告"])
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        control_layout.addLayout(mode_layout)
        
        # 动态渲染选项
        self.dynamic_checkbox = QCheckBox("启用动态渲染 (Playwright) - 用于SPA网站")
        control_layout.addWidget(self.dynamic_checkbox)
        
        # 网址管理区域（控制面板快捷版）
        url_manage_group = QGroupBox("网址信息源管理")
        url_manage_layout = QVBoxLayout(url_manage_group)
        
        # 当前网址数量显示
        self.url_count_label = QLabel("当前网址数量: 0")
        url_manage_layout.addWidget(self.url_count_label)
        
        # 快速添加网址
        add_url_layout = QHBoxLayout()
        self.new_url_input = QLineEdit()
        self.new_url_input.setPlaceholderText("输入网址 (例如: https://example.com/notice)")
        add_url_layout.addWidget(self.new_url_input)
        
        self.new_url_name = QLineEdit()
        self.new_url_name.setPlaceholderText("名称/备注 (可选)")
        self.new_url_name.setMaximumWidth(150)
        add_url_layout.addWidget(self.new_url_name)
        
        quick_add_btn = QPushButton("添加")
        quick_add_btn.setStyleSheet("background-color: #10b981; color: white; padding: 5px 15px;")
        quick_add_btn.clicked.connect(self.quick_add_url)
        add_url_layout.addWidget(quick_add_btn)
        
        url_manage_layout.addLayout(add_url_layout)
        
        # 最近添加的网址列表（只显示前5个）
        self.recent_urls_list = QTextEdit()
        self.recent_urls_list.setReadOnly(True)
        self.recent_urls_list.setMaximumHeight(100)
        self.recent_urls_list.setPlaceholderText("最近添加的网址将显示在这里...")
        url_manage_layout.addWidget(self.recent_urls_list)
        
        # 操作按钮
        url_btn_layout = QHBoxLayout()
        
        view_all_btn = QPushButton("查看全部网址")
        view_all_btn.clicked.connect(lambda: self.tabs.setCurrentIndex(1))  # 切换到网址管理标签
        url_btn_layout.addWidget(view_all_btn)
        
        reload_btn = QPushButton("重新加载")
        reload_btn.clicked.connect(self.load_urls_to_control)
        url_btn_layout.addWidget(reload_btn)
        
        import_national_btn = QPushButton("导入全国网址库")
        import_national_btn.setStyleSheet("background-color: #f59e0b; color: white;")
        import_national_btn.clicked.connect(self.import_national_urls)
        url_btn_layout.addWidget(import_national_btn)
        
        url_btn_layout.addStretch()
        url_manage_layout.addLayout(url_btn_layout)
        
        control_layout.addWidget(url_manage_group)
        
        # 加载当前网址
        self.load_urls_to_control()
        
        # 按钮区域
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("开始爬取")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #9ca3af;
            }
        """)
        self.start_btn.clicked.connect(self.start_crawl)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_crawl)
        button_layout.addWidget(self.stop_btn)
        
        button_layout.addStretch()
        control_layout.addLayout(button_layout)
        
        # 进度显示区域（新增）
        progress_group = QGroupBox("抓取进度")
        progress_layout = QVBoxLayout(progress_group)
        
        # 总体进度
        progress_info_layout = QHBoxLayout()
        
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        progress_info_layout.addWidget(self.progress_label)
        
        self.progress_count_label = QLabel("0 / 0")
        self.progress_count_label.setStyleSheet("font-size: 14px; color: #2563eb;")
        progress_info_layout.addWidget(self.progress_count_label)
        
        progress_info_layout.addStretch()
        
        # 当前状态
        self.current_status_label = QLabel("等待开始...")
        self.current_status_label.setStyleSheet("color: #64748b;")
        progress_info_layout.addWidget(self.current_status_label)
        
        progress_layout.addLayout(progress_info_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        # 实时状态表格
        self.status_table = QTextEdit()
        self.status_table.setReadOnly(True)
        self.status_table.setMaximumHeight(120)
        self.status_table.setFont(QFont("Consolas", 9))
        self.status_table.setPlaceholderText("抓取状态将实时显示在这里...\n格式: [序号] 网址名称 - 状态")
        progress_layout.addWidget(self.status_table)
        
        control_layout.addWidget(progress_group)
        
        layout.addWidget(control_group)
        
        # 日志输出
        log_group = QGroupBox("运行日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        log_layout.addWidget(self.log_text)
        
        # 日志按钮
        log_btn_layout = QHBoxLayout()
        clear_btn = QPushButton("清空日志")
        clear_btn.clicked.connect(self.log_text.clear)
        log_btn_layout.addWidget(clear_btn)
        
        save_log_btn = QPushButton("保存日志")
        save_log_btn.clicked.connect(self.save_log)
        log_btn_layout.addWidget(save_log_btn)
        
        log_btn_layout.addStretch()
        log_layout.addLayout(log_btn_layout)
        
        layout.addWidget(log_group)
        
        return widget
        
    def create_urls_tab(self):
        """创建网址管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 说明
        info_label = QLabel("管理要爬取的网址列表。每行一个网址，支持CSV格式。")
        layout.addWidget(info_label)
        
        # 网址表格
        self.urls_table = QTableWidget()
        self.urls_table.setColumnCount(4)
        self.urls_table.setHorizontalHeaderLabels(["网址", "名称", "分类", "操作"])
        self.urls_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.urls_table)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("添加网址")
        add_btn.clicked.connect(self.add_url)
        btn_layout.addWidget(add_btn)
        
        import_btn = QPushButton("导入CSV")
        import_btn.clicked.connect(self.import_csv)
        btn_layout.addWidget(import_btn)
        
        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(export_btn)
        
        delete_btn = QPushButton("删除选中")
        delete_btn.clicked.connect(self.delete_selected_urls)
        btn_layout.addWidget(delete_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return widget
        
    def create_schedule_tab(self):
        """创建定时任务标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 启用定时任务
        self.schedule_checkbox = QCheckBox("启用定时自动爬取")
        layout.addWidget(self.schedule_checkbox)
        
        # 定时设置
        schedule_group = QGroupBox("定时设置")
        schedule_layout = QVBoxLayout(schedule_group)
        
        # 周期选择
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("运行周期:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems(["每天", "每周", "每月", "自定义小时"])
        period_layout.addWidget(self.period_combo)
        
        period_layout.addWidget(QLabel("时间/间隔:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 168)
        self.interval_spin.setValue(24)
        period_layout.addWidget(self.interval_spin)
        period_layout.addWidget(QLabel("小时"))
        period_layout.addStretch()
        
        schedule_layout.addLayout(period_layout)
        
        # 下次运行时间
        next_run_layout = QHBoxLayout()
        next_run_layout.addWidget(QLabel("下次运行:"))
        self.next_run_label = QLabel("未设置")
        next_run_layout.addWidget(self.next_run_label)
        next_run_layout.addStretch()
        schedule_layout.addLayout(next_run_layout)
        
        # 保存按钮
        save_schedule_btn = QPushButton("保存定时设置")
        save_schedule_btn.clicked.connect(self.save_schedule)
        schedule_layout.addWidget(save_schedule_btn)
        
        layout.addWidget(schedule_group)
        
        # 运行历史
        history_group = QGroupBox("运行历史")
        history_layout = QVBoxLayout(history_group)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(["时间", "状态", "文档数", "操作"])
        history_layout.addWidget(self.history_table)
        
        layout.addWidget(history_group)
        
        return widget
        
    def create_results_tab(self):
        """创建结果查看标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 快捷操作
        quick_group = QGroupBox("快捷操作")
        quick_layout = QHBoxLayout(quick_group)
        
        view_report_btn = QPushButton("查看最新HTML报告")
        view_report_btn.setStyleSheet("padding: 15px; font-size: 14px;")
        view_report_btn.clicked.connect(self.open_latest_report)
        quick_layout.addWidget(view_report_btn)
        
        view_word_btn = QPushButton("查看最新Word文档")
        view_word_btn.setStyleSheet("padding: 15px; font-size: 14px;")
        view_word_btn.clicked.connect(self.open_latest_word)
        quick_layout.addWidget(view_word_btn)
        
        view_pdf_btn = QPushButton("打开文档文件夹")
        view_pdf_btn.setStyleSheet("padding: 15px; font-size: 14px;")
        view_pdf_btn.clicked.connect(self.open_pdf_folder)
        quick_layout.addWidget(view_pdf_btn)
        
        refresh_btn = QPushButton("刷新结果")
        refresh_btn.setStyleSheet("padding: 15px; font-size: 14px;")
        refresh_btn.clicked.connect(self.refresh_results)
        quick_layout.addWidget(refresh_btn)
        
        layout.addWidget(quick_group)
        
        # 结果列表
        results_group = QGroupBox("爬取结果")
        results_layout = QVBoxLayout(results_group)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["时间", "网址数", "文档数", "报告", "操作"])
        results_layout.addWidget(self.results_table)
        
        layout.addWidget(results_group)
        
        return widget
        
    def create_settings_tab(self):
        """创建设置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 输出设置
        output_group = QGroupBox("输出设置")
        output_layout = QVBoxLayout(output_group)
        
        # 输出目录
        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel("输出目录:"))
        self.output_dir_edit = QLineEdit("./output")
        dir_layout.addWidget(self.output_dir_edit)
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(browse_btn)
        output_layout.addLayout(dir_layout)
        
        # 超时设置
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("请求超时(秒):"))
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        timeout_layout.addWidget(self.timeout_spin)
        timeout_layout.addStretch()
        output_layout.addLayout(timeout_layout)
        
        layout.addWidget(output_group)
        
        # 代理设置
        proxy_group = QGroupBox("代理设置")
        proxy_layout = QVBoxLayout(proxy_group)
        
        # 启用代理
        self.use_proxy_checkbox = QCheckBox("使用代理IP")
        self.use_proxy_checkbox.setChecked(False)
        self.use_proxy_checkbox.stateChanged.connect(self.on_proxy_enabled_changed)
        proxy_layout.addWidget(self.use_proxy_checkbox)
        
        # 代理类型
        proxy_type_layout = QHBoxLayout()
        proxy_type_layout.addWidget(QLabel("代理类型:"))
        self.proxy_type_combo = QComboBox()
        self.proxy_type_combo.addItems(["自动轮换", "HTTP", "HTTPS", "SOCKS5"])
        self.proxy_type_combo.setEnabled(False)
        proxy_type_layout.addWidget(self.proxy_type_combo)
        proxy_type_layout.addStretch()
        proxy_layout.addLayout(proxy_type_layout)
        
        # 代理文件
        proxy_file_layout = QHBoxLayout()
        proxy_file_layout.addWidget(QLabel("代理文件:"))
        self.proxy_file_edit = QLineEdit("proxies.json")
        self.proxy_file_edit.setEnabled(False)
        proxy_file_layout.addWidget(self.proxy_file_edit)
        self.proxy_browse_btn = QPushButton("浏览...")
        self.proxy_browse_btn.setEnabled(False)
        self.proxy_browse_btn.clicked.connect(self.browse_proxy_file)
        proxy_file_layout.addWidget(self.proxy_browse_btn)
        proxy_layout.addLayout(proxy_file_layout)
        
        # 添加代理按钮
        add_proxy_layout = QHBoxLayout()
        self.add_proxy_btn = QPushButton("添加代理...")
        self.add_proxy_btn.setEnabled(False)
        self.add_proxy_btn.clicked.connect(self.show_add_proxy_dialog)
        add_proxy_layout.addWidget(self.add_proxy_btn)
        
        self.test_proxy_btn = QPushButton("测试代理")
        self.test_proxy_btn.setEnabled(False)
        self.test_proxy_btn.clicked.connect(self.test_proxies)
        
        proxy_layout.addLayout(add_proxy_layout)
        
        layout.addWidget(proxy_group)
        
        # 安全设置
        safety_group = QGroupBox("安全设置")
        safety_layout = QVBoxLayout(safety_group)
        
        # 安全模式
        self.safe_mode_checkbox = QCheckBox("安全模式（推荐）")
        self.safe_mode_checkbox.setChecked(True)
        self.safe_mode_checkbox.setToolTip("禁用自动删除功能，避免大量网址失败时崩溃")
        safety_layout.addWidget(self.safe_mode_checkbox)
        
        # 自动删除选项（仅在非安全模式可用）
        self.auto_remove_checkbox = QCheckBox("自动删除失败网址（3次失败后）")
        self.auto_remove_checkbox.setChecked(False)
        self.auto_remove_checkbox.setEnabled(False)
        self.safe_mode_checkbox.stateChanged.connect(self.on_safe_mode_changed)
        safety_layout.addWidget(self.auto_remove_checkbox)
        
        # 说明
        safety_help = QLabel("""
            <p style='color: gray; font-size: 12px;'>
            安全模式：禁用自动删除，避免程序崩溃<br>
            关闭安全模式后可启用自动删除，但大量失败时可能崩溃
            </p>
        """)
        safety_help.setTextFormat(Qt.TextFormat.RichText)
        safety_layout.addWidget(safety_help)
        
        layout.addWidget(safety_group)
        add_proxy_layout.addWidget(self.test_proxy_btn)
        
        self.proxy_stats_btn = QPushButton("代理状态")
        self.proxy_stats_btn.setEnabled(False)
        self.proxy_stats_btn.clicked.connect(self.show_proxy_stats)
        add_proxy_layout.addWidget(self.proxy_stats_btn)
        
        add_proxy_layout.addStretch()
        proxy_layout.addLayout(add_proxy_layout)
        
        # 代理说明
        proxy_help = QLabel("""
            <p style='color: gray; font-size: 12px;'>
            提示：代理文件支持 JSON 或 TXT 格式（每行一个代理）<br>
            格式: http://user:pass@host:port 或 host:port
            </p>
        """)
        proxy_help.setTextFormat(Qt.TextFormat.RichText)
        proxy_layout.addWidget(proxy_help)
        
        layout.addWidget(proxy_group)
        
        # 关于信息
        about_group = QGroupBox("关于")
        about_layout = QVBoxLayout(about_group)
        
        about_text = QLabel("""
            <h3>比赛通知爬虫桌面版</h3>
            <p>版本: 2.0</p>
            <p>功能: 自动抓取比赛通知和公告文档(PDF/Word/Excel/PPT/压缩包)</p>
            <p>支持: 静态网页、动态渲染、定时任务</p>
        """)
        about_text.setTextFormat(Qt.TextFormat.RichText)
        about_layout.addWidget(about_text)
        
        layout.addWidget(about_group)
        layout.addStretch()
        
        return widget
        
    # ===== 功能方法 =====
    
    def start_crawl(self):
        """开始爬取"""
        # 使用绝对路径
        urls_file = os.path.join(self.app_dir, "urls.csv")
        if not os.path.exists(urls_file):
            QMessageBox.warning(self, "Warning", f"URL file not found: {urls_file}")
            return
        
        # 统计网址数量
        try:
            with open(urls_file, 'r', encoding='utf-8') as f:
                import csv
                reader = csv.reader(f)
                next(reader, None)  # 跳过标题
                self.total_urls = sum(1 for row in reader if row and row[0].strip())
        except:
            self.total_urls = 0
        
        # 获取设置
        mode = self.mode_combo.currentText().split(" - ")[0]
        use_dynamic = self.dynamic_checkbox.isChecked()
        
        # 处理输出目录（确保是绝对路径）
        output_dir = self.output_dir_edit.text()
        if not os.path.isabs(output_dir):
            # 规范化路径，处理 ./output 这样的情况
            output_dir = os.path.normpath(os.path.join(self.app_dir, output_dir))
        
        # 获取代理设置
        use_proxy = self.use_proxy_checkbox.isChecked()
        proxy_file = self.proxy_file_edit.text() or "proxies.json"
        # 处理代理文件路径（确保是绝对路径）
        if not os.path.isabs(proxy_file):
            proxy_file = os.path.normpath(os.path.join(self.app_dir, proxy_file))
        
        # 获取安全设置
        safe_mode = getattr(self, 'safe_mode_checkbox', None)
        if safe_mode:
            auto_remove = not safe_mode.isChecked()  # 安全模式开启时禁用自动删除
        else:
            auto_remove = False  # 默认禁用自动删除
        
        # 创建工作线程
        self.worker = CrawlerWorker(urls_file, mode, use_dynamic, output_dir, use_proxy, proxy_file, auto_remove)
        self.worker.progress_signal.connect(self.update_log)
        self.worker.finished_signal.connect(self.crawl_finished)
        
        # 初始化进度
        self.current_progress = 0
        self.success_count = 0
        self.fail_count = 0
        self.status_history = []
        
        # 更新UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_text.clear()
        self.status_table.clear()
        self.status_table.setText("等待爬虫启动...")
        
        # 设置进度条范围
        if self.total_urls > 0:
            self.progress_bar.setRange(0, self.total_urls)
            self.progress_bar.setValue(0)
            self.progress_label.setText("准备抓取...")
            self.progress_count_label.setText(f"0 / {self.total_urls}")
            self.current_status_label.setText("正在启动爬虫...")
        else:
            self.progress_bar.setRange(0, 0)  # 无限进度
        
        # 立即刷新UI
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        
        # 开始
        self.worker.start()
        self.status_bar.showMessage(f"正在爬取 {self.total_urls} 个网址...")
        
    def stop_crawl(self):
        """停止爬取"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Stopped")
        
    def update_log(self, message):
        """更新日志和进度"""
        # 添加到详细日志
        self.log_text.append(message)
        # 自动滚动到底部
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 解析进度信息
        self._parse_and_update_progress(message)
        
    def _parse_and_update_progress(self, message):
        """解析日志并更新进度显示"""
        import re
        
        # 0. 解析 "[PROGRESS]" - 爬虫的进度输出
        if "[PROGRESS]" in message:
            # 解析 "Completed: X/Y (Z%)"
            match = re.search(r'\[PROGRESS\]\s*(Completed|Failed|Error):\s*(\d+)/(\d+)', message)
            if match:
                status = match.group(1)
                current = int(match.group(2))
                total = int(match.group(3))
                
                self.current_progress = current
                if status == "Completed":
                    self.success_count += 1
                else:
                    self.fail_count += 1
                
                # 更新状态
                self.current_status_label.setText(f"正在抓取第 {current}/{total} 个...")
                
                # 更新进度条
                if self.total_urls > 0:
                    self.progress_bar.setValue(min(current, self.total_urls))
                    percent = (current / self.total_urls) * 100
                    self.progress_label.setText(f"正在抓取... {percent:.1f}%")
                    self.progress_count_label.setText(f"{current} / {self.total_urls}")
            
            # 解析 "Starting to crawl X URLs"
            match = re.search(r'Starting to crawl (\d+) URLs', message)
            if match:
                total = int(match.group(1))
                self.total_urls = total
                self.current_status_label.setText(f"开始爬取 {total} 个网址...")
                self.progress_bar.setRange(0, total)
            
            # 解析 "Crawl completed"
            if "Crawl completed" in message:
                self.current_status_label.setText("爬取完成！")
                self.progress_label.setText("抓取完成")
        
        # 1. 解析 "[OK] Title:" - 表示成功抓取一个页面
        elif "[OK] Title:" in message:
            # 提取标题
            match = re.search(r'\[OK\] Title:\s*(.+)', message)
            if match:
                title = match.group(1)[:40] + "..." if len(match.group(1)) > 40 else match.group(1)
                self._add_status_entry(f"✓ {title}")
                self.current_status_label.setText(f"成功: {title[:30]}...")
        
        # 2. 解析 "[FAIL]" - 抓取失败
        elif "[FAIL]" in message or "[Error]" in message:
            # 提取错误信息
            error_msg = message.replace("[FAIL]", "").replace("[Error]", "").strip()[:40]
            self._add_status_entry(f"✗ {error_msg}")
            self.current_status_label.setText(f"失败: {error_msg[:30]}...")
        
        # 3. 解析 "[DOC] Found" - 发现文档
        elif "[DOC] Found" in message or "[PDF] Found" in message:
            match = re.search(r'\[(?:DOC|PDF)\] Found (\d+)', message)
            if match:
                doc_count = match.group(1)
                self.current_status_label.setText(f"发现 {doc_count} 个文档附件")
        
        # 4. 解析 "[DOWNLOAD]" - 下载文档
        elif "[DOWNLOAD]" in message:
            self.current_status_label.setText("正在下载文档文件...")
        
        # 5. 解析 "[REPORT]" - 生成报告
        elif "[REPORT]" in message:
            self.current_status_label.setText("正在生成报告...")
        
        # 6. 解析 "Crawl completed" 或 "CRAWL COMPLETED"
        elif "completed" in message.lower() or "completed" in message.lower():
            self.current_status_label.setText("爬取完成！")
            self.progress_label.setText("抓取完成")
    
    def _add_status_entry(self, status_text):
        """添加状态条目到状态表格"""
        import datetime
        time_str = datetime.datetime.now().strftime("%H:%M:%S")
        entry = f"[{time_str}] {status_text}"
        self.status_history.append(entry)
        
        # 只保留最近20条
        if len(self.status_history) > 20:
            self.status_history = self.status_history[-20:]
        
        # 更新显示
        self.status_table.setText("\n".join(self.status_history))
        
        # 滚动到底部
        scrollbar = self.status_table.verticalScrollBar()
        if scrollbar:
            scrollbar.setValue(scrollbar.maximum())
    
    def crawl_finished(self, success, message):
        """爬取完成"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if success:
            self.progress_bar.setValue(self.total_urls if self.total_urls > 0 else 100)
            self.progress_label.setText("抓取完成")
            self.progress_count_label.setText(f"{self.current_progress} / {self.total_urls}")
            self.current_status_label.setText(f"成功:{self.success_count} 失败:{self.fail_count}")
            
            summary = f"""爬取完成！

统计信息：
• 总网址数: {self.total_urls}
• 成功: {self.success_count}
• 失败: {self.fail_count}
• 完成率: {(self.success_count/self.total_urls*100):.1f}%"""
            
            self.status_bar.showMessage("Crawl completed")
            QMessageBox.information(self, "Success", summary)
            self.refresh_results()
        else:
            self.progress_bar.setValue(0)
            self.progress_label.setText("抓取失败")
            self.current_status_label.setText("发生错误")
            self.status_bar.showMessage("Crawl failed")
            QMessageBox.critical(self, "Error", message)
            
    def open_latest_report(self):
        """打开最新报告"""
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            reports = sorted([f for f in os.listdir(reports_dir) if f.endswith('.html')])
            if reports:
                latest = os.path.join(reports_dir, reports[-1])
                os.startfile(os.path.abspath(latest))
            else:
                QMessageBox.information(self, "Info", "No reports found")
        else:
            QMessageBox.warning(self, "Warning", "Reports directory not found")
            
    def open_latest_word(self):
        """打开最新Word文档"""
        output_dir = self.output_dir_edit.text()
        word_dir = os.path.join(output_dir, "word_reports")
        if os.path.exists(word_dir):
            docs = sorted([f for f in os.listdir(word_dir) if f.endswith('.docx')])
            if docs:
                import webbrowser
                doc_path = os.path.abspath(os.path.join(word_dir, docs[-1]))
                webbrowser.open(f'file://{doc_path}')
                return
        QMessageBox.warning(self, "Warning", "No Word document found. Please run crawl first.")
            
    def open_pdf_folder(self):
        """打开文档文件夹"""
        # 使用GUI中设置的输出目录
        output_dir = self.output_dir_edit.text()
        doc_dir = os.path.join(output_dir, "documents")
        if os.path.exists(doc_dir):
            os.startfile(os.path.abspath(doc_dir))
            return
        # 如果目录不存在，尝试创建它
        try:
            os.makedirs(doc_dir, exist_ok=True)
            os.startfile(os.path.abspath(doc_dir))
            return
        except Exception:
            pass
        QMessageBox.warning(self, "Warning", f"Documents directory not found: {doc_dir}")
        
    def load_urls(self):
        """加载网址"""
        urls_file = os.path.join(self.app_dir, "urls.csv")
        if os.path.exists(urls_file):
            with open(urls_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]  # 跳过标题
                self.urls_table.setRowCount(len(lines))
                for i, line in enumerate(lines):
                    parts = line.strip().split(",")
                    for j, part in enumerate(parts[:3]):
                        self.urls_table.setItem(i, j, QTableWidgetItem(part))
    
    def load_urls_to_control(self):
        """加载网址到控制面板"""
        urls_file = os.path.join(self.app_dir, "urls.csv")
        urls = []
        if os.path.exists(urls_file):
            with open(urls_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[1:]  # 跳过标题
                self.url_count_label.setText(f"当前网址数量: {len(lines)}")
                
                # 显示最近5个
                recent = lines[-5:] if len(lines) > 5 else lines
                display_text = "最近添加的网址:\n"
                for i, line in enumerate(recent, 1):
                    parts = line.strip().split(",")
                    url = parts[0] if parts else ""
                    name = parts[1] if len(parts) > 1 else ""
                    display_text += f"{i}. {name[:20] if name else '未命名'} - {url[:50]}...\n"
                
                self.recent_urls_list.setText(display_text)
        else:
            self.url_count_label.setText("当前网址数量: 0 (未找到urls.csv)")
            self.recent_urls_list.setText("未找到网址文件，请添加网址")
    
    def quick_add_url(self):
        """快速添加网址"""
        url = self.new_url_input.text().strip()
        name = self.new_url_name.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Warning", "请输入网址")
            return
        
        # 验证URL格式
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        # 使用绝对路径
        urls_file = os.path.join(self.app_dir, "urls.csv")
        
        # 添加到CSV
        try:
            # 如果文件不存在，创建并写入标题
            if not os.path.exists(urls_file):
                with open(urls_file, "w", encoding="utf-8") as f:
                    f.write("url,name,category\n")
            
            # 检查是否已存在
            existing = []
            if os.path.exists(urls_file):
                with open(urls_file, "r", encoding="utf-8") as f:
                    existing = [line.strip().split(",")[0] for line in f.readlines()[1:]]
            
            if url in existing:
                QMessageBox.information(self, "Info", "该网址已存在")
                return
            
            # 添加新网址
            with open(urls_file, "a", encoding="utf-8") as f:
                name_str = name if name else ""
                f.write(f"{url},{name_str},\n")
            
            QMessageBox.information(self, "Success", f"已添加网址:\n{url}")
            
            # 清空输入框
            self.new_url_input.clear()
            self.new_url_name.clear()
            
            # 刷新显示
            self.load_urls_to_control()
            self.load_urls()  # 同时刷新网址管理标签页
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"添加失败: {e}")
    
    def import_national_urls(self):
        """导入全国电教馆和教科委网址库"""
        source_file = os.path.join(self.app_dir, "全国电教馆_教科委网址库.csv")
        
        if not os.path.exists(source_file):
            QMessageBox.warning(self, "Warning", f"未找到网址库文件:\n{source_file}")
            return
        
        # 读取网址库
        import csv
        urls_to_add = []
        try:
            with open(source_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    urls_to_add.append({
                        'url': row.get('url', '').strip(),
                        'name': row.get('name', '').strip(),
                        'category': row.get('category', '').strip()
                    })
        except Exception as e:
            QMessageBox.critical(self, "Error", f"读取网址库失败: {e}")
            return
        
        # 统计
        categories = {}
        for item in urls_to_add:
            cat = item['category'] or '未分类'
            categories[cat] = categories.get(cat, 0) + 1
        
        # 检查已存在的
        urls_file = os.path.join(self.app_dir, "urls.csv")
        existing_urls = set()
        if os.path.exists(urls_file):
            with open(urls_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row:
                        existing_urls.add(row[0].strip())
        
        new_urls = [u for u in urls_to_add if u['url'] not in existing_urls]
        duplicates = len(urls_to_add) - len(new_urls)
        
        # 显示确认对话框
        msg = f"网址库包含 {len(urls_to_add)} 个网址:\n\n"
        for cat, count in sorted(categories.items()):
            msg += f"  {cat}: {count} 个\n"
        
        if duplicates > 0:
            msg += f"\n其中 {duplicates} 个已存在，将跳过"
        
        msg += f"\n实际将导入: {len(new_urls)} 个新网址\n\n确认导入?"
        
        reply = QMessageBox.question(self, "确认导入", msg, 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 执行导入
        try:
            if not os.path.exists(urls_file):
                with open(urls_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['url', 'name', 'category'])
            
            with open(urls_file, 'a', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                for item in new_urls:
                    writer.writerow([item['url'], item['name'], item['category']])
            
            QMessageBox.information(self, "Success", 
                                    f"导入成功！\n\n已添加 {len(new_urls)} 个网址\n"
                                    f"当前共有 {len(existing_urls) + len(new_urls)} 个网址")
            
            # 刷新显示
            self.load_urls_to_control()
            self.load_urls()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"导入失败: {e}")
                    
    def add_url(self):
        """添加网址"""
        row = self.urls_table.rowCount()
        self.urls_table.insertRow(row)
        
    def import_csv(self):
        """导入CSV"""
        file_path, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if file_path:
            # 复制到urls.csv
            import shutil
            urls_file = os.path.join(self.app_dir, "urls.csv")
            shutil.copy(file_path, urls_file)
            self.load_urls()
            QMessageBox.information(self, "Success", "URLs imported successfully")
            
    def export_csv(self):
        """导出CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if file_path:
            import shutil
            urls_file = os.path.join(self.app_dir, "urls.csv")
            shutil.copy(urls_file, file_path)
            QMessageBox.information(self, "Success", "URLs exported successfully")
            
    def delete_selected_urls(self):
        """删除选中的网址"""
        current_row = self.urls_table.currentRow()
        if current_row >= 0:
            self.urls_table.removeRow(current_row)
            self.save_urls()
            
    def save_urls(self):
        """保存网址"""
        urls_file = os.path.join(self.app_dir, "urls.csv")
        with open(urls_file, "w", encoding="utf-8") as f:
            f.write("url,name,category\n")
            for row in range(self.urls_table.rowCount()):
                url = self.urls_table.item(row, 0)
                name = self.urls_table.item(row, 1)
                category = self.urls_table.item(row, 2)
                if url:
                    f.write(f"{url.text()},{name.text() if name else ''},{category.text() if category else ''}\n")
                    
    def save_schedule(self):
        """保存定时设置"""
        enabled = self.schedule_checkbox.isChecked()
        period = self.period_combo.currentText()
        interval = self.interval_spin.value()
        
        # 保存到设置
        self.settings.setValue("schedule/enabled", enabled)
        self.settings.setValue("schedule/period", period)
        self.settings.setValue("schedule/interval", interval)
        
        QMessageBox.information(self, "Success", "Schedule settings saved")
        
    def setup_scheduler(self):
        """设置定时任务"""
        # 加载设置
        enabled = self.settings.value("schedule/enabled", False, type=bool)
        if enabled:
            self.schedule_checkbox.setChecked(True)
            
        # 创建定时器
        self.scheduler_timer = QTimer(self)
        self.scheduler_timer.timeout.connect(self.on_scheduled_run)
        
        if enabled:
            interval = self.settings.value("schedule/interval", 24, type=int)
            self.scheduler_timer.start(interval * 3600 * 1000)  # 转换为毫秒
            
    def on_scheduled_run(self):
        """定时运行"""
        if self.schedule_checkbox.isChecked():
            self.start_crawl()
            
    def refresh_results(self):
        """刷新结果"""
        # 加载结果列表
        self.results_table.setRowCount(0)
        
        # 查找输出目录中的结果
        output_dirs = ["output", "pdfs", "reports"]
        results = []
        
        for output_dir in output_dirs:
            if os.path.exists(output_dir):
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        if file.endswith('.json'):
                            filepath = os.path.join(root, file)
                            mtime = os.path.getmtime(filepath)
                            results.append((filepath, mtime))
                            
        # 按时间排序
        results.sort(key=lambda x: x[1], reverse=True)
        
        # 添加到表格
        for filepath, mtime in results[:10]:
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            
            dt = datetime.fromtimestamp(mtime)
            self.results_table.setItem(row, 0, QTableWidgetItem(dt.strftime("%Y-%m-%d %H:%M")))
            self.results_table.setItem(row, 1, QTableWidgetItem("N/A"))
            self.results_table.setItem(row, 2, QTableWidgetItem("N/A"))
            self.results_table.setItem(row, 3, QTableWidgetItem(os.path.basename(filepath)))
            
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")
        if dir_path:
            self.output_dir_edit.setText(dir_path)
            
    def save_log(self):
        """保存日志"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Log", "crawler_log.txt", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())
            QMessageBox.information(self, "Success", "Log saved successfully")
    
    # ===== 代理管理方法 =====
    
    def on_proxy_enabled_changed(self, state):
        """代理启用状态改变"""
        enabled = state == Qt.CheckState.Checked.value
        self.proxy_type_combo.setEnabled(enabled)
        self.proxy_file_edit.setEnabled(enabled)
        self.proxy_browse_btn.setEnabled(enabled)
        self.add_proxy_btn.setEnabled(enabled)
        self.test_proxy_btn.setEnabled(enabled)
        self.proxy_stats_btn.setEnabled(enabled)
        
        # 保存设置
        self.settings.setValue("proxy/enabled", enabled)
    
    def on_safe_mode_changed(self, state):
        """安全模式改变"""
        safe_mode = state == Qt.CheckState.Checked.value
        # 安全模式开启时，禁用自动删除
        self.auto_remove_checkbox.setEnabled(not safe_mode)
        if safe_mode:
            self.auto_remove_checkbox.setChecked(False)
        
        # 保存设置
        self.settings.setValue("safety/safe_mode", safe_mode)
    
    def browse_proxy_file(self):
        """浏览代理文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择代理文件", "", 
            "JSON Files (*.json);;Text Files (*.txt);;All Files (*.*)"
        )
        if file_path:
            self.proxy_file_edit.setText(file_path)
            self.settings.setValue("proxy/file", file_path)
    
    def show_add_proxy_dialog(self):
        """显示添加代理对话框"""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加代理")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout(dialog)
        
        # 代理地址
        proxy_host = QLineEdit()
        proxy_host.setPlaceholderText("例如: 192.168.1.1")
        layout.addRow("代理主机:", proxy_host)
        
        # 代理端口
        proxy_port = QSpinBox()
        proxy_port.setRange(1, 65535)
        proxy_port.setValue(8080)
        layout.addRow("代理端口:", proxy_port)
        
        # 代理协议
        proxy_protocol = QComboBox()
        proxy_protocol.addItems(["http", "https", "socks5"])
        layout.addRow("代理协议:", proxy_protocol)
        
        # 用户名（可选）
        proxy_user = QLineEdit()
        proxy_user.setPlaceholderText("可选")
        layout.addRow("用户名:", proxy_user)
        
        # 密码（可选）
        proxy_pass = QLineEdit()
        proxy_pass.setPlaceholderText("可选")
        proxy_pass.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("密码:", proxy_pass)
        
        # 按钮
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 添加代理
            try:
                from core.proxy_manager import Proxy
                proxy = Proxy(
                    host=proxy_host.text().strip(),
                    port=proxy_port.value(),
                    protocol=proxy_protocol.currentText(),
                    username=proxy_user.text().strip() or None,
                    password=proxy_pass.text().strip() or None
                )
                
                proxy_file = self.proxy_file_edit.text() or "proxies.json"
                manager = ProxyManager(proxy_file)
                
                if manager.add_proxy(proxy):
                    QMessageBox.information(self, "成功", f"代理添加成功:\n{proxy}")
                else:
                    QMessageBox.warning(self, "提示", "代理已存在")
                    
            except Exception as e:
                QMessageBox.critical(self, "错误", f"添加代理失败: {e}")
    
    def test_proxies(self):
        """测试代理"""
        proxy_file = self.proxy_file_edit.text() or "proxies.json"
        
        if not os.path.exists(proxy_file):
            QMessageBox.warning(self, "警告", f"代理文件不存在:\n{proxy_file}")
            return
        
        try:
            from core.proxy_manager import ProxyManager
            
            # 创建测试线程
            self.test_worker = ProxyTestWorker(proxy_file)
            self.test_worker.progress_signal.connect(self.update_log)
            self.test_worker.finished_signal.connect(self.on_proxy_test_finished)
            
            self.log_text.append("[代理测试] 开始测试所有代理...")
            self.test_worker.start()
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"启动测试失败: {e}")
    
    def on_proxy_test_finished(self, success, message):
        """代理测试完成"""
        self.log_text.append(f"[代理测试] {message}")
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.warning(self, "结果", message)
    
    def show_proxy_stats(self):
        """显示代理状态"""
        proxy_file = self.proxy_file_edit.text() or "proxies.json"
        
        try:
            from core.proxy_manager import ProxyManager
            manager = ProxyManager(proxy_file)
            stats = manager.get_stats()
            
            msg = f"""
            <h3>代理状态统计</h3>
            <table>
            <tr><td>总代理数:</td><td><b>{stats['total']}</b></td></tr>
            <tr><td>可用代理:</td><td><b style='color: green;'>{stats['working']}</b></td></tr>
            <tr><td>失败代理:</td><td><b style='color: red;'>{stats['failed']}</b></td></tr>
            <tr><td>可用率:</td><td><b>{stats['working_rate']}</b></td></tr>
            <tr><td>平均延迟:</td><td><b>{stats['avg_latency']}</b></td></tr>
            </table>
            """
            
            QMessageBox.information(self, "代理状态", msg)
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"获取代理状态失败: {e}")
    
    def load_settings(self):
        """加载设置"""
        # 代理设置
        proxy_enabled = self.settings.value("proxy/enabled", False, type=bool)
        proxy_file = self.settings.value("proxy/file", "proxies.json")
        
        self.use_proxy_checkbox.setChecked(proxy_enabled)
        self.proxy_file_edit.setText(proxy_file)


class ProxyTestWorker(QThread):
    """代理测试工作线程"""
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, proxy_file):
        super().__init__()
        self.proxy_file = proxy_file
    
    def run(self):
        """运行测试"""
        try:
            import asyncio
            from core.proxy_manager import ProxyManager
            
            manager = ProxyManager(self.proxy_file)
            
            if not manager.proxies:
                self.finished_signal.emit(False, "没有配置代理")
                return
            
            # 运行异步测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(manager.test_all_proxies())
            loop.close()
            
            # 统计结果
            working = sum(1 for _, is_working, _ in results if is_working)
            total = len(results)
            
            msg = f"测试完成: {working}/{total} 个代理可用"
            self.finished_signal.emit(True, msg)
            
        except Exception as e:
            self.finished_signal.emit(False, f"测试失败: {e}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用样式
    app.setStyle("Fusion")
    
    # 创建窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
