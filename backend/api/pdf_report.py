"""
Smart Health Sync — Clinical case PDF report builder.
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026

Layout Fixes Implemented:
1. NumberedCanvas for dynamic "Page X of Y" and header/footer margins that never collide with content.
2. KeepTogether wrappers on logical section blocks (Predicted Diagnosis, Patient Details, Doctor Signature, Doctor Notes).
3. keepWithNext=True on SECTION_STYLE so section headers never appear orphaned at page bottoms.
4. Total table column widths engineered to match printable width (17.4 cm).
5. All table cell strings wrapped in Paragraph flowables to prevent text truncation/overflow.
"""

import json
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
)

from backend.database.models import PreliminaryAssessment, AISummary

STYLES = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "SHSTitle", parent=STYLES["Title"], fontSize=18, leading=22, spaceAfter=2,
    textColor=colors.HexColor("#1b3a4b"), alignment=0
)
SUBTITLE_STYLE = ParagraphStyle(
    "SHSSubtitle", parent=STYLES["BodyText"], fontSize=9.5, leading=13,
    textColor=colors.HexColor("#555555"), spaceAfter=10
)
SECTION_STYLE = ParagraphStyle(
    "SHSSection", parent=STYLES["Heading2"], fontSize=12, leading=15,
    spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1b3a4b"),
    keepWithNext=True
)
BODY_STYLE = ParagraphStyle(
    "SHSBody", parent=STYLES["BodyText"], fontSize=9.5, leading=13.5,
    textColor=colors.HexColor("#222222")
)
DISCLAIMER_STYLE = ParagraphStyle(
    "SHSDisclaimer", parent=STYLES["BodyText"], fontSize=8, leading=11,
    textColor=colors.HexColor("#666666"), spaceBefore=6, spaceAfter=4
)
TH_STYLE = ParagraphStyle(
    "SHSTableHeader", parent=STYLES["BodyText"], fontSize=9, leading=12,
    textColor=colors.white, fontName="Helvetica-Bold"
)
TD_STYLE = ParagraphStyle(
    "SHSTableCell", parent=STYLES["BodyText"], fontSize=8.5, leading=12,
    textColor=colors.HexColor("#222222")
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page count ('Page X of Y') and clean headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#666666"))

        # Header rule & page title (pages 2+)
        if self._pageNumber > 1:
            self.setLineWidth(0.5)
            self.setStrokeColor(colors.HexColor("#cccccc"))
            self.line(1.8 * cm, 28.1 * cm, 19.2 * cm, 28.1 * cm)
            self.drawString(1.8 * cm, 28.3 * cm, "Smart Health Sync — Clinical Case Decision Support Report")

        # Footer rule & page numbering
        self.setLineWidth(0.5)
        self.setStrokeColor(colors.HexColor("#cccccc"))
        self.line(1.8 * cm, 1.4 * cm, 19.2 * cm, 1.4 * cm)

        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(19.2 * cm, 0.9 * cm, page_text)
        self.drawString(1.8 * cm, 0.9 * cm, "Confidential Medical Decision Support Document · For Clinical Use Only")
        self.restoreState()


def _kv_table(pairs, col_widths=None):
    if col_widths is None:
        col_widths = [5.4 * cm, 12.0 * cm]  # Total = 17.4 cm printable width
    data = [[Paragraph(f"<b>{k}</b>", TD_STYLE), Paragraph(str(v) if v not in (None, "") else "—", TD_STYLE)]
            for k, v in pairs]
    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
    ]))
    return table


def generate_case_report_pdf(record, sections, signature, output_path):
    """
    Build a PDF for a DiagnosticRecord (clinical case) with zero page-break content collisions.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
        title=f"Smart Health Sync Clinical Report — Case #{record.id}",
    )
    story = []

    # Title & Subtitle Header
    story.append(Paragraph("Smart Health Sync", TITLE_STYLE))
    story.append(Paragraph("Clinical Decision Support Report", SUBTITLE_STYLE))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1b3a4b"), spaceAfter=10))

    patient = record.patient
    patient_name = (
        f"{patient.first_name or ''} {patient.last_name or ''}".strip() or patient.full_name
        if patient else (record.patient_reference or "Unrecorded")
    )

    # 1. PATIENT DETAILS
    if "Patient Details" in sections:
        p_table = _kv_table([
            ("Patient Reference", record.patient_reference or "—"),
            ("Patient Name", patient_name),
            ("Date of Birth", patient.date_of_birth.strftime("%d %b %Y") if patient and patient.date_of_birth else "—"),
            ("Gender", patient.gender if patient else "—"),
            ("Case ID", f"#{record.id}"),
            ("Report Generated", datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")),
        ])
        story.append(KeepTogether([
            Paragraph("Patient Details", SECTION_STYLE),
            p_table
        ]))

    # 2. PRESENTING SYMPTOMS
    if "Presenting Symptoms" in sections:
        sym_elements = [Paragraph("Presenting Symptoms", SECTION_STYLE)]
        symptoms = record.case_symptoms.all() if hasattr(record.case_symptoms, "all") else record.case_symptoms
        if symptoms:
            headers = [Paragraph("<b>Symptom</b>", TH_STYLE), Paragraph("<b>Severity</b>", TH_STYLE),
                       Paragraph("<b>Duration</b>", TH_STYLE), Paragraph("<b>Source</b>", TH_STYLE)]
            rows = [[Paragraph(s.display_name, TD_STYLE),
                     Paragraph(s.severity or "—", TD_STYLE),
                     Paragraph(f"{s.duration_value or '—'} {s.duration_unit or ''}".strip(), TD_STYLE),
                     Paragraph(s.source or "—", TD_STYLE)]
                    for s in symptoms]
            data = [headers] + rows
            t = Table(data, colWidths=[5.4 * cm, 3.0 * cm, 4.5 * cm, 4.5 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ]))
            sym_elements.append(t)
        else:
            sym_elements.append(Paragraph("No symptoms recorded for this case.", BODY_STYLE))

        if len(symptoms or []) <= 5:
            story.append(KeepTogether(sym_elements))
        else:
            story.extend(sym_elements)

    # 3. PRELIMINARY ASSESSMENT
    if "Preliminary Assessment" in sections:
        pa_elements = [Paragraph("Preliminary Assessment", SECTION_STYLE)]
        pa = record.preliminary_assessments.order_by(
            PreliminaryAssessment.created_at.desc()
        ).first() if hasattr(record.preliminary_assessments, "order_by") else None
        if pa:
            pa_elements.append(Paragraph(pa.summary_text or "—", BODY_STYLE))
            for c in pa.candidates.all():
                pa_elements.append(Paragraph(
                    f"&bull; <b>{c.condition_name}</b> ({c.score}%) — {c.rationale or ''}"
                    + ("" if c.supported_by_biomarker_model else " <i>[No biomarker model available]</i>"),
                    BODY_STYLE,
                ))
            if pa.disclaimer:
                pa_elements.append(Paragraph(pa.disclaimer, DISCLAIMER_STYLE))
        else:
            pa_elements.append(Paragraph("No preliminary assessment recorded.", BODY_STYLE))

        story.append(KeepTogether(pa_elements))

    # 4. INVESTIGATIONS
    if "Recommended Investigations" in sections or "Investigations Performed" in sections:
        inv_elements = [Paragraph("Investigations", SECTION_STYLE)]
        invs = record.case_investigations.all() if hasattr(record.case_investigations, "all") else record.case_investigations
        if invs:
            headers = [Paragraph("<b>Investigation Panel</b>", TH_STYLE), Paragraph("<b>Priority</b>", TH_STYLE),
                       Paragraph("<b>Status</b>", TH_STYLE), Paragraph("<b>Clinical Reason / Notes</b>", TH_STYLE)]
            rows = [[Paragraph(ci.investigation.name if ci.investigation else "—", TD_STYLE),
                     Paragraph(ci.priority or "—", TD_STYLE),
                     Paragraph(ci.status or "—", TD_STYLE),
                     Paragraph(ci.reason or "—", TD_STYLE)]
                    for ci in invs]
            data = [headers] + rows
            t = Table(data, colWidths=[5.4 * cm, 2.5 * cm, 2.5 * cm, 7.0 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e5e7eb")),
            ]))
            inv_elements.append(t)
        else:
            inv_elements.append(Paragraph("No investigations recorded.", BODY_STYLE))

        if len(invs or []) <= 5:
            story.append(KeepTogether(inv_elements))
        else:
            story.extend(inv_elements)

    # 5. RESULTS / BIOMARKERS
    if "Results/Biomarkers" in sections:
        bio_elements = [Paragraph("Results / Biomarkers", SECTION_STYLE)]
        biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        if biomarkers:
            pairs = list(biomarkers.items())
            t = _kv_table(pairs)
            bio_elements.append(t)
        else:
            bio_elements.append(Paragraph("No biomarker laboratory results recorded.", BODY_STYLE))

        if len(biomarkers or {}) <= 6:
            story.append(KeepTogether(bio_elements))
        else:
            story.extend(bio_elements)

    # 6. PREDICTED DIAGNOSIS & MACHINE LEARNING INFERENCE
    if "Predicted Diagnosis" in sections:
        pred_elements = [
            Paragraph("Predicted Diagnosis", SECTION_STYLE),
            _kv_table([
                ("Predicted Condition", record.prediction_label or "Pending"),
                ("Model Confidence", f"{record.confidence_score:.1f}%" if record.confidence_score else "—"),
                ("Model Version / Key", record.model_version or "—"),
                ("Diagnostic Case Status", record.case_status or "—"),
            ]),
            Paragraph(
                "Notice: This is an algorithmic decision-support prediction, not a final clinical diagnosis. "
                "Final clinical responsibility remains strictly with the attending physician.",
                DISCLAIMER_STYLE,
            )
        ]
        story.append(KeepTogether(pred_elements))

    # 7. AI CLINICAL SUMMARY & EXPLANATION
    if "AI Clinical Summary" in sections:
        ai_elements = [Paragraph("AI Simplified Explanation & Summary", SECTION_STYLE)]
        ai_summary = record.ai_summaries.order_by(
            AISummary.created_at.desc()
        ).first() if hasattr(record.ai_summaries, "order_by") else None

        summary_text = None
        if ai_summary and ai_summary.summary_text:
            summary_text = ai_summary.summary_text
        elif record.ai_explanation:
            summary_text = record.ai_explanation

        if summary_text:
            for line in summary_text.split("\n"):
                if line.strip():
                    ai_elements.append(Paragraph(line, BODY_STYLE))
        else:
            ai_elements.append(Paragraph("No AI clinical summary generated for this case.", BODY_STYLE))

        story.append(KeepTogether(ai_elements))

    # 8. DOCTOR NOTES & RECOMMENDATIONS
    if "Doctor Notes" in sections:
        obs = (record.observations or record.doctor_remarks or "").strip()
        treat = (record.treatment_notes or "").strip()
        if obs or treat:
            doc_elements = [Paragraph("Doctor Notes & Recommendations", SECTION_STYLE)]
            if obs:
                doc_elements.append(Paragraph("<b>Clinical Observations:</b>", BODY_STYLE))
                for line in obs.split("\n"):
                    if line.strip():
                        doc_elements.append(Paragraph(line, BODY_STYLE))
                doc_elements.append(Spacer(1, 4))
            if treat:
                doc_elements.append(Paragraph("<b>Treatment & Management Plan:</b>", BODY_STYLE))
                for line in treat.split("\n"):
                    if line.strip():
                        doc_elements.append(Paragraph(line, BODY_STYLE))

            story.append(KeepTogether(doc_elements))

    # 9. DOCTOR IDENTITY / SIGNATURE
    if "Doctor Identity/Signature" in sections:
        sig_elements = [
            Spacer(1, 15),
            HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=10),
            Paragraph(f"<b>Attending Physician Signature:</b> {signature or '—'}", BODY_STYLE),
            Paragraph(f"<b>Signed Date:</b> {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}", BODY_STYLE),
        ]
        story.append(KeepTogether(sig_elements))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path
