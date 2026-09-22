"""
프리미엄 A4 HTML 수익 보고서 생성 (고급풍 리디자인).
- Wivo Company 로고의 '+' 심볼을 리포트 전반의 시그니처 마크로 재사용
- 이중 헤어라인 프레임, 미세 페이퍼 그레인, 골드 포일 포인트로 인쇄물(프로스펙터스) 톤 연출
- 인쇄(Ctrl+P) 시 A4 1~2페이지에 맞도록 @page 규칙 적용
- 로고는 base64로 인라인 임베드하여 단일 HTML 파일로 완결
"""
import base64
from datetime import datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "assets" / "logo.png"

# Wivo 로고의 '+' 심볼을 그대로 본뜬 시그니처 마크 (teal)
PLUS_GLYPH_SVG = (
    '<svg class="plus-glyph" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M10.5 2.5a1.5 1.5 0 0 1 3 0V9.5H20.5a1.5 1.5 0 0 1 0 3H13.5V19.5a1.5 1.5 0 0 1-3 0V12.5H3.5a1.5 1.5 0 0 1 0-3H10.5V2.5Z"/>'
    '</svg>'
)


def _logo_base64() -> str:
    if not LOGO_PATH.exists():
        return ""
    data = base64.b64encode(LOGO_PATH.read_bytes()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def _fmt(amount: Decimal) -> str:
    return f"{int(amount):,}"


def _room_rows_html(lines: list) -> str:
    rows = []
    for line in lines:
        warn = " class='warn'" if line.get("warning") else ""
        rows.append(f"""
        <tr{warn}>
            <td class="name-cell">{line['명칭']}</td>
            <td>{line['구간']}</td>
            <td class="num">{line['환자일수']:,}</td>
            <td class="num">{_fmt(line['단가'])}</td>
            <td class="code">{line['수가코드'] or '-'}</td>
            <td class="num strong">{_fmt(line['금액'])}</td>
        </tr>""")
    return "".join(rows)


def _grade_bars_html(comparison: list) -> str:
    if not comparison:
        return "<p class='muted'>등급 비교 데이터가 없습니다.</p>"
    max_val = max((r["total_revenue"] for r in comparison), default=Decimal("1"))
    max_val = max_val if max_val > 0 else Decimal("1")
    bars = []
    for r in comparison:
        pct = float(r["total_revenue"] / max_val * 100)
        is_current = r.get("is_current", False)
        cls = "bar-fill current" if is_current else "bar-fill"
        label = f"{r['grade']}등급" + (" · 현재 적용" if is_current else "") + (" ⚠️" if r.get("unmatched") else "")
        bars.append(f"""
        <div class="bar-row{' is-current' if is_current else ''}">
            <div class="bar-label">{label}</div>
            <div class="bar-track"><div class="{cls}" style="width:{pct:.1f}%"></div></div>
            <div class="bar-value">{_fmt(r['total_revenue'])}<span class="won">원</span></div>
        </div>""")
    return "".join(bars)


def build_html_report(ctx: dict) -> str:
    """
    ctx keys:
        hospital_name, period_label, generated_at, grade, night_type,
        room_lines, room_subtotal, night_amount, night_unit_price, night_patient_days,
        total_revenue, total_patient_days, grade_comparison(list of dict w/ grade, total_revenue, is_current),
        ai_narrative (str or None)
    """
    logo_uri = _logo_base64()
    now_str = ctx.get("generated_at") or datetime.now().strftime("%Y년 %m월 %d일 %H:%M")

    ai_block = ""
    if ctx.get("ai_narrative"):
        paragraphs = [p.strip() for p in ctx["ai_narrative"].split("\n") if p.strip()]
        ai_paras_html = "".join(f"<p>{p}</p>" for p in paragraphs)
        ai_block = f"""
        <section class="section">
            <h2>{PLUS_GLYPH_SVG}<span class="sec-title">경영 분석 요약</span><span class="sec-rule"></span></h2>
            <div class="ai-box">
                <div class="ai-kicker">MEDIEM CONSULTING NOTE</div>
                {ai_paras_html}
            </div>
        </section>"""

    bed_suffix = ""
    if ctx.get("total_beds"):
        bed_suffix = f" · 총 {ctx['total_beds']}병상"
        if ctx.get("occupancy") is not None:
            bed_suffix += f" (가동률 {ctx['occupancy']}%)"

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>일반병동 수익 보고서 - {ctx.get('hospital_name','')}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Playfair+Display:ital,wght@0,600;0,700;0,800;1,600&display=swap');

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

:root {{
    --navy-950: #050B18;
    --navy-900: #0A1428;
    --navy-800: #10203F;
    --navy-700: #182B52;
    --teal-400: #2FE6C6;
    --teal-600: #0FA98F;
    --blue-500: #1257E0;
    --gold-300: #E7CD8E;
    --gold-400: #D4AF63;
    --gold-600: #9A7A2C;
    --ink-900: #10151F;
    --ink-500: #56607A;
    --ink-300: #8B93A8;
    --paper: #FBFAF6;
    --paper-2: #F5F2E9;
    --line: #E3DFD2;
}}

@page {{ size: A4; margin: 0; }}

body {{
    font-family: 'Noto Sans KR', sans-serif;
    color: var(--ink-900);
    background: #C9CEDA;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}}

.page {{
    width: 210mm;
    min-height: 297mm;
    margin: 18px auto;
    background:
        radial-gradient(circle at 1px 1px, rgba(10,20,40,0.045) 1px, transparent 0) 0 0/3px 3px,
        var(--paper);
    box-shadow: 0 18px 44px rgba(5,11,24,0.28);
    position: relative;
    padding: 11mm;
}}

/* 이중 헤어라인 프레임 — 프로스펙터스/증서 톤 */
.frame {{
    position: relative;
    border: 1.4pt solid var(--navy-900);
    padding: 9mm 12mm 10mm 12mm;
    min-height: calc(297mm - 22mm);
}}
.frame::before {{
    content: "";
    position: absolute; inset: 4px;
    border: 0.6pt solid var(--gold-400);
    pointer-events: none;
}}

@media print {{
    body {{ background: none; }}
    .page {{ margin: 0; box-shadow: none; width: auto; min-height: auto; }}
}}

/* ---------- Masthead ---------- */
.masthead {{
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 9px;
    border-bottom: 0.6pt solid var(--gold-400);
    margin-bottom: 20px;
}}
.masthead .brandline {{
    display: flex; align-items: center; gap: 7px;
    font-size: 0.68rem; letter-spacing: 0.18em; color: var(--gold-600);
}}
.masthead .brandline .plus-glyph {{ width: 9px; height: 9px; fill: var(--teal-600); }}
.masthead .doc-date {{ font-size: 0.68rem; color: var(--ink-300); letter-spacing: 0.03em; }}

/* ---------- Header ---------- */
.report-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 22px;
}}
.report-header .title-block h1 {{
    font-family: 'Playfair Display', serif;
    font-weight: 800;
    font-size: 2.05rem;
    color: var(--navy-900);
    letter-spacing: -0.01em;
    line-height: 1.18;
}}
.report-header .title-block .subline {{
    display: flex; align-items: center; gap: 9px;
    margin-top: 10px;
}}
.report-header .subline .rule {{ width: 20px; height: 1.4px; background: var(--gold-400); }}
.report-header .subline .text {{
    font-size: 0.92rem; color: var(--ink-500);
}}
.report-header .subline .text b {{ color: var(--navy-900); font-weight: 600; }}
.report-header .logo-emblem {{ text-align: right; flex-shrink: 0; padding-left: 18px; }}
.report-header .logo-emblem img {{ height: 40px; }}

/* ---------- KPI ---------- */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-bottom: 28px;
}}
.kpi-card {{
    position: relative;
    background: linear-gradient(160deg, var(--navy-900) 0%, var(--navy-800) 100%);
    border: 0.6pt solid rgba(212,175,99,0.45);
    padding: 17px 18px 15px 18px;
    color: #fff;
    overflow: hidden;
}}
.kpi-card::before {{
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: linear-gradient(90deg, var(--gold-600), var(--gold-300), var(--gold-600));
}}
.kpi-card .kpi-mark {{ position: absolute; top: 10px; right: 12px; width: 11px; height: 11px; fill: rgba(47,230,198,0.55); }}
.kpi-card .kpi-label {{
    font-size: 0.68rem; color: var(--teal-400);
    letter-spacing: 0.1em; margin-bottom: 10px;
}}
.kpi-card .kpi-value {{
    font-family: 'Playfair Display', serif;
    font-size: 1.56rem; font-weight: 700;
    font-variant-numeric: tabular-nums;
}}
.kpi-card .kpi-sub {{ font-size: 0.68rem; color: #A9B4CE; margin-top: 6px; }}
.kpi-card .kpi-sub-detail {{ margin-top: 3px; color: #7E8AAE; line-height: 1.35; }}

/* ---------- Section ---------- */
.section {{ margin-bottom: 26px; }}
.section h2 {{
    display: flex; align-items: center; gap: 9px;
    margin-bottom: 13px;
}}
.section h2 .plus-glyph {{ width: 11px; height: 11px; fill: var(--teal-600); flex-shrink: 0; }}
.section h2 .sec-title {{
    font-family: 'Playfair Display', serif;
    font-weight: 700; font-size: 1.05rem; color: var(--navy-900);
    white-space: nowrap;
}}
.section h2 .sec-rule {{ flex: 1; height: 0.6pt; background: var(--line); margin-left: 4px; }}

table {{ width: 100%; border-collapse: collapse; font-size: 0.8rem; }}
thead th {{
    text-align: left; font-weight: 600; color: var(--ink-500);
    font-size: 0.68rem; letter-spacing: 0.04em;
    padding: 8px 9px; background: var(--paper-2);
    border-top: 0.8pt solid var(--navy-900);
    border-bottom: 0.8pt solid var(--navy-900);
}}
thead th.num, td.num {{ text-align: right; }}
tbody td {{ padding: 7.5px 9px; border-bottom: 0.5pt solid var(--line); }}
tbody tr:nth-child(even) {{ background: rgba(212,175,99,0.05); }}
td.num {{ font-variant-numeric: tabular-nums; }}
td.code {{ color: var(--ink-300); font-size: 0.72rem; }}
td.name-cell {{ font-size: 0.76rem; line-height: 1.3; max-width: 210px; }}
td.strong {{ font-weight: 700; color: var(--navy-900); }}
tr.warn td {{ color: #A6402F; }}
tfoot td {{
    padding: 9px 9px; font-size: 0.86rem; color: var(--navy-900);
    border-top: 0.5pt solid var(--line);
}}
tfoot tr:last-child td {{
    border-top: 1.1pt solid var(--gold-600);
    background: linear-gradient(90deg, rgba(212,175,99,0.10), transparent 60%);
    font-weight: 700; font-size: 0.98rem;
    font-family: 'Playfair Display', serif;
}}

/* ---------- Bars ---------- */
.bar-row {{ display: flex; align-items: center; gap: 12px; margin-bottom: 10px; }}
.bar-label {{ flex: 0 0 112px; font-size: 0.78rem; color: var(--ink-500); white-space: nowrap; }}
.bar-row.is-current .bar-label {{ color: var(--gold-600); font-weight: 600; }}
.bar-track {{ flex: 1 1 auto; min-width: 0; height: 11px; background: var(--paper-2); border: 0.4pt solid var(--line); border-radius: 20px; overflow: hidden; }}
.bar-fill {{ height: 100%; background: linear-gradient(90deg, var(--blue-500), var(--teal-400)); border-radius: 20px; }}
.bar-fill.current {{ background: linear-gradient(90deg, var(--gold-600), var(--gold-300)); }}
.bar-value {{
    flex: 0 0 150px; text-align: right; font-family: 'Playfair Display', serif; font-weight: 700;
    font-size: 0.86rem; font-variant-numeric: tabular-nums; color: var(--navy-900);
    white-space: nowrap;
}}
.bar-value .won {{ font-family: 'Noto Sans KR', sans-serif; font-weight: 400; font-size: 0.72rem; color: var(--ink-300); margin-left: 1px; }}

/* ---------- AI narrative ---------- */
.ai-box {{
    background: var(--paper-2);
    border-left: 2.4pt solid var(--gold-400);
    padding: 18px 20px 16px 20px;
    font-size: 0.85rem; line-height: 1.85; color: #2B3244;
}}
.ai-kicker {{
    font-size: 0.63rem; letter-spacing: 0.14em; color: var(--gold-600);
    margin-bottom: 10px;
}}
.ai-box p {{ margin-bottom: 10px; }}
.ai-box p:last-child {{ margin-bottom: 0; }}
.ai-box p:first-of-type::first-letter {{
    font-family: 'Playfair Display', serif; font-weight: 700; font-style: italic;
    font-size: 2.15rem; color: var(--gold-600); float: left;
    line-height: 0.75; padding-right: 6px; padding-top: 3px; padding-bottom: 2px;
}}

.muted {{ color: var(--ink-300); font-size: 0.78rem; }}

.report-footer {{
    margin-top: 26px; padding-top: 12px;
    border-top: 0.5pt solid var(--gold-400);
    display: flex; align-items: center; justify-content: space-between;
    font-size: 0.66rem; color: var(--ink-300);
}}
.report-footer .plus-glyph {{ width: 7px; height: 7px; fill: var(--gold-400); margin: 0 8px; vertical-align: middle; }}
.report-footer .brandmark {{ display: flex; align-items: center; color: var(--ink-500); letter-spacing: 0.04em; }}
</style>
</head>
<body>
<div class="page">
<div class="frame">

    <div class="masthead">
        <div class="brandline">{PLUS_GLYPH_SVG}WIVO COMPANY &nbsp;·&nbsp; MEDIEM CONSULTING</div>
        <div class="doc-date">작성일 {now_str}</div>
    </div>

    <div class="report-header">
        <div class="title-block">
            <h1>일반병동 수익 분석 보고서</h1>
            <div class="subline">
                <span class="rule"></span>
                <span class="text"><b>{ctx.get('hospital_name','')}</b> · 분석기간 {ctx.get('period_label','')}{bed_suffix}</span>
            </div>
        </div>
        <div class="logo-emblem">
            {f'<img src="{logo_uri}" alt="Wivo Company">' if logo_uri else ''}
        </div>
    </div>

    <div class="kpi-grid">
        <div class="kpi-card">
            {PLUS_GLYPH_SVG.replace('class="plus-glyph"', 'class="kpi-mark"')}
            <div class="kpi-label">TOTAL REVENUE</div>
            <div class="kpi-value">{_fmt(ctx['total_revenue'])}원</div>
            <div class="kpi-sub">적용 등급 {ctx.get('grade')}등급 기준</div>
        </div>
        <div class="kpi-card">
            {PLUS_GLYPH_SVG.replace('class="plus-glyph"', 'class="kpi-mark"')}
            <div class="kpi-label">병실료 소계</div>
            <div class="kpi-value">{_fmt(ctx['room_subtotal'])}원</div>
            <div class="kpi-sub">연인원 {ctx.get('total_patient_days'):,}일</div>
        </div>
        <div class="kpi-card">
            {PLUS_GLYPH_SVG.replace('class="plus-glyph"', 'class="kpi-mark"')}
            <div class="kpi-label">{ctx.get('night_type','야간간호료')}</div>
            <div class="kpi-value">{_fmt(ctx['night_amount'])}원</div>
            <div class="kpi-sub">1일당 {_fmt(ctx.get('night_unit_price', Decimal('0')))}원 × {ctx.get('night_patient_days',0):,}일</div>
            <div class="kpi-sub kpi-sub-detail">{ctx.get('night_detail','')}</div>
        </div>
    </div>

    <section class="section">
        <h2>{PLUS_GLYPH_SVG}<span class="sec-title">병실료 항목별 수익 상세</span><span class="sec-rule"></span></h2>
        <table>
            <thead>
                <tr>
                    <th>청구 항목명</th><th>재원구간</th><th class="num">환자일수</th>
                    <th class="num">단가(원)</th><th>수가코드</th><th class="num">금액(원)</th>
                </tr>
            </thead>
            <tbody>
                {_room_rows_html(ctx['room_lines'])}
            </tbody>
            <tfoot>
                <tr><td colspan="5">병실료 소계</td><td class="num">{_fmt(ctx['room_subtotal'])}</td></tr>
                <tr><td colspan="5">{ctx.get('night_type','야간간호료')} <span class="muted">({ctx.get('night_detail','')})</span></td><td class="num">{_fmt(ctx['night_amount'])}</td></tr>
                <tr><td colspan="5">총 수익</td><td class="num">{_fmt(ctx['total_revenue'])}</td></tr>
            </tfoot>
        </table>
    </section>

    <section class="section">
        <h2>{PLUS_GLYPH_SVG}<span class="sec-title">간호관리료 등급별 수익 비교</span><span class="sec-rule"></span></h2>
        <div class="bar-chart">
            {_grade_bars_html(ctx.get('grade_comparison', []))}
        </div>
        <p class="muted" style="margin-top:6px;">※ 동일한 재원일수 데이터를 각 등급의 수가에 적용했을 때의 예상 수익입니다.</p>
    </section>

    {ai_block}

    <div class="report-footer">
        <span>본 보고서는 업로드된 자체 수가 DB를 기준으로 자동 산출되었습니다. 실제 청구·심사 결과와 차이가 있을 수 있습니다.</span>
        <span class="brandmark">WIVO COMPANY{PLUS_GLYPH_SVG}MEDIEM</span>
    </div>

</div>
</div>
</body>
</html>"""
    return html
