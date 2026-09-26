"""
프리미엄 A4 HTML 수익 보고서 생성 — Wivo 원무일일보고서와 동일한 디자인 시스템 적용.
- 클래스 프리픽스(adr-a4-)와 컬러 토큰, 결재란/번호 섹션 구조를 그대로 재사용하여
  Wivo 원무일일보고서(daily-report-app)와 시각적으로 통일감 있게 제작.
- 인쇄(Ctrl+P) 시 A4 1~2페이지에 맞도록 @page 규칙 적용
- 로고는 base64로 인라인 임베드하여 단일 HTML 파일로 완결 (푸터에 배치)
- 단일 시나리오 리포트(build_html_report)와 A안/B안 비교 리포트(build_comparison_html_report)가
  동일한 CSS(_BASE_CSS)를 공유합니다.
"""
import base64
from datetime import datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

_BASE_CSS = """
@page{size:A4 portrait;margin:8mm 9mm 9mm}
*{box-sizing:border-box}
:root{--ink:#0b2334;--muted:#617282;--line:#dce7e8;--wash:#f6f9fa;--brand:#0f9a8c;--brand-dark:#08766d;--brand-soft:#e7f5f3;--accent:#d8b879}
.adr-a4-body{margin:0;background:#eef2f3;color:var(--ink);font-family:Pretendard,'Noto Sans KR','Malgun Gothic',Arial,sans-serif;font-size:11.2px;line-height:1.42;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.adr-a4-preview-frame{overflow:auto;padding:18px;background:#eef2f3}
.adr-a4-report{width:210mm;max-width:100%;margin:14px auto 28px;background:#fff;color:var(--ink)}
.adr-a4-head{position:relative;padding:9mm 11mm 6mm;border-bottom:1px solid #e8eeee}
.adr-a4-brandline{position:absolute;left:0;right:0;top:0;height:4px;background:linear-gradient(90deg,var(--ink) 0 24%,var(--brand) 24% 82%,var(--accent) 82%)}
.adr-a4-header-grid{display:flex;gap:10mm;align-items:flex-start}
.adr-a4-header-grid>div:first-child{flex:1 1 auto;min-width:0}
.adr-a4-eyebrow{display:flex;align-items:center;gap:7px;color:var(--brand-dark);font-size:8.3px;font-weight:800;letter-spacing:.12em;margin-bottom:3px}
.adr-a4-eyebrow:before{content:"";width:20px;height:2px;background:var(--brand)}
.adr-a4-title{margin:0;font-size:24px;line-height:1.14;letter-spacing:-.03em;color:var(--ink)}
.adr-a4-subtitle{margin:4px 0 0;color:var(--muted);font-size:9.6px}
.adr-a4-approval{flex:0 0 54mm;width:54mm;border:1px solid var(--line);border-radius:5px;overflow:hidden;background:#fff;margin-top:9mm}
.adr-a4-approval-head{text-align:center;background:var(--ink);color:#fff;font-size:7.5px;font-weight:800;padding:3px}
.adr-a4-approval-grid{display:flex}
.adr-a4-approval-grid div{flex:1 1 0;height:15mm;border-right:1px solid var(--line);padding:4px;text-align:center;font-size:8px;color:#657684}
.adr-a4-approval-grid div:last-child{border-right:0}
.adr-a4-meta{display:flex;margin-top:8px;border-top:1px solid var(--ink);border-bottom:1px solid var(--line)}
.adr-a4-meta>div{flex:1 1 0;min-width:0;padding:6px 9px 5px 0;min-height:34px}
.adr-a4-meta>div+div{padding-left:9px;border-left:1px solid var(--line)}
.adr-a4-meta small{display:block;font-size:7px;letter-spacing:.08em;color:#7a8a95;font-weight:700;margin-bottom:2px}
.adr-a4-meta b{font-size:9.8px;color:var(--ink)}
.adr-a4-content{padding:3.5mm 11mm 7mm}
.adr-a4-kpis{display:flex;gap:5px;margin-bottom:3mm}
.adr-a4-kpi{flex:1 1 0;min-width:0;border:1px solid var(--line);border-top:2.5px solid var(--brand);padding:7px 8px;border-radius:6px;background:#fff;min-height:52px}
.adr-a4-kpi.win{border-top-color:var(--accent);background:#fffaf0}
.adr-a4-kpi small{display:block;color:var(--muted);font-size:7.8px;font-weight:700}
.adr-a4-kpi b{display:block;font-size:13.2px;margin:2px 0 1px;color:var(--ink)}
.adr-a4-kpi span{font-size:8px;color:#6f7f8c}
.adr-a4-section{padding:2.5mm 0 1.8mm;border-top:1px solid #edf1f2}
.adr-a4-stitle{display:flex;align-items:center;gap:7px;margin:0 0 5px;padding-bottom:4px;border-bottom:1px solid #dce8e8;font-size:13px;color:var(--ink)}
.adr-a4-num{background:var(--ink);color:#fff;border-radius:4px;padding:2px 5px;font-size:8.4px}
.adr-a4-desc{margin-left:auto;color:#8795a0;font-size:8px;font-weight:500}
.adr-a4-grid2{display:flex;gap:6px}
.adr-a4-grid2-col{flex:1 1 0;min-width:0}
.adr-a4-grid2-col>.adr-a4-table{width:100%}
.adr-a4-table{width:100%;border-collapse:collapse;font-size:8.8px}
.adr-a4-table th,.adr-a4-table td{padding:4px 5px;border-bottom:1px solid #e2eaea;text-align:left;vertical-align:middle}
.adr-a4-table thead th{background:var(--ink);color:#fff;font-size:8.2px}
.adr-a4-table tbody tr:nth-child(even){background:#f8fbfb}
.adr-a4-table tfoot td{border-top:1.4px solid var(--ink);font-weight:800;background:var(--brand-soft)}
.adr-a4-money{font-variant-numeric:tabular-nums;text-align:right}
.adr-a4-ai-box{border:1px solid #d9e8e6;border-left:3px solid var(--brand);background:#f7fbfb;border-radius:6px;padding:8px 9px}
.adr-a4-ai-box strong{display:block;color:var(--brand-dark);font-size:9px;margin-bottom:3px}
.adr-a4-ai-box p{margin:0 0 6px;color:#3e505e;font-size:8.6px;line-height:1.48}
.adr-a4-ai-box p:last-child{margin-bottom:0}
.adr-a4-special{display:grid;grid-template-columns:62px 1fr;gap:8px;padding:7px 8px;border:1px solid #e5dfcc;border-left:3px solid var(--accent);border-radius:6px;background:#fbfaf5}
.adr-a4-special b{font-size:8.8px;color:#70581e}
.adr-a4-special p{margin:0;font-size:8.5px;color:#55636e}
.adr-a4-footer{display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:7.2px;color:#93a0a8;margin-top:2mm;padding-top:4px;border-top:1px solid #edf1f2}
.adr-a4-footer-brand{display:flex;align-items:center}
.adr-a4-footer-brand img{height:14px;display:block}
.adr-a4-win-tag{display:inline-block;margin-left:5px;font-size:7px;font-weight:800;color:#70581e;background:#f3e6c4;border-radius:8px;padding:1px 6px;vertical-align:middle}
@media print{html,body{width:auto!important;min-width:0!important;margin:0!important;padding:0!important;background:#fff!important}.adr-a4-body{font-size:10.5px!important;line-height:1.38!important}.adr-a4-preview-frame{padding:0!important;background:#fff!important}.adr-a4-report{width:100%!important;max-width:none!important;margin:0!important}.adr-a4-head{padding:5mm 0 4mm!important;border-bottom:1px solid #e8eeee!important}.adr-a4-brandline{top:0!important;height:3px!important}.adr-a4-header-grid{gap:8mm!important;align-items:flex-start!important}.adr-a4-approval{flex:0 0 51mm!important;width:51mm!important;margin-top:8mm!important}.adr-a4-approval-grid div{height:13mm!important}.adr-a4-meta{margin-top:6px!important}.adr-a4-meta>div{min-height:28px!important;padding-top:4px!important;padding-bottom:3px!important}.adr-a4-content{padding:3mm 0 0!important}.adr-a4-section{padding:2.2mm 0 1.6mm!important;break-inside:auto!important;page-break-inside:auto!important}.adr-a4-stitle{break-after:avoid-page!important;page-break-after:avoid!important}.adr-a4-kpi,.adr-a4-approval,.adr-a4-ai-box,.adr-a4-special,.adr-a4-table tr{break-inside:avoid-page!important;page-break-inside:avoid!important}.adr-a4-table{break-inside:auto!important;page-break-inside:auto!important}.adr-a4-table thead{display:table-header-group}}
@media(max-width:800px){.adr-a4-preview-frame{padding:0;background:#fff}.adr-a4-report{width:100%;margin:0}.adr-a4-head,.adr-a4-content{padding-left:14px;padding-right:14px}.adr-a4-approval{flex:0 0 34mm;width:34mm;margin-top:0}.adr-a4-approval-head{font-size:6.6px;padding:2px}.adr-a4-approval-grid div{height:11mm;font-size:6.6px;padding:2px}.adr-a4-title{font-size:19px}.adr-a4-kpis{flex-wrap:wrap}.adr-a4-kpis>.adr-a4-kpi{flex:1 1 45%}.adr-a4-grid2{flex-wrap:wrap}.adr-a4-grid2-col{flex:1 1 100%}}
"""


def _logo_base64() -> str:
    if not LOGO_PATH.exists():
        return ""
    data = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def _fmt(amount: Decimal) -> str:
    return f"{int(amount):,}"


def _night_kpi_detail_html(night_items: list) -> str:
    if not night_items:
        return "선택 안 함"
    return " + ".join(it["구분"] for it in night_items)


def _room_rows_html(lines: list) -> str:
    rows = []
    for line in lines:
        warn = ' style="color:#b23b3b"' if line.get("warning") else ""
        rows.append(f"""
        <tr>
            <td{warn}>{line['명칭']}</td>
            <td>{line['구간']}</td>
            <td class="adr-a4-money">{line['환자일수']:,}</td>
            <td class="adr-a4-money">{_fmt(line['단가'])}원</td>
            <td>{line['수가코드'] or '-'}</td>
            <td class="adr-a4-money"><b>{_fmt(line['금액'])}원</b></td>
        </tr>""")
    return "".join(rows)


def _grade_rows_html(comparison: list) -> str:
    rows = []
    for r in comparison:
        is_current = r.get("is_current", False)
        tag = " ✓ 현재 적용" if is_current else ""
        warn = " ⚠ 일부 미매칭" if r.get("unmatched") else ""
        style = ' style="background:#f7fbfb;font-weight:700"' if is_current else ""
        rows.append(f"""
        <tr{style}>
            <td>{r['grade']}등급{tag}{warn}</td>
            <td class="adr-a4-money">{_fmt(r['total_revenue'])}원</td>
        </tr>""")
    return "".join(rows)


def _night_rows_html(night_items: list) -> str:
    if not night_items:
        return '<tr><td colspan="2">선택된 야간 항목 없음</td></tr>'
    rows = []
    for it in night_items:
        rows.append(f"""
        <tr>
            <td>{it['구분']}<br><span style="color:#8795a0;font-size:7.6px">{it['명칭']}</span></td>
            <td class="adr-a4-money">{_fmt(it['금액'])}원</td>
        </tr>""")
    return "".join(rows)


def build_html_report(ctx: dict) -> str:
    """
    ctx keys:
        hospital_name, period_label, generated_at, grade,
        room_lines, room_subtotal, night_items, night_amount, night_patient_days,
        total_revenue, total_patient_days, grade_comparison, ai_narrative,
        total_beds, bed_counts, occupancy
    """
    now_str = ctx.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    report_date = datetime.now().strftime("%Y-%m-%d")
    logo_uri = _logo_base64()

    night_items = ctx.get("night_items", [])
    night_summary = _night_kpi_detail_html(night_items)

    ai_text = ctx.get("ai_narrative") or "AI 해설이 생성되지 않았습니다."
    ai_html = "".join(f"<p>{p.strip()}</p>" for p in ai_text.split("\n") if p.strip())

    notes = ["본 보고서는 업로드된 자체 수가 DB를 기준으로 자동 산출되었습니다. 실제 청구·심사 결과와 차이가 있을 수 있습니다."]
    if any(r.get("unmatched") for r in ctx.get("grade_comparison", [])):
        notes.append("일부 등급 비교에서 병실 크기가 매칭되지 않아 제외된 항목이 있습니다 (⚠ 표시 참고).")
    notes_html = " ".join(notes)

    bed_line = ""
    if ctx.get("total_beds"):
        bed_line = f"{ctx['total_beds']}병상"
        if ctx.get("occupancy") is not None:
            bed_line += f" · 가동률 {ctx['occupancy']}%"
    else:
        bed_line = "입력 안 됨"

    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>일반병동 수익 분석 보고서 - {ctx.get('hospital_name','')}</title>
<style>{_BASE_CSS}</style>
</head>
<body class="adr-a4-body">
<div class="adr-a4-preview-frame">
<main class="adr-a4-report">
  <header class="adr-a4-head">
    <div class="adr-a4-brandline"></div>
    <div class="adr-a4-header-grid">
      <div>
        <div class="adr-a4-eyebrow">General Ward Revenue Report</div>
        <h1 class="adr-a4-title">일반병동 수익 분석 보고서</h1>
        <p class="adr-a4-subtitle">병실료·야간간호료 기반 수익 현황, 간호관리료 등급별 비교 및 AI 경영 브리핑</p>
      </div>
      <section class="adr-a4-approval">
        <div class="adr-a4-approval-head">결재</div>
        <div class="adr-a4-approval-grid"><div>담당</div><div>부장</div><div>원장</div></div>
      </section>
    </div>
    <div class="adr-a4-meta">
      <div><small>ANALYSIS PERIOD</small><b>{ctx.get('period_label','')}</b></div>
      <div><small>HOSPITAL</small><b>{ctx.get('hospital_name','')}</b></div>
      <div><small>ANALYSIS</small><b>Wivo AI</b></div>
    </div>
  </header>
  <div class="adr-a4-content">
    <div class="adr-a4-kpis">
      <div class="adr-a4-kpi"><small>TOTAL REVENUE</small><b>{_fmt(ctx['total_revenue'])}원</b><span>적용 등급 {ctx.get('grade')}등급 기준</span></div>
      <div class="adr-a4-kpi"><small>병실료 소계</small><b>{_fmt(ctx['room_subtotal'])}원</b><span>연인원 {ctx.get('total_patient_days'):,}일</span></div>
      <div class="adr-a4-kpi"><small>야간 가산 합계</small><b>{_fmt(ctx['night_amount'])}원</b><span>{night_summary}</span></div>
      <div class="adr-a4-kpi"><small>병상 현황</small><b>{bed_line}</b><span>작성일 {report_date}</span></div>
    </div>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">01</span>병실료 항목별 수익 상세<span class="adr-a4-desc">청구 항목·재원구간별 환자일수·단가·금액</span></h2>
      <table class="adr-a4-table">
        <thead><tr><th>청구 항목명</th><th>재원구간</th><th class="adr-a4-money">환자일수</th><th class="adr-a4-money">단가</th><th>수가코드</th><th class="adr-a4-money">금액</th></tr></thead>
        <tbody>
          {_room_rows_html(ctx['room_lines'])}
        </tbody>
        <tfoot>
          <tr><td colspan="5">총 수익 (병실료 + 야간 가산)</td><td class="adr-a4-money">{_fmt(ctx['total_revenue'])}원</td></tr>
        </tfoot>
      </table>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">02</span>등급별 비교 · 야간 항목 내역<span class="adr-a4-desc">간호관리료 등급별 예상 수익과 적용 야간 항목</span></h2>
      <div class="adr-a4-grid2">
        <div class="adr-a4-grid2-col">
        <table class="adr-a4-table">
          <thead><tr><th>등급</th><th class="adr-a4-money">예상 총수익</th></tr></thead>
          <tbody>
            {_grade_rows_html(ctx.get('grade_comparison', []))}
          </tbody>
        </table>
        </div>
        <div class="adr-a4-grid2-col">
        <table class="adr-a4-table">
          <thead><tr><th>적용 야간 항목</th><th class="adr-a4-money">금액</th></tr></thead>
          <tbody>
            {_night_rows_html(night_items)}
          </tbody>
        </table>
        </div>
      </div>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">03</span>AI 경영 브리핑<span class="adr-a4-desc">수익 현황 검토 의견</span></h2>
      <div class="adr-a4-ai-box"><strong>WIVO AI CONSULTING NOTE</strong>{ai_html}</div>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">04</span>참고사항</h2>
      <div class="adr-a4-special"><b>NOTE</b><p>{notes_html}</p></div>
    </section>

    <footer class="adr-a4-footer">
      <span class="adr-a4-footer-brand">{f'<img src="{logo_uri}" alt="Wivo Company">' if logo_uri else 'Wivo Company'}</span>
      <span>General Ward Revenue Report · 작성일시 {now_str}</span>
    </footer>
  </div>
</main>
</div>
</body>
</html>"""
    return html


def _compare_night_rows_html(night_items: list) -> str:
    if not night_items:
        return '<div style="color:#8795a0">선택 안 함</div>'
    return "".join(
        f'<div>{it["구분"]} <span style="color:#8795a0">· {_fmt(it["금액"])}원</span></div>'
        for it in night_items
    )


def build_comparison_html_report(ctx: dict) -> str:
    """
    A안/B안 두 운영 시나리오를 비교하는 A4 리포트.
    ctx keys:
        hospital_name, period_label, grade, generated_at,
        label_a, occupancy_a, result_a (calc_total_revenue 반환값), night_items_a,
        label_b, occupancy_b, result_b, night_items_b,
        diff_amount, better_label, ai_narrative
    """
    now_str = ctx.get("generated_at") or datetime.now().strftime("%Y-%m-%d %H:%M")
    logo_uri = _logo_base64()

    ra, rb = ctx["result_a"], ctx["result_b"]
    label_a, label_b = ctx.get("label_a", "A안"), ctx.get("label_b", "B안")
    diff = ctx.get("diff_amount", ra["total_revenue"] - rb["total_revenue"])
    better = ctx.get("better_label", "-")
    win_a = better == label_a
    win_b = better == label_b

    ai_text = ctx.get("ai_narrative") or "AI 비교 진단이 생성되지 않았습니다."
    ai_html = "".join(f"<p>{p.strip()}</p>" for p in ai_text.split("\n") if p.strip())

    def row(label, val_a, val_b, money=True):
        fa = f"{_fmt(val_a)}원" if money else val_a
        fb = f"{_fmt(val_b)}원" if money else val_b
        return f"""
        <tr>
            <td>{label}</td>
            <td class="adr-a4-money">{fa}</td>
            <td class="adr-a4-money">{fb}</td>
        </tr>"""

    detail_rows = (
        row("병상가동률", f"{ctx.get('occupancy_a')}%", f"{ctx.get('occupancy_b')}%", money=False)
        + row("병실료 소계", ra["room"]["subtotal"], rb["room"]["subtotal"])
        + row("야간 가산 합계", ra["night"]["금액"], rb["night"]["금액"])
        + f"""
        <tr style="background:#f7fbfb;font-weight:800">
            <td>총 수익</td>
            <td class="adr-a4-money">{_fmt(ra['total_revenue'])}원{' <span class="adr-a4-win-tag">우위</span>' if win_a else ''}</td>
            <td class="adr-a4-money">{_fmt(rb['total_revenue'])}원{' <span class="adr-a4-win-tag">우위</span>' if win_b else ''}</td>
        </tr>"""
    )

    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>일반병동 수익 비교 진단 보고서 - {ctx.get('hospital_name','')}</title>
<style>{_BASE_CSS}</style>
</head>
<body class="adr-a4-body">
<div class="adr-a4-preview-frame">
<main class="adr-a4-report">
  <header class="adr-a4-head">
    <div class="adr-a4-brandline"></div>
    <div class="adr-a4-header-grid">
      <div>
        <div class="adr-a4-eyebrow">Scenario Comparison Report</div>
        <h1 class="adr-a4-title">일반병동 수익 비교 진단 보고서</h1>
        <p class="adr-a4-subtitle">{label_a} vs {label_b} — 병상가동률·야간 가산 항목 차이에 따른 수익 비교 및 Wivo AI 진단</p>
      </div>
      <section class="adr-a4-approval">
        <div class="adr-a4-approval-head">결재</div>
        <div class="adr-a4-approval-grid"><div>담당</div><div>부장</div><div>원장</div></div>
      </section>
    </div>
    <div class="adr-a4-meta">
      <div><small>ANALYSIS PERIOD</small><b>{ctx.get('period_label','')}</b></div>
      <div><small>HOSPITAL</small><b>{ctx.get('hospital_name','')}</b></div>
      <div><small>ANALYSIS</small><b>Wivo AI</b></div>
    </div>
  </header>
  <div class="adr-a4-content">
    <div class="adr-a4-kpis">
      <div class="adr-a4-kpi{' win' if win_a else ''}"><small>{label_a} 총수익</small><b>{_fmt(ra['total_revenue'])}원</b><span>가동률 {ctx.get('occupancy_a')}%</span></div>
      <div class="adr-a4-kpi{' win' if win_b else ''}"><small>{label_b} 총수익</small><b>{_fmt(rb['total_revenue'])}원</b><span>가동률 {ctx.get('occupancy_b')}%</span></div>
      <div class="adr-a4-kpi"><small>수익 차이</small><b>{_fmt(abs(diff))}원</b><span>{better} 우위</span></div>
      <div class="adr-a4-kpi"><small>적용 등급</small><b>{ctx.get('grade')}등급</b><span>공통 조건</span></div>
    </div>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">01</span>{label_a} vs {label_b} 상세 비교<span class="adr-a4-desc">동일 병상·기간 기준 시나리오별 수익 비교</span></h2>
      <table class="adr-a4-table">
        <thead><tr><th>구분</th><th class="adr-a4-money">{label_a}</th><th class="adr-a4-money">{label_b}</th></tr></thead>
        <tbody>
          {detail_rows}
        </tbody>
      </table>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">02</span>적용 야간 항목<span class="adr-a4-desc">시나리오별 야간간호료·야간전담간호료 적용 내역</span></h2>
      <div class="adr-a4-grid2">
        <div class="adr-a4-grid2-col">
          <div style="font-size:8.6px;font-weight:700;color:var(--ink);margin-bottom:4px">{label_a}</div>
          {_compare_night_rows_html(ctx.get('night_items_a', []))}
        </div>
        <div class="adr-a4-grid2-col">
          <div style="font-size:8.6px;font-weight:700;color:var(--ink);margin-bottom:4px">{label_b}</div>
          {_compare_night_rows_html(ctx.get('night_items_b', []))}
        </div>
      </div>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">03</span>Wivo AI 비교 진단<span class="adr-a4-desc">두 시나리오 중 권장안 및 실행 시 유의사항</span></h2>
      <div class="adr-a4-ai-box"><strong>WIVO AI COMPARISON VERDICT</strong>{ai_html}</div>
    </section>

    <section class="adr-a4-section">
      <h2 class="adr-a4-stitle"><span class="adr-a4-num">04</span>참고사항</h2>
      <div class="adr-a4-special"><b>NOTE</b><p>본 비교는 업로드된 자체 수가 DB와 입력된 병상 조건을 기준으로 자동 산출되었습니다. 실제 인력 운영·청구 결과와 차이가 있을 수 있습니다.</p></div>
    </section>

    <footer class="adr-a4-footer">
      <span class="adr-a4-footer-brand">{f'<img src="{logo_uri}" alt="Wivo Company">' if logo_uri else 'Wivo Company'}</span>
      <span>Scenario Comparison Report · 작성일시 {now_str}</span>
    </footer>
  </div>
</main>
</div>
</body>
</html>"""
    return html
