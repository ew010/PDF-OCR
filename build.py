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
    ]

    # 平台特定配置
    if platform == 'macos':
        cmd.extend([
            '--onedir',
            '--osx-bundle-identifier', 'com.ew010.pdf2markdown',
            '--collect-all', 'PyQt6',
            '--collect-all', 'rapidocr',
            '--collect-all', 'onnxruntime',
        ])
        icon_path = 'assets/icon.icns'
        if os.path.exists(icon_path):
            cmd.extend(['--icon', icon_path])
    elif platform == 'windows':
        cmd.extend([
            '--onefile',
            '--collect-all', 'rapidocr',
            '--collect-all', 'onnxruntime',
        ])
        icon_path = 'assets/icon.ico'
        if os.path.exists(icon_path):
            cmd.extend(['--icon', icon_path])

    cmd.append('main_gui.py')

    print("执行命令:", ' '.join(cmd))
    result = subprocess.run(cmd, check=False)

    if result.returncode != 0:
        print("打包失败!")
        sys.exit(1)

    # macOS: 修复 Qt 插件路径
    if platform == 'macos':
        app_path = Path('dist/PDF2Markdown.app')
        plugins_src = app_path / 'Contents/MacOS/PyQt6/Qt6/plugins'
        plugins_dst = app_path / 'Contents/PlugIns'
        if plugins_src.exists():
            plugins_dst.mkdir(parents=True, exist_ok=True)
            for item in plugins_src.iterdir():
                dst = plugins_dst / item.name
                if dst.exists():
                    shutil.rmtree(dst) if dst.is_dir() else dst.unlink()
                if item.is_dir():
                    shutil.copytree(item, dst)
                else:
                    shutil.copy2(item, dst)
            print("已修复 Qt 插件路径")

    print("打包成功!")
    dist_path = Path('dist')
    for f in dist_path.iterdir():
        print(f"  生成文件: {f}")


if __name__ == '__main__':
    build()
