# PDF 转 Markdown 工具

基于 RapidOCR 的 PDF 转 Markdown 图形工具，支持 Windows 和 macOS。

## 功能特性

- 拖拽或选择 PDF 文件进行转换
- 使用 RapidOCR 进行高精度文字识别
- 支持中英文混合识别
- 可调整 DPI 参数以优化识别效果
- 转换完成后自动打开文件
- 跨平台支持（Windows / macOS）

## 快速开始

### 环境要求

- Python 3.8+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行程序

```bash
python main_gui.py
```

### 命令行使用

```bash
python pdf_to_md.py input.pdf [output.md]
```

## 本地打包

```bash
python build.py
```

打包后的可执行文件位于 `dist/` 目录。

## GitHub Actions 自动发布

1. 推送代码到 GitHub
2. 创建并推送标签：
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. GitHub Actions 会自动构建 Windows 和 macOS 版本，并发布到 Release 页面

## 项目结构

```
.
├── .github/workflows/build.yml   # GitHub Actions 配置
├── assets/                        # 图标资源
├── pdf_to_md.py                  # 核心转换逻辑
├── main_gui.py                   # GUI 界面
├── build.py                      # 本地打包脚本
├── requirements.txt              # 依赖列表
└── README.md                     # 说明文档
```

## 依赖说明

- **rapidocr-onnxruntime**: 轻量级 OCR 引擎
- **PyMuPDF**: PDF 文件处理
- **Pillow**: 图像处理
- **PyQt6**: GUI 界面
- **PyInstaller**: 打包工具
