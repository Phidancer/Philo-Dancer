# PDF 乐谱教材 → 可视化、可审计、可交互、可演奏教学系统

这个仓库提供一个轻量可扩展的转换管线：将含有 **SHEETMUSIC（乐谱）** 和 **分析图表** 的 PDF 教材，转换为教学系统产物：

- `bundle.json`：结构化教学数据（章节、乐句、分析证据、审计日志）
- `index.html`：可直接打开的互动页面（章节浏览、审计查看、示例播放）

## 核心能力

1. **可视化**：输出 HTML 页面展示课程章节、乐谱片段与分析洞见。  
2. **可审计**：每页分类结果写入 `audit_log`，可追踪自动识别过程。  
3. **可交互**：前端支持上传 PDF、浏览章节、点击试听示例。  
4. **可演奏（基础版）**：支持乐句列表及示例声音触发；可扩展为 MIDI/MusicXML 精确回放。  

## 方式一：命令行转换

```bash
python -m music_teaching_system.cli /path/to/SchenkerGUIDE.pdf -o teaching_system_output
```

## 方式二：Web 上传（推荐）

启动上传服务：

```bash
python -m music_teaching_system.webapp
```

然后打开：`http://127.0.0.1:8787`，直接上传 **Pankhurst 的 SchenkerGUIDE PDF**，转换完成后可点开：

- 互动页面：`/outputs/<job_id>/index.html`
- 审计数据：`/outputs/<job_id>/bundle.json`

## 解析说明

- 优先使用 `PyMuPDF`（`fitz`）解析 PDF。
- 若无 `fitz`，自动尝试 `pypdf`。
- 若都不可用，回退到文本模式（`\f` 分页），用于最小环境下的流程验证。

## 开发说明

- 主要代码：
  - `music_teaching_system/pdf_ingest.py`：PDF 解析与页类型分类
  - `music_teaching_system/pipeline.py`：构建课程数据 + 生成产物
  - `music_teaching_system/webapp.py`：Web 上传与在线查看
  - `music_teaching_system/cli.py`：命令行入口
- 测试：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```
