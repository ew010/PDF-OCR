#!/usr/bin/env python3
"""
本地打包脚本，支持 Windows 和 macOS
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def get_platform():
    if sys.platform == 'darwin':
        return 'macos'
    elif sys.platform == 'win32':
        return 'windows'
    else:
        return 'linux'


def build():
    platform = get_platform()
    print(f"开始为 {platform} 平台打包...")

    # 清理旧构建
    for d in ['build', 'dist']:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"清理 {d}/")

    # 基础命令
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--name', 'PDF2Markdown',
        '--windowed',
        '--hidden-import=rapidocr',
        '--hidden-import=onnxruntime',
        '--hidden-import=fitz',
        '--hidden-import=PIL',
        '--collect-submodules', 'rapidocr',
        '--collect-submodules', 'rapidocr.utils',
        '--collect-binaries', 'onnxruntime',
        '--copy-metadata', 'rapidocr',
        '--copy-metadata', 'onnxruntime',
        '--exclude-module', 'matplotlib',
        '--exclude-module', 'scipy',
        '--exclude-module', 'pandas',
        '--exclude-module', 'sklearn',
    ]

    # 平台特定配置
    if platform == 'macos':
        cmd.extend([
            '--onedir',
            '--osx-bundle-identifier', 'com.ew010.pdf2markdown',
        ])
        icon_path = 'assets/icon.icns'
        if os.path.exists(icon_path):
            cmd.extend(['--icon', icon_path])
    elif platform == 'windows':
        cmd.append('--onefile')
        icon_path = 'assets/icon.ico'
        if os.path.exists(icon_path):
            cmd.extend(['--icon', icon_path])

    cmd.append('main_gui.py')

    print("执行命令:", ' '.join(cmd))
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print("打包失败!")
        sys.exit(1)

    print("打包成功!")
    dist_path = Path('dist')
    for f in dist_path.iterdir():
        print(f"  生成文件: {f}")

    # 显示体积
    if platform == 'macos':
        app_path = dist_path / 'PDF2Markdown.app'
        if app_path.exists():
            total_size = sum(
                f.stat().st_size for f in app_path.rglob('*') if f.is_file()
            )
            print(f"  App 体积: {total_size / 1024 / 1024:.1f} MB")


if __name__ == '__main__':
    build()
