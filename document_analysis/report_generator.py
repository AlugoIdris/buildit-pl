"""
Generates a branded PDF report from analysis results using ReportLab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

BRAND_ORANGE = colors.HexColor("#E8732A")
BRAND_DARK   = colors.HexColor("#1A1A1A")
HIGH_RED     = colors.HexColor("#D32F2F")
MED_AMBER    = colors.HexColor("#F57C00")
LOW_GREEN    = colors.HexColor("#388E3C")

SEVERITY_COLOR = {"HIGH": HIGH_RED, "MEDIUM": MED_AMBER, "LOW": LOW_GREEN}

def generate_pdf_report(report: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Header ──────────────────────────────────────────────────────────
    story.append(Paragraph(
        '<font color="#E8732A" size="22"><b>🏗️ BuildIt PL</b></font>',
        styles["Title"]
    ))
    story.append(Paragraph("Contract & Document Analysis Report", styles["Heading2"]))
    story.append(Paragraph(
        f'Document: <b>{report["document_name"]}</b> | Generated: {datetime.now().strftime("%d %b %Y %H:%M")}',
        styles["Normal"]
    ))
    story.append(HRFlowable(width="100%", color=BRAND_ORANGE, thickness=2))
    story.append(Spacer(1, 0.3*cm))

    # ── Risk Score Badge ─────────────────────────────────────────────────
    score       = report["risk_score"]
    score_color = SEVERITY_COLOR.get(score, MED_AMBER)
    story.append(Paragraph(
        f'Overall Risk: <font color="{score_color.hexval()}"><b>{score}</b></font> ' +
        f'({report["total_risks"]} issue(s) found)',
        styles["Heading3"]
    ))
    story.append(Spacer(1, 0.3*cm))

    # ── Summary ──────────────────────────────────────────────────────────
    story.append(Paragraph("<b>Document Summary</b>", styles["Heading3"]))
    story.append(Paragraph(report["summary"], styles["Normal"]))
    story.append(Spacer(1, 0.4*cm))

    # ── Risks ─────────────────────────────────────────────────────────────
    story.append(Paragraph("<b>Risk Analysis</b>", styles["Heading3"]))
    for level, risks in [("HIGH", report["risks_high"]),
                         ("MEDIUM", report["risks_medium"]),
                         ("LOW", report["risks_low"])]:
        for r in risks:
            c = SEVERITY_COLOR[level]
            story.append(Paragraph(
                f'<font color="{c.hexval()}"><b>[{level}]</b></font> {r["description"]}',
                styles["Normal"]
            ))
            if r.get("explanation"):
                story.append(Paragraph(f'→ {r["explanation"]}', styles["Normal"]))
            story.append(Spacer(1, 0.2*cm))

    if not any([report["risks_high"], report["risks_medium"], report["risks_low"]]):
        story.append(Paragraph("No specific risks identified.", styles["Normal"]))

    story.append(Spacer(1, 0.4*cm))

    # ── Missing Items ────────────────────────────────────────────────────
    story.append(Paragraph("<b>Missing or Unclear Items</b>", styles["Heading3"]))
    for i, item in enumerate(report["missing_items"], 1):
        story.append(Paragraph(f'{i}. {item}', styles["Normal"]))

    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", color=colors.lightgrey, thickness=1))
    story.append(Paragraph(
        "<i>Disclaimer: This report is AI-generated for informational purposes only. "
        "Always consult a licensed Polish attorney before signing any legal document.</i>",
        styles["Normal"]
    ))

    doc.build(story)
    return buffer.getvalue()
