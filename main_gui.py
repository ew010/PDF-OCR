import sys
import os
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QTextEdit, QProgressBar,
    QMessageBox, QLineEdit, QGroupBox, QSpinBox, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QFont

from pdf_to_md import PDFToMarkdownConverter


class ConvertThread(QThread):
    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pdf_path, output_path, dpi=300):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.dpi = dpi
        self._is_running = True

    def run(self):
        try:
            converter = PDFToMarkdownConverter()
            def progress_cb(page, total, msg):
                if not self._is_running:
                    raise InterruptedError("用户取消")
                self.progress.emit(page, total, msg)

            result = converter.convert(self.pdf_path, self.output_path, progress_cb)
            if self._is_running:
                self.finished.emit(str(result))
        except InterruptedError:
            pass
        except Exception as e:
            if self._is_running:
                self.error.emit(str(e))

    def stop(self):
        self._is_running = False
        self.wait(2000)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF 转 Markdown 工具")
        self.setMinimumSize(700, 500)
        self.convert_thread = None
        self.setup_ui()
        self.apply_styles()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("PDF 转 Markdown (OCR)")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 文件选择区域
        file_group = QGroupBox("文件选择")
        file_layout = QVBoxLayout(file_group)

        pdf_layout = QHBoxLayout()
        self.pdf_path_edit = QLineEdit()
        self.pdf_path_edit.setPlaceholderText("拖拽 PDF 文件到此处，或点击选择...")
        self.pdf_path_edit.setReadOnly(True)
        self.pdf_path_edit.setMinimumHeight(35)
        pdf_btn = QPushButton("选择 PDF")
        pdf_btn.setMinimumHeight(35)
        pdf_btn.clicked.connect(self.select_pdf)
        pdf_layout.addWidget(self.pdf_path_edit)
        pdf_layout.addWidget(pdf_btn)
        file_layout.addLayout(pdf_layout)

        out_layout = QHBoxLayout()
        self.output_path_edit = QLineEdit()
        self.output_path_edit.setPlaceholderText("输出 Markdown 路径（可选，默认同名）")
        self.output_path_edit.setMinimumHeight(35)
        out_btn = QPushButton("选择输出路径")
        out_btn.setMinimumHeight(35)
        out_btn.clicked.connect(self.select_output)
        out_layout.addWidget(self.output_path_edit)
        out_layout.addWidget(out_btn)
        file_layout.addLayout(out_layout)

        layout.addWidget(file_group)

        # 设置区域
        settings_group = QGroupBox("设置")
        settings_layout = QHBoxLayout(settings_group)

        dpi_layout = QHBoxLayout()
        dpi_layout.addWidget(QLabel("DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(150, 600)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSingleStep(50)
        dpi_layout.addWidget(self.dpi_spin)
        settings_layout.addLayout(dpi_layout)

        self.open_after_check = QCheckBox("完成后打开文件")
        self.open_after_check.setChecked(True)
        settings_layout.addWidget(self.open_after_check)

        settings_layout.addStretch()
        layout.addWidget(settings_group)

        # 进度区域
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(25)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.convert_btn = QPushButton("开始转换")
        self.convert_btn.setMinimumHeight(45)
        self.convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #218838; }
            QPushButton:pressed { background-color: #1e7e34; }
            QPushButton:disabled { background-color: #6c757d; }
        """)
        self.convert_btn.clicked.connect(self.start_convert)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumHeight(45)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self.cancel_convert)

        btn_layout.addWidget(self.convert_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)

        # 日志区域
        log_group = QGroupBox("日志")
        log_layout = QVBoxLayout(log_group)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)

        # 启用拖拽
        self.setAcceptDrops(True)
        self.pdf_path_edit.setAcceptDrops(True)

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLineEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 5px 10px;
                background: white;
            }
            QPushButton {
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 5px 15px;
                background: #e9ecef;
            }
            QPushButton:hover {
                background: #dee2e6;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 6px;
                background: #f8f9fa;
                font-family: monospace;
            }
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 6px;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith('.pdf'):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if file_path.lower().endswith('.pdf'):
                self.pdf_path_edit.setText(file_path)
                # 自动设置输出路径
                if not self.output_path_edit.text():
                    default_out = str(Path(file_path).with_suffix('.md'))
                    self.output_path_edit.setText(default_out)

    def select_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if file_path:
            self.pdf_path_edit.setText(file_path)
            if not self.output_path_edit.text():
                default_out = str(Path(file_path).with_suffix('.md'))
                self.output_path_edit.setText(default_out)

    def select_output(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存 Markdown 文件", "", "Markdown 文件 (*.md)"
        )
        if file_path:
            if not file_path.endswith('.md'):
                file_path += '.md'
            self.output_path_edit.setText(file_path)

    def log(self, message):
        self.log_text.append(message)

    def start_convert(self):
        pdf_path = self.pdf_path_edit.text().strip()
        if not pdf_path:
            QMessageBox.warning(self, "提示", "请先选择 PDF 文件")
            return
        if not os.path.exists(pdf_path):
            QMessageBox.warning(self, "错误", "PDF 文件不存在")
            return

        output_path = self.output_path_edit.text().strip()
        if not output_path:
            output_path = str(Path(pdf_path).with_suffix('.md'))
            self.output_path_edit.setText(output_path)

        self.convert_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.log(f"开始转换: {pdf_path}")

        self.convert_thread = ConvertThread(pdf_path, output_path, self.dpi_spin.value())
        self.convert_thread.progress.connect(self.on_progress)
        self.convert_thread.finished.connect(self.on_finished)
        self.convert_thread.error.connect(self.on_error)
        self.convert_thread.start()

    def on_progress(self, page, total, msg):
        percent = int(page / total * 100) if total > 0 else 0
        self.progress_bar.setValue(percent)
        self.status_label.setText(msg)
        self.log(msg)

    def on_finished(self, result_path):
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setValue(100)
        self.status_label.setText("转换完成")
        self.log(f"转换完成: {result_path}")

        if self.open_after_check.isChecked():
            self.open_file(result_path)

        QMessageBox.information(self, "完成", f"转换成功！\n输出文件: {result_path}")

    def on_error(self, error_msg):
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("转换失败")
        self.log(f"错误: {error_msg}")
        QMessageBox.critical(self, "错误", f"转换失败:\n{error_msg}")

    def cancel_convert(self):
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.stop()
            self.log("用户取消转换")
        self.convert_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("已取消")

    def open_file(self, file_path):
        if sys.platform == 'darwin':
            os.system(f'open "{file_path}"')
        elif sys.platform == 'win32':
            os.startfile(file_path)
        else:
            os.system(f'xdg-open "{file_path}"')

    def closeEvent(self, event):
        if self.convert_thread and self.convert_thread.isRunning():
            self.convert_thread.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 设置应用级字体
    font = QFont("Microsoft YaHei", 10)
    if sys.platform == 'darwin':
        font = QFont("PingFang SC", 10)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
