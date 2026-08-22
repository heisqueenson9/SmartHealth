"""
Smart Health Sync — Clinical case PDF report builder.
Authors: Enock Queenson Eduafo & Christabel Araba Edumadze | University of Ghana 2026
"""

import json
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
)

from backend.database.models import PreliminaryAssessment, AISummary

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle(
    "SHSTitle", parent=STYLES["Title"], fontSize=18, spaceAfter=4,
)
SECTION_STYLE = ParagraphStyle(
    "SHSSection", parent=STYLES["Heading2"], fontSize=13,
    spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1b3a4b"),
)
BODY_STYLE = ParagraphStyle(
    "SHSBody", parent=STYLES["BodyText"], fontSize=10, leading=14,
)
DISCLAIMER_STYLE = ParagraphStyle(
    "SHSDisclaimer", parent=STYLES["BodyText"], fontSize=8,
    textColor=colors.HexColor("#666666"), spaceBefore=16,
)


def _kv_table(pairs):
    data = [[Paragraph(f"<b>{k}</b>", BODY_STYLE), Paragraph(str(v) if v not in (None, "") else "—", BODY_STYLE)]
            for k, v in pairs]
    table = Table(data, colWidths=[5 * cm, 11 * cm])
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
    ]))
    return table


def generate_case_report_pdf(record, sections, signature, output_path):
    """
    Build a PDF for a DiagnosticRecord (clinical case), including only the
    requested sections, and write it to output_path.

    record: DiagnosticRecord instance (with its relationships available)
    sections: list[str] of section names to include (matches build_case_report's
              default list in routes.py)
    signature: doctor signature string
    output_path: full filesystem path to write the .pdf to
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title=f"Smart Health Sync Clinical Report — Case #{record.id}",
    )
    story = []

    story.append(Paragraph("Smart Health Sync", TITLE_STYLE))
    story.append(Paragraph("Clinical Decision Support Report", BODY_STYLE))
    story.append(Spacer(1, 10))

    patient = record.patient
    patient_name = (
        f"{patient.first_name or ''} {patient.last_name or ''}".strip() or patient.full_name
        if patient else (record.patient_reference or "Unrecorded")
    )

    if "Patient Details" in sections:
        story.append(Paragraph("Patient Details", SECTION_STYLE))
        story.append(_kv_table([
            ("Patient Reference", record.patient_reference or "—"),
            ("Patient Name", patient_name),
            ("Date of Birth", patient.date_of_birth.strftime("%d %b %Y") if patient and patient.date_of_birth else "—"),
            ("Gender", patient.gender if patient else "—"),
            ("Case ID", record.id),
            ("Report Generated", datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")),
        ]))

    if "Presenting Symptoms" in sections:
        story.append(Paragraph("Presenting Symptoms", SECTION_STYLE))
        symptoms = record.case_symptoms.all() if hasattr(record.case_symptoms, "all") else record.case_symptoms
        if symptoms:
            rows = [[s.display_name, s.severity or "—", f"{s.duration_value or '—'} {s.duration_unit or ''}".strip(), s.source or "—"]
                    for s in symptoms]
            data = [["Symptom", "Severity", "Duration", "Source"]] + rows
            t = Table(data, colWidths=[6 * cm, 3 * cm, 4 * cm, 3 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No symptoms recorded.", BODY_STYLE))

    if "Preliminary Assessment" in sections:
        story.append(Paragraph("Preliminary Assessment", SECTION_STYLE))
        pa = record.preliminary_assessments.order_by(
            PreliminaryAssessment.created_at.desc()
        ).first() if hasattr(record.preliminary_assessments, "order_by") else None
        if pa:
            story.append(Paragraph(pa.summary_text or "—", BODY_STYLE))
            for c in pa.candidates.all():
                story.append(Paragraph(
                    f"&bull; <b>{c.condition_name}</b> ({c.score}%) — {c.rationale or ''}"
                    + ("" if c.supported_by_biomarker_model else " <i>[No biomarker model available]</i>"),
                    BODY_STYLE,
                ))
            story.append(Paragraph(pa.disclaimer or "", DISCLAIMER_STYLE))
        else:
            story.append(Paragraph("No preliminary assessment recorded.", BODY_STYLE))

    if "Recommended Investigations" in sections or "Investigations Performed" in sections:
        story.append(Paragraph("Investigations", SECTION_STYLE))
        invs = record.case_investigations.all() if hasattr(record.case_investigations, "all") else record.case_investigations
        if invs:
            rows = [[ci.investigation.name if ci.investigation else "—", ci.priority or "—", ci.status or "—", ci.reason or "—"]
                    for ci in invs]
            data = [["Investigation", "Priority", "Status", "Reason"]] + rows
            t = Table(data, colWidths=[5 * cm, 2.5 * cm, 2.5 * cm, 6 * cm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1b3a4b")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dddddd")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No investigations recorded.", BODY_STYLE))

    if "Results/Biomarkers" in sections:
        story.append(Paragraph("Results / Biomarkers", SECTION_STYLE))
        biomarkers = json.loads(record.biomarkers_json) if record.biomarkers_json else {}
        if biomarkers:
            story.append(_kv_table(list(biomarkers.items())))
        else:
            story.append(Paragraph("No biomarker results recorded.", BODY_STYLE))

    if "Predicted Diagnosis" in sections:
        story.append(Paragraph("Predicted Diagnosis", SECTION_STYLE))
        story.append(_kv_table([
            ("Predicted Diagnosis", record.prediction_label or "Pending"),
            ("Confidence", f"{record.confidence_score:.1f}%" if record.confidence_score else "—"),
            ("Model Used", record.model_version or "—"),
        ]))
        story.append(Paragraph(
            "This is an algorithmic Predicted Diagnosis, not a Final Clinical Diagnosis. "
            "Clinical responsibility remains with the attending physician.",
            DISCLAIMER_STYLE,
        ))

    if "AI Clinical Summary" in sections:
        story.append(Paragraph("AI Simplified Explanation & Summary", SECTION_STYLE))
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
                    story.append(Paragraph(line, BODY_STYLE))
        else:
            story.append(Paragraph("No AI summary generated for this case.", BODY_STYLE))

    if "Doctor Notes" in sections:
        obs = (record.observations or record.doctor_remarks or "").strip()
        treat = (record.treatment_notes or "").strip()
        if obs or treat:
            story.append(Paragraph("Doctor Notes & Recommendations", SECTION_STYLE))
            if obs:
                story.append(Paragraph("<b>Observations</b>", BODY_STYLE))
                for line in obs.split("\n"):
                    if line.strip():
                        story.append(Paragraph(line, BODY_STYLE))
                story.append(Spacer(1, 4))
            if treat:
                story.append(Paragraph("<b>Treatment Plan</b>", BODY_STYLE))
                for line in treat.split("\n"):
                    if line.strip():
                        story.append(Paragraph(line, BODY_STYLE))

    if "Doctor Identity/Signature" in sections:
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Signed: {signature or '—'}", BODY_STYLE))
        story.append(Paragraph(datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC"), BODY_STYLE))

    doc.build(story)
    return output_path
