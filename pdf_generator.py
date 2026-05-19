import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_font():
    """Register a Unicode-capable font for PDF. Falls back to Helvetica if no TTF found."""
    font_candidates = [
        # Common Vietnamese-supporting font names across platforms
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("UnicodeFont", path))
                return "UnicodeFont"
            except Exception:
                continue
    return "Helvetica"


FONT_NAME = register_font()


def build_pdf(transactions, user_name):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontName=FONT_NAME,
        fontSize=16,
        spaceAfter=6 * mm,
        textColor=colors.HexColor("#18181b"),
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=9,
        spaceAfter=4 * mm,
        textColor=colors.HexColor("#71717a"),
    )
    cell_style = ParagraphStyle(
        "Cell",
        parent=styles["Normal"],
        fontName=FONT_NAME,
        fontSize=8,
        leading=11,
        alignment=1,  # CENTER
    )
    cell_left = ParagraphStyle(
        "CellLeft", parent=cell_style, alignment=0
    )
    elements = []

    # Title row
    elements.append(Paragraph("Transaction Report", title_style))
    elements.append(
        Paragraph(
            f"User: {user_name} &nbsp;|&nbsp; "
            f"Total transactions: {len(transactions)} &nbsp;|&nbsp; "
            f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 3 * mm))

    # Table data
    header = ["Date", "Category", "Note", "Amount", "Type"]
    data = [header]

    total_income = 0.0
    total_expense = 0.0

    for txn in transactions:
        amt = txn.amount
        txn_type = txn.category.type
        if txn_type == "Income":
            total_income += amt
            amount_str = f"+${amt:,.2f}"
        else:
            total_expense += amt
            amount_str = f"-${amt:,.2f}"

        data.append([
            Paragraph(txn.date.strftime("%Y-%m-%d"), cell_style),
            Paragraph(f"{txn.category.name}", cell_style),
            Paragraph(txn.note or "\u2014", cell_left),
            Paragraph(amount_str, cell_style),
            Paragraph(txn_type, cell_style),
        ])

    # Summary row
    balance = total_income - total_expense
    data.append([
        Paragraph("<b>Summary</b>", cell_style),
        Paragraph("", cell_style),
        Paragraph("", cell_style),
        Paragraph(
            f"Income: <font color='#15803d'>+${total_income:,.2f}</font><br/>"
            f"Expense: <font color='#dc2626'>-${total_expense:,.2f}</font><br/>"
            f"Balance: ${balance:,.2f}",
            ParagraphStyle("SummaryCell", parent=cell_style, alignment=1, fontSize=8, leading=13),
        ),
        Paragraph("", cell_style),
    ])

    col_widths = [55 * mm, 45 * mm, 65 * mm, 45 * mm, 40 * mm]
    table = Table(data, colWidths=col_widths, repeatRows=1)

    table_style = TableStyle([
        # Header row
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#18181b")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_NAME),
        ("FONTSIZE", (0, 0), (-1, 0), 8.5),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        # Body
        ("FONTNAME", (0, 1), (-1, -1), FONT_NAME),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -2), 0.5, colors.HexColor("#e4e4e7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        # Summary row
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f4f4f5")),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor("#18181b")),
        # Zebra stripes
        *[
            (("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fafafa")))
            for i in range(2, len(data) - 1, 2)
        ],
    ])
    table.setStyle(table_style)

    elements.append(table)
    doc.build(elements)
    buf.seek(0)
    return buf
