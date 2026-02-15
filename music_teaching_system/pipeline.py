from __future__ import annotations

import json
from pathlib import Path

from .models import AnalysisInsight, Evidence, LessonSection, ScoreMeasure, TeachingSystemBundle
from .pdf_ingest import classify_page, parse_pdf


def _build_sections(pdf_text_pages: list[tuple[int, str]]) -> tuple[list[LessonSection], list[str]]:
    sections: list[LessonSection] = []
    audit: list[str] = []

    non_empty_pages = 0
    for page_number, text in pdf_text_pages:
        if text.strip():
            non_empty_pages += 1

        page_type = classify_page(text)
        audit.append(f"page={page_number} classified_as={page_type} chars={len(text.strip())}")

        if page_type in {"sheetmusic", "hybrid"}:
            measures = []
            for idx, line in enumerate(text.splitlines(), start=1):
                if "|" in line or "measure" in line.lower() or "小节" in line:
                    measures.append(ScoreMeasure(index=idx, notation=line.strip()[:120]))

            if not measures:
                measures = [ScoreMeasure(index=1, notation="(auto-detected phrase)")]

            sections.append(
                LessonSection(
                    id=f"score-{page_number}",
                    title=f"乐谱页 {page_number}",
                    objective="识别旋律结构并支持交互演奏",
                    measures=measures,
                )
            )

        if page_type in {"analysis", "hybrid"}:
            insight = AnalysisInsight(
                insight_type="theory",
                title=f"分析图表页 {page_number}",
                description="提取结构/和声/动机信息并关联到对应乐谱段落",
                evidence=[
                    Evidence(
                        source="pdf",
                        page=page_number,
                        excerpt=text.strip().replace("\n", " ")[:200],
                        confidence=0.68,
                    )
                ],
            )

            sections.append(
                LessonSection(
                    id=f"analysis-{page_number}",
                    title=f"分析页 {page_number}",
                    objective="建立可审计的分析链路",
                    insights=[insight],
                )
            )

    if not sections:
        objective = "未识别到乐谱/图表关键词，已生成基础课程壳。"
        if non_empty_pages == 0:
            objective = "未提取到可读文本（常见于扫描版 PDF）。请先进行 OCR 再上传，或安装可用 PDF 解析依赖。"
            audit.append("warning: no readable text extracted from source")

        sections.append(
            LessonSection(
                id="fallback-1",
                title="自动导入内容",
                objective=objective,
                measures=[ScoreMeasure(index=1, notation="请补充人工校对后的乐谱片段")],
            )
        )
        audit.append("fallback section generated")

    return sections, audit


def _build_html(bundle: TeachingSystemBundle) -> str:
    payload = json.dumps(bundle.to_dict(), ensure_ascii=False)
    return f"""<!doctype html>
<html lang='zh-CN'>
<head>
  <meta charset='UTF-8' />
  <meta name='viewport' content='width=device-width, initial-scale=1.0' />
  <title>{bundle.title} - 互动教学系统</title>
  <style>
    body {{ font-family: sans-serif; margin: 0; background:#0f172a; color:#e2e8f0; }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 24px; }}
    .card {{ background:#1e293b; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
    button {{ background:#22c55e; border:0; padding:8px 12px; border-radius:8px; cursor:pointer; }}
    pre {{ white-space: pre-wrap; }}
  </style>
</head>
<body>
<div class='wrap'>
  <h1>🎼 {bundle.title}：可视化/可审计/可交互教学系统</h1>
  <p>支持审计日志追踪、章节浏览、乐句播放（示例音频）与分析证据查看。</p>
  <div id='app'></div>
</div>
<script>
const bundle = {payload};
const app = document.getElementById('app');

function beep() {{
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const osc = ctx.createOscillator();
  osc.type = 'sine';
  osc.frequency.value = 440;
  osc.connect(ctx.destination);
  osc.start();
  setTimeout(() => osc.stop(), 180);
}}

bundle.sections.forEach(section => {{
  const div = document.createElement('div');
  div.className = 'card';
  const measures = (section.measures || []).map(m => `<li>#${{m.index}} ${{m.notation}}</li>`).join('');
  const insights = (section.insights || []).map(i => `<li><b>${{i.title}}</b>：${{i.description}}</li>`).join('');
  div.innerHTML = `
    <h3>${{section.title}}</h3>
    <p>目标：${{section.objective}}</p>
    ${{measures ? `<h4>可演奏片段</h4><ul>${{measures}}</ul>` : ''}}
    ${{insights ? `<h4>分析洞见</h4><ul>${{insights}}</ul>` : ''}}
    <button>▶ 试听示例</button>
  `;
  div.querySelector('button')?.addEventListener('click', beep);
  app.appendChild(div);
}});

const audit = document.createElement('div');
audit.className = 'card';
audit.innerHTML = `<h3>审计日志</h3><pre>${{bundle.audit_log.join('\n')}}</pre>`;
app.appendChild(audit);
</script>
</body>
</html>
"""


def convert_pdf_to_teaching_system(pdf_path: str | Path, output_dir: str | Path) -> TeachingSystemBundle:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)

    parsed = parse_pdf(pdf_path)
    pages = [(p.page, p.text) for p in parsed.pages]
    sections, audit = _build_sections(pages)

    bundle = TeachingSystemBundle(
        title=parsed.title,
        source_pdf=str(pdf_path),
        sections=sections,
        audit_log=audit,
        metadata={"page_count": len(parsed.pages), "version": "0.1.0"},
    )

    json_path = output / "bundle.json"
    json_path.write_text(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    html_path = output / "index.html"
    html_path.write_text(_build_html(bundle), encoding="utf-8")

    return bundle
