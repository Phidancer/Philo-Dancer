from __future__ import annotations

import html
import json
import shutil
from datetime import datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .pipeline import convert_pdf_to_teaching_system

APP_TITLE = "Schenker 教材转换器"
UPLOAD_DIR = Path("web_uploads")
OUTPUT_ROOT = Path("web_outputs")


def _html_page(body: str) -> bytes:
    page = f"""<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>{APP_TITLE}</title>
  <style>
    body {{ font-family: Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 24px; }}
    .card {{ background: #1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
    .row {{ display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }}
    input, button {{ font-size: 16px; }}
    input[type='file'] {{ background:#0b1220; border:1px solid #334155; color:#e2e8f0; padding:8px; border-radius:8px; }}
    button {{ background:#22c55e; border:0; padding:8px 14px; border-radius:8px; cursor:pointer; color:#052e16; font-weight:600; }}
    a {{ color: #93c5fd; }}
    code {{ background:#334155; padding:2px 6px; border-radius:6px; }}
    .muted {{ color:#94a3b8; }}
  </style>
</head>
<body>
<div class='wrap'>{body}</div>
</body>
</html>"""
    return page.encode("utf-8")


class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.startswith("/outputs/"):
            self._serve_output_file()
            return

        body = """
<h1>🎼 Schenker 教材转换器</h1>
<div class='card'>
  <p>上传 Pankhurst 的 <b>SchenkerGUIDE PDF</b>（或其他包含乐谱与分析图表的教材），自动生成：</p>
  <ul>
    <li><code>bundle.json</code>：可审计教学结构化数据</li>
    <li><code>index.html</code>：可视化、可交互、可演奏（示例）页面</li>
  </ul>
  <form action='/upload' method='post' enctype='multipart/form-data'>
    <div class='row'>
      <input id='pdf-input' type='file' name='pdf' accept='.pdf,.txt' required />
      <button id='submit-btn' type='submit'>开始转换</button>
    </div>
  </form>
  <p class='muted'>如果你之前遇到“无法点击”，请直接点击上方文件选择框并选择 PDF 后点击“开始转换”。</p>
</div>
<p class='muted'>提示：若环境已安装 PyMuPDF 或 pypdf，将优先用 PDF 解析；否则回退文本解析。</p>
"""
        self._send_html(body)

    def do_POST(self) -> None:
        if self.path != "/upload":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        content_type = self.headers.get("Content-Type", "")
        if "multipart/form-data" not in content_type:
            self.send_error(HTTPStatus.BAD_REQUEST, "Expected multipart/form-data")
            return

        import cgi

        fs = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
        )
        file_item = fs["pdf"] if "pdf" in fs else None
        if file_item is None or not getattr(file_item, "filename", ""):
            self.send_error(HTTPStatus.BAD_REQUEST, "No file uploaded")
            return

        safe_name = Path(file_item.filename).name
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        job_id = f"{timestamp}-{safe_name.replace(' ', '_')}"

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

        upload_path = UPLOAD_DIR / job_id
        with upload_path.open("wb") as f:
            shutil.copyfileobj(file_item.file, f)

        output_dir = OUTPUT_ROOT / job_id
        bundle = convert_pdf_to_teaching_system(upload_path, output_dir)

        summary = {
            "title": bundle.title,
            "source_pdf": bundle.source_pdf,
            "section_count": len(bundle.sections),
            "audit_count": len(bundle.audit_log),
            "metadata": bundle.metadata,
        }

        body = f"""
<h1>✅ 转换完成</h1>
<div class='card'>
  <p><b>教材：</b>{html.escape(bundle.title)}</p>
  <p><b>章节数：</b>{len(bundle.sections)}，<b>审计日志：</b>{len(bundle.audit_log)}</p>
  <p><a href='/outputs/{job_id}/index.html' target='_blank'>打开互动教学页面</a></p>
  <p><a href='/outputs/{job_id}/bundle.json' target='_blank'>查看 bundle.json</a></p>
</div>
<div class='card'>
  <h3>转换摘要</h3>
  <pre>{html.escape(json.dumps(summary, ensure_ascii=False, indent=2))}</pre>
</div>
<p><a href='/'>← 继续上传</a></p>
"""
        self._send_html(body)

    def _serve_output_file(self) -> None:
        rel = self.path[len("/outputs/") :]
        target = (OUTPUT_ROOT / rel).resolve()
        if not str(target).startswith(str(OUTPUT_ROOT.resolve())):
            self.send_error(HTTPStatus.FORBIDDEN, "Invalid path")
            return
        if not target.exists() or not target.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        if target.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        elif target.suffix == ".json":
            ctype = "application/json; charset=utf-8"
        else:
            ctype = "application/octet-stream"

        data = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_html(self, body: str) -> None:
        data = _html_page(body)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def run_server(host: str = "0.0.0.0", port: int = 8787) -> None:
    server = ThreadingHTTPServer((host, port), UploadHandler)
    print(f"🚀 Web 上传服务已启动: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
