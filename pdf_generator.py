from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from io import BytesIO
from datetime import datetime


# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor("#0a1628")
MID_BLUE    = colors.HexColor("#0d2540")
ACCENT_BLUE = colors.HexColor("#00b8d4")
WHITE       = colors.white
LIGHT_GREY  = colors.HexColor("#c8daf0")
TEXT_GREY   = colors.HexColor("#4a6080")
CRITICAL    = colors.HexColor("#ff4b4b")
HIGH        = colors.HexColor("#ffb700")
MODERATE    = colors.HexColor("#00e5ff")
LOW         = colors.HexColor("#00ff9d")


def get_severity_color(severity):
    return {
        "CRITICAL": CRITICAL,
        "HIGH":     HIGH,
        "MODERATE": MODERATE,
        "LOW":      LOW
    }.get(severity.upper(), ACCENT_BLUE)


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        fontSize=20,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        alignment=TA_CENTER,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        fontSize=10,
        fontName="Helvetica",
        textColor=ACCENT_BLUE,
        alignment=TA_CENTER,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="DocMeta",
        fontSize=8,
        fontName="Helvetica",
        textColor=LIGHT_GREY,
        alignment=TA_CENTER,
        spaceAfter=2
    ))
    styles.add(ParagraphStyle(
        name="SectionTitle",
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=ACCENT_BLUE,
        spaceBefore=14,
        spaceAfter=6,
        leftIndent=0
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#2c3e50"),
        leading=15,
        alignment=TA_JUSTIFY,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="BulletItem",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#2c3e50"),
        leading=14,
        leftIndent=16,
        spaceAfter=3
    ))
    styles.add(ParagraphStyle(
        name="FieldLabel",
        fontSize=8,
        fontName="Helvetica-Bold",
        textColor=TEXT_GREY,
        spaceAfter=1
    ))
    styles.add(ParagraphStyle(
        name="FieldValue",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#1a252f"),
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="Footer",
        fontSize=7,
        fontName="Helvetica",
        textColor=TEXT_GREY,
        alignment=TA_CENTER
    ))
    return styles


def generate_report_pdf(report_data: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm,
        rightMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title=f"IARMS Outbreak Report — {report_data.get('report_id', '')}",
        author="IARMS System v1.0"
    )

    styles = build_styles()
    story  = []
    width  = A4[0] - 4*cm
    severity = report_data.get("severity", "LOW")
    sev_color = get_severity_color(severity)

    # ── HEADER BLOCK ─────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("IARMS", styles["DocTitle"]),
    ]]
    header_table = Table(header_data, colWidths=[width])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), DARK_BLUE),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [6]),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(header_table)

    subtitle_data = [[
        Paragraph(
            "Intelligent Advisory and Response Management System",
            styles["DocSubtitle"]
        )
    ]]
    subtitle_table = Table(subtitle_data, colWidths=[width])
    subtitle_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), DARK_BLUE),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(subtitle_table)

    meta_data = [[
        Paragraph(
            f"OUTBREAK RESPONSE REPORT &nbsp;|&nbsp; "
            f"Generated: {report_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}",
            styles["DocMeta"]
        )
    ]]
    meta_table = Table(meta_data, colWidths=[width])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), MID_BLUE),
        ("TOPPADDING",   (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        ("LEFTPADDING",  (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ── SEVERITY BANNER ───────────────────────────────────────────────────────
    sev_style = ParagraphStyle(
        "SevBanner",
        fontSize=12,
        fontName="Helvetica-Bold",
        textColor=WHITE,
        alignment=TA_CENTER
    )
    sev_data = [[Paragraph(f"ALERT LEVEL: {severity}", sev_style)]]
    sev_table = Table(sev_data, colWidths=[width])
    sev_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), sev_color),
        ("TOPPADDING",   (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 10),
        ("ROUNDEDCORNERS", (0, 0), (-1, -1), [4]),
    ]))
    story.append(sev_table)
    story.append(Spacer(1, 14))

    # ── REPORT METADATA TABLE ─────────────────────────────────────────────────
    story.append(Paragraph("REPORT INFORMATION", styles["SectionTitle"]))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=8
    ))

    meta_fields = [
        ["Report ID",  report_data.get("report_id", "—")],
        ["Disease",    report_data.get("disease",   "—")],
        ["Region",     report_data.get("region",    "—")],
        ["Timestamp",  report_data.get("timestamp", "—")],
        ["Severity",   severity],
    ]
    info_table_data = [
        [
            Paragraph(row[0], styles["FieldLabel"]),
            Paragraph(str(row[1]), styles["FieldValue"])
        ]
        for row in meta_fields
    ]
    info_table = Table(
        info_table_data,
        colWidths=[width * 0.3, width * 0.7]
    )
    info_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("BACKGROUND",   (1, 0), (1, -1), WHITE),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dce6f0")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # ── OUTBREAK DATA TABLE ───────────────────────────────────────────────────
    story.append(Paragraph("OUTBREAK DATA", styles["SectionTitle"]))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=8
    ))

    outbreak_fields = [
        ["Total Cases",     str(report_data.get("cases", "—"))],
        ["Total Deaths",    str(report_data.get("deaths", "—"))],
        ["Fatality Rate",   f"{float(report_data.get('fatality_rate', 0)) * 100:.2f}%"],
        ["Spread Rate",     f"{float(report_data.get('spread_rate', 0)) * 100:.2f}%"],
        ["Risk Score",      str(report_data.get("risk_score", "—"))],
        ["Resource Level",  str(report_data.get("resource_level", "—"))],
        ["Days Active",     str(report_data.get("days_active", "—"))],
    ]
    outbreak_table_data = [
        [
            Paragraph(row[0], styles["FieldLabel"]),
            Paragraph(row[1], styles["FieldValue"])
        ]
        for row in outbreak_fields
    ]
    outbreak_table = Table(
        outbreak_table_data,
        colWidths=[width * 0.3, width * 0.7]
    )
    outbreak_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (0, -1), colors.HexColor("#f0f4f8")),
        ("BACKGROUND",   (1, 0), (1, -1), WHITE),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dce6f0")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(outbreak_table)
    story.append(Spacer(1, 10))

    # ── CCE ───────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "1. COORDINATION AND CONTROL ENGINE (CCE)",
        styles["SectionTitle"]
    ))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=6
    ))
    story.append(Paragraph(
        f"The Coordination and Control Engine assessed the current outbreak "
        f"state and issued the following coordination action:",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"<b>Recommended Action:</b> {report_data.get('cce_recommendation', '—')}",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 8))

    # ── KAU ───────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "2. KNOWLEDGE-BASED ADVISORY UNIT (KAU)",
        styles["SectionTitle"]
    ))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=6
    ))
    story.append(Paragraph(
        f"The Knowledge-Based Advisory Unit generated the following health "
        f"advisory based on the outbreak profile:",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"<b>Outbreak Stage:</b> {report_data.get('kau_stage', '—')}",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"<b>Primary Advisory:</b> {report_data.get('kau_advisory', '—')}",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 8))

    # ── CRU ───────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "3. COMMUNICATION AND RESPONSE UNIT (CRU)",
        styles["SectionTitle"]
    ))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=6
    ))
    story.append(Paragraph(
        f"The Communication and Response Unit assessed the outbreak and "
        f"issued the following severity classification:",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"<b>Severity Classification:</b> {report_data.get('cru_severity', '—')}",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 8))

    # ── IDRU ──────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "4. INTELLIGENT DISTRIBUTION AND TRACKING UNIT (IDRU)",
        styles["SectionTitle"]
    ))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=6
    ))
    story.append(Paragraph(
        f"The Intelligent Distribution and Tracking Unit allocated resources "
        f"based on the severity classification.",
        styles["BodyText2"]
    ))
    story.append(Paragraph(
        f"<b>Total Units Allocated:</b> {report_data.get('resources_allocated', '—')}",
        styles["BodyText2"]
    ))

    allocations = report_data.get("allocations", [])
    if allocations:
        alloc_data = [[
            Paragraph("Region", styles["FieldLabel"]),
            Paragraph("Resource Type", styles["FieldLabel"]),
            Paragraph("Quantity", styles["FieldLabel"]),
            Paragraph("Priority Score", styles["FieldLabel"]),
            Paragraph("Status", styles["FieldLabel"]),
            Paragraph("Tracking ID", styles["FieldLabel"]),
        ]]
        for alloc in allocations:
            alloc_data.append([
                Paragraph(alloc.get("region_name", "—"), styles["FieldValue"]),
                Paragraph(alloc.get("resource_type", "—"), styles["FieldValue"]),
                Paragraph(str(alloc.get("quantity_allocated", "—")), styles["FieldValue"]),
                Paragraph(str(alloc.get("priority_score", "—")), styles["FieldValue"]),
                Paragraph(alloc.get("status", "—"), styles["FieldValue"]),
                Paragraph(alloc.get("tracking_id", "—"), styles["FieldValue"]),
            ])
        alloc_table = Table(
            alloc_data,
            colWidths=[
                width*0.2, width*0.2, width*0.1,
                width*0.15, width*0.15, width*0.2
            ]
        )
        alloc_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#f0f4f8")),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dce6f0")),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(Spacer(1, 6))
        story.append(alloc_table)
    story.append(Spacer(1, 8))

    # ── CEU ───────────────────────────────────────────────────────────────────
    story.append(Paragraph(
        "5. COLLABORATION AND ENGAGEMENT UNIT (CEU)",
        styles["SectionTitle"]
    ))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=6
    ))
    story.append(Paragraph(
        f"<b>Stakeholders Engaged:</b> {report_data.get('stakeholders_engaged', '—')}",
        styles["BodyText2"]
    ))
    story.append(Spacer(1, 8))

    # ── FULL WRITTEN REPORT ───────────────────────────────────────────────────
    story.append(Paragraph("FULL WRITTEN REPORT", styles["SectionTitle"]))
    story.append(HRFlowable(
        width=width, thickness=1,
        color=ACCENT_BLUE, spaceAfter=8
    ))
    written = report_data.get("written_report", "")
    for line in written.split("\n"):
        stripped = line.strip()
        if stripped:
            story.append(Paragraph(
                stripped.replace("&", "&amp;").replace("<", "&lt;"),
                styles["BodyText2"]
            ))
        else:
            story.append(Spacer(1, 4))

    # ── FOOTER ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(HRFlowable(
        width=width, thickness=0.5,
        color=TEXT_GREY, spaceAfter=6
    ))
    story.append(Paragraph(
        f"IARMS v1.0 &nbsp;|&nbsp; Intelligent Advisory and Response Management System &nbsp;|&nbsp; "
        f"Report ID: {report_data.get('report_id', '—')} &nbsp;|&nbsp; "
        f"Generated: {report_data.get('timestamp', '—')}",
        styles["Footer"]
    ))

    doc.build(story)
    return buffer.getvalue()