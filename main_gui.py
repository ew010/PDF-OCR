import sys
import os
import threading
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Entry, Text, Scrollbar,
    filedialog, messagebox, IntVar, Checkbutton, StringVar
)
from tkinter import ttk

from pdf_to_md import PDFToMarkdownConverter


class ConvertThread(threading.Thread):
    def __init__(self, pdf_path, output_path, dpi=300, progress_cb=None, finished_cb=None, error_cb=None):
        super().__init__(daemon=True)
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.dpi = dpi
        self.progress_cb = progress_cb
        self.finished_cb = finished_cb
        self.error_cb = error_cb
        self._is_running = True

    def run(self):
        try:
            converter = PDFToMarkdownConverter()
            def progress_cb(page, total, msg):
                if not self._is_running:
                    raise InterruptedError("用户取消")
                if self.progress_cb:
                    self.progress_cb(page, total, msg)

            result = converter.convert(self.pdf_path, self.output_path, progress_cb)
            if self._is_running and self.finished_cb:
                self.finished_cb(str(result))
        except InterruptedError:
            pass
        except Exception as e:
            if self._is_running and self.error_cb:
                self.error_cb(str(e))

    def stop(self):
        self._is_running = False


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 转 Markdown 工具")
        self.root.geometry("700x550")
        self.root.minsize(600, 450)
        self.convert_thread = None
        self.setup_ui()

    def setup_ui(self):
        # 主容器
        main_frame = Frame(self.root, padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)

        # 标题
        title = Label(main_frame, text="PDF 转 Markdown (OCR)", font=("Microsoft YaHei", 16, "bold"))
        title.pack(pady=(0, 15))

        # 文件选择区域
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=10)
        file_frame.pack(fill="x", pady=5)

        # PDF 路径
        pdf_row = Frame(file_frame)
        pdf_row.pack(fill="x", pady=3)
        self.pdf_path_var = StringVar()
        pdf_entry = Entry(pdf_row, textvariable=self.pdf_path_var, state="readonly", fg="gray")
        pdf_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        pdf_entry.configure(readonlybackground="white")
        pdf_btn = Button(pdf_row, text="选择 PDF", command=self.select_pdf, width=12)
        pdf_btn.pack(side="right")

        # 输出路径
        out_row = Frame(file_frame)
        out_row.pack(fill="x", pady=3)
        self.output_path_var = StringVar()
        out_entry = Entry(out_row, textvariable=self.output_path_var, state="readonly", fg="gray")
        out_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        out_entry.configure(readonlybackground="white")
        out_btn = Button(out_row, text="选择输出路径", command=self.select_output, width=12)
        out_btn.pack(side="right")

        # 设置区域
        settings_frame = ttk.LabelFrame(main_frame, text="设置", padding=10)
        settings_frame.pack(fill="x", pady=5)

        settings_row = Frame(settings_frame)
        settings_row.pack(fill="x")

        # DPI
        dpi_frame = Frame(settings_row)
        dpi_frame.pack(side="left")
        Label(dpi_frame, text="DPI:").pack(side="left")
        self.dpi_var = IntVar(value=300)
        dpi_spin = ttk.Spinbox(dpi_frame, from_=150, to=600, increment=50, textvariable=self.dpi_var, width=8)
        dpi_spin.pack(side="left", padx=5)

        # 完成后打开
        self.open_after_var = IntVar(value=1)
        Checkbutton(settings_row, text="完成后打开文件", variable=self.open_after_var).pack(side="left", padx=20)

        # 进度区域
        self.progress_var = IntVar(value=0)
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", pady=(10, 5))

        self.status_var = StringVar(value="就绪")
        status_label = Label(main_frame, textvariable=self.status_var, fg="gray")
        status_label.pack()

        # 按钮区域
        btn_frame = Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)

        self.convert_btn = Button(btn_frame, text="开始转换", command=self.start_convert, bg="#28a745", fg="white", font=("Microsoft YaHei", 11, "bold"), height=2)
        self.convert_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.cancel_btn = Button(btn_frame, text="取消", command=self.cancel_convert, state="disabled", height=2)
        self.cancel_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="日志", padding=5)
        log_frame.pack(fill="both", expand=True, pady=5)

        log_scroll = Scrollbar(log_frame)
        log_scroll.pack(side="right", fill="y")

        self.log_text = Text(log_frame, height=6, yscrollcommand=log_scroll.set, state="disabled", font=("Consolas", 9))
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)

        # 拖拽支持
        self.root.drop_target_register("*")
        self.root.dnd_bind("<<Drop>>", self.on_drop)
        pdf_entry.drop_target_register("*")
        pdf_entry.dnd_bind("<<Drop>>", self.on_drop)

    def on_drop(self, event):
        file_path = event.data.strip("{}")
        if file_path.lower().endswith('.pdf'):
            self.pdf_path_var.set(file_path)
            if not self.output_path_var.get():
                default_out = str(Path(file_path).with_suffix('.md'))
                self.output_path_var.set(default_out)

    def select_pdf(self):
        file_path = filedialog.askopenfilename(title="选择 PDF 文件", filetypes=[("PDF 文件", "*.pdf")])
        if file_path:
            self.pdf_path_var.set(file_path)
            if not self.output_path_var.get():
                default_out = str(Path(file_path).with_suffix('.md'))
                self.output_path_var.set(default_out)

    def select_output(self):
        file_path = filedialog.asksaveasfilename(title="保存 Markdown 文件", defaultextension=".md", filetypes=[("Markdown 文件", "*.md")])
        if file_path:
            self.output_path_var.set(file_path)

    def log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def start_convert(self):
        pdf_path = self.pdf_path_var.get().strip()
        if not pdf_path:
            messagebox.showwarning("提示", "请先选择 PDF 文件")
            return
        if not os.path.exists(pdf_path):
            messagebox.showwarning("错误", "PDF 文件不存在")
            return

        output_path = self.output_path_var.get().strip()
        if not output_path:
            output_path = str(Path(pdf_path).with_suffix('.md'))
            self.output_path_var.set(output_path)

        self.convert_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self.progress_var.set(0)
        self.log_text.configure(state="normal")
        self.log_text.delete(1.0, "end")
        self.log_text.configure(state="disabled")
        self.log(f"开始转换: {pdf_path}")

        self.convert_thread = ConvertThread(
            pdf_path, output_path, self.dpi_var.get(),
            progress_cb=self.on_progress,
            finished_cb=self.on_finished,
            error_cb=self.on_error
        )
        self.convert_thread.start()

    def on_progress(self, page, total, msg):
        percent = int(page / total * 100) if total > 0 else 0
        self.progress_var.set(percent)
        self.status_var.set(msg)
        self.log(msg)

    def on_finished(self, result_path):
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.progress_var.set(100)
        self.status_var.set("转换完成")
        self.log(f"转换完成: {result_path}")

        if self.open_after_var.get():
            self.open_file(result_path)

        messagebox.showinfo("完成", f"转换成功！\n输出文件: {result_path}")

    def on_error(self, error_msg):
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_var.set("转换失败")
        self.log(f"错误: {error_msg}")
        messagebox.showerror("错误", f"转换失败:\n{error_msg}")

    def cancel_convert(self):
        if self.convert_thread and self.convert_thread.is_alive():
            self.convert_thread.stop()
            self.log("用户取消转换")
        self.convert_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self.status_var.set("已取消")

    def open_file(self, file_path):
        if sys.platform == 'darwin':
            os.system(f'open "{file_path}"')
        elif sys.platform == 'win32':
            os.startfile(file_path)
        else:
            os.system(f'xdg-open "{file_path}"')


def main():
    root = Tk()
    app = MainWindow(root)
    root.mainloop()


if __name__ == "__main__":
    main()
