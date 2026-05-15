import os
import sys
import fitz  # PyMuPDF
from pathlib import Path
from PIL import Image
import io

from rapidocr import RapidOCR


class PDFToMarkdownConverter:
    def __init__(self, ocr_engine=None):
        self.ocr_engine = ocr_engine or RapidOCR()

    def pdf_to_images(self, pdf_path, dpi=300):
        doc = fitz.open(pdf_path)
        images = []
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # 使用矩阵提高分辨率
            mat = fitz.Matrix(dpi/72, dpi/72)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))
            images.append((page_num + 1, img))
        doc.close()
        return images

    def image_to_text(self, image):
        result = self.ocr_engine(image)
        if not result or not result[0]:
            return ""
        # result[0] 是识别结果列表
        items = result[0]
        # 按行排序并拼接文本
        lines = []
        current_line = []
        last_y = None
        threshold = 10  # 同一行的y坐标阈值

        for item in items:
            box, text, score = item
            # box: [[x1,y1],[x2,y2],[x3,y3],[x4,y4]]
            y_center = (box[0][1] + box[2][1]) / 2
            if last_y is None or abs(y_center - last_y) < threshold:
                current_line.append((box[0][0], text))
            else:
                current_line.sort(key=lambda x: x[0])
                lines.append(" ".join([t for _, t in current_line]))
                current_line = [(box[0][0], text)]
            last_y = y_center

        if current_line:
            current_line.sort(key=lambda x: x[0])
            lines.append(" ".join([t for _, t in current_line]))

        return "\n".join(lines)

    def convert(self, pdf_path, output_md_path=None, progress_callback=None):
        pdf_path = Path(pdf_path)
        if output_md_path is None:
            output_md_path = pdf_path.with_suffix('.md')
        else:
            output_md_path = Path(output_md_path)

        images = self.pdf_to_images(pdf_path)
        total = len(images)
        md_content = f"# {pdf_path.stem}\n\n"

        for idx, (page_num, img) in enumerate(images):
            if progress_callback:
                progress_callback(page_num, total, f"正在识别第 {page_num}/{total} 页...")

            text = self.image_to_text(img)
            md_content += f"## 第 {page_num} 页\n\n"
            md_content += text + "\n\n"
            md_content += "---\n\n"

        output_md_path.write_text(md_content, encoding='utf-8')
        return output_md_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pdf_to_md.py <pdf文件路径> [输出md路径]")
        sys.exit(1)

    pdf_file = sys.argv[1]
    md_file = sys.argv[2] if len(sys.argv) > 2 else None

    converter = PDFToMarkdownConverter()
    result = converter.convert(pdf_file, md_file, progress_callback=lambda p, t, m: print(m))
    print(f"转换完成: {result}")
