"""
Academic PDF Report Generator
Generates formatted PDF reports with statistics, charts, and methodology.
"""

import io
import os
import math
import statistics
from datetime import datetime
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.logger import get_logger
from ..utils.llm_client import LLMClient

logger = get_logger('mirofish.report.pdf')

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm, cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.colors import HexColor, black, white
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, KeepTogether
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("reportlab not installed, PDF generation disabled")

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logger.warning("matplotlib not installed, chart generation disabled")


REPORTS_DIR = os.path.join(Config.UPLOAD_FOLDER, 'pdf_reports')


class PDFReportGenerator:
    """
    Generates academic survey reports as PDFs with:
    - Title page
    - Methodology
    - Descriptive statistics tables
    - Bar charts for frequency distributions
    - Cross-tabulation tables
    - Cronbach's alpha
    - Interpretation
    """

    @classmethod
    def _ensure_dirs(cls):
        os.makedirs(REPORTS_DIR, exist_ok=True)
        chart_dir = os.path.join(REPORTS_DIR, '_charts')
        os.makedirs(chart_dir, exist_ok=True)
        return chart_dir

    @classmethod
    def generate(cls, project_id: str, results: Dict[str, Any], statistics: Dict[str, Any], survey_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a complete PDF report.
        
        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab is required for PDF generation")

        chart_dir = cls._ensure_dirs()
        output_path = os.path.join(REPORTS_DIR, f"{project_id}.pdf")

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=2*cm,
            bottomMargin=2*cm,
            leftMargin=2.5*cm,
            rightMargin=2.5*cm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=22, spaceAfter=20, alignment=TA_CENTER)
        subtitle_style = ParagraphStyle('Subtitle2', parent=styles['Normal'], fontSize=12, alignment=TA_CENTER, textColor=HexColor('#666666'), spaceAfter=30)
        h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=16, spaceAfter=12, spaceBefore=20, textColor=HexColor('#000000'))
        h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=13, spaceAfter=8, spaceBefore=14, textColor=HexColor('#333333'))
        body = ParagraphStyle('Body2', parent=styles['Normal'], fontSize=10, leading=15, spaceAfter=6, alignment=TA_JUSTIFY)
        body_center = ParagraphStyle('BodyCenter', parent=body, alignment=TA_CENTER)
        small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=8, textColor=HexColor('#999999'))

        elements = []

        # Title page
        elements.append(Spacer(1, 5*cm))
        elements.append(Paragraph("LAPORAN SURVEI AKADEMIK", title_style))
        elements.append(Spacer(1, 0.5*cm))

        title_text = survey_config.get('title', '') if survey_config else ''
        if title_text:
            elements.append(Paragraph(title_text, ParagraphStyle('TitleBig', parent=title_style, fontSize=18)))
        elements.append(Spacer(1, 1*cm))

        sim_type = survey_config.get('sim_type', 'academic') if survey_config else 'academic'
        type_map = {'academic': 'Akademik', 'political': 'Politik', 'market': 'Pasar', 'social': 'Sosial', 'custom': 'Kustom'}
        elements.append(Paragraph(f"Tipe: {type_map.get(sim_type, sim_type)}", subtitle_style))

        total_resp = statistics.get('total_respondents', 0)
        total_q = statistics.get('total_questions', 0)
        elements.append(Paragraph(f"Responden: {total_resp} | Pertanyaan: {total_q}", subtitle_style))
        elements.append(Paragraph(f"Diproses: {datetime.now().strftime('%d %B %Y %H:%M')}", ParagraphStyle('Date', parent=subtitle_style, fontSize=9)))
        elements.append(PageBreak())

        # 1. Methodology
        elements.append(Paragraph("1. Metodologi", h1))
        elements.append(Paragraph(
            f"Survei ini menggunakan metode kuantitatif dengan instrumen kuesioner daring. "
            f"Data dikumpulkan dari {total_resp} responden yang dipilih secara acak dari populasi simulasi. "
            f"Instrumen terdiri dari {total_q} pertanyaan yang mencakup skala Likert, pilihan ganda, dan pertanyaan terbuka.",
            body
        ))

        likert_scale = statistics.get('likert_scale', 5)
        elements.append(Paragraph(f"Skala Likert {likert_scale}-point digunakan untuk mengukur tingkat persetujuan responden.", body))
        elements.append(Spacer(1, 0.5*cm))

        # Reliability
        alpha = statistics.get('cronbach_alpha')
        if alpha is not None:
            reliability = "Tinggi" if alpha >= 0.7 else "Sedang" if alpha >= 0.5 else "Rendah"
            elements.append(Paragraph(f"Uji Reliabilitas (Cronbach's Alpha): {alpha:.3f} ({reliability})", h2))
        else:
            elements.append(Paragraph("Uji Reliabilitas: Tidak tersedia (min. 2 pertanyaan Likert diperlukan)", small))

        elements.append(PageBreak())

        # 2. Descriptive Statistics
        elements.append(Paragraph("2. Statistik Deskriptif", h1))
        descriptives = statistics.get('descriptives', {})
        if descriptives:
            table_data = [["No", "Pertanyaan", "N", "Mean", "SD", "Min", "Max", "Median", "Rel. Mean (%)"]]
            for i, (qid, desc) in enumerate(descriptives.items(), 1):
                q_text = desc.get('question_text', qid)[:60]
                table_data.append([
                    str(i),
                    q_text,
                    str(desc.get('n', 0)),
                    str(desc.get('mean', 0)),
                    str(desc.get('std_dev', 0)),
                    str(desc.get('min', 0)),
                    str(desc.get('max', 0)),
                    str(desc.get('median', 0)),
                    str(desc.get('relative_mean', 0))
                ])

            col_w = [20*mm, 70*mm, 15*mm, 15*mm, 15*mm, 12*mm, 12*mm, 15*mm, 15*mm]
            t = Table(table_data, colWidths=col_w, repeatRows=1)
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
            ]))
            elements.append(t)
        else:
            elements.append(Paragraph("Tidak ada data deskriptif yang tersedia.", body))

        elements.append(Spacer(1, 0.5*cm))

        # Summary text
        summary = statistics.get('summary', {})
        if summary and summary.get('text'):
            elements.append(Paragraph("Ringkasan:", h2))
            elements.append(Paragraph(summary['text'], body))

        elements.append(PageBreak())

        # 3. Frequency Distributions (with charts)
        elements.append(Paragraph("3. Distribusi Frekuensi", h1))
        frequencies = statistics.get('frequencies', {})

        for qid, freq in frequencies.items():
            q_text = freq.get('question_text', qid)
            elements.append(Paragraph(f"{qid}: {q_text}", h2))

            q_type = freq.get('type', 'likert')
            dist = freq.get('distribution', {})

            if q_type == 'likert' and dist:
                table_data = [["Skor", "Frekuensi", "Persentase (%)"]]
                for score, data in dist.items():
                    table_data.append([score, str(data['count']), str(data['percentage'])])
                table_data.append(["Total", str(freq.get('total', 0)), "100.0"])

                t = Table(table_data, colWidths=[30*mm, 40*mm, 40*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                    ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ]))
                elements.append(t)

                chart_path = cls._generate_bar_chart(chart_dir, qid, dist, q_text, likert_scale)
                if chart_path:
                    elements.append(Spacer(1, 4*mm))
                    img = Image(chart_path, width=14*cm, height=8*cm)
                    elements.append(img)

            elif q_type == 'mcq' and dist:
                table_data = [["Pilihan", "Frekuensi", "Persentase (%)"]]
                for opt, data in dist.items():
                    table_data.append([str(opt)[:50], str(data['count']), str(data['percentage'])])
                table_data.append(["Total", str(freq.get('total', 0)), "100.0"])

                t = Table(table_data, colWidths=[70*mm, 30*mm, 30*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                ]))
                elements.append(t)

            elif q_type == 'open':
                responses = freq.get('responses', [])
                elements.append(Paragraph(f"Total respons: {freq.get('total_responses', 0)}", body))
                for resp in responses[:5]:
                    elements.append(Paragraph(f"• {resp}", ParagraphStyle('Quote', parent=body, fontSize=9, leftIndent=10, textColor=HexColor('#555555'))))
                if len(responses) > 5:
                    elements.append(Paragraph(f"... dan {len(responses) - 5} respons lainnya", small))

            elements.append(Spacer(1, 0.5*cm))

        elements.append(PageBreak())

        # 4. Cross-tabulations
        cross_tabs = statistics.get('cross_tabs', [])
        if cross_tabs:
            elements.append(Paragraph("4. Tabulasi Silang Demografi", h1))
            for ct in cross_tabs:
                field_label = {'age': 'Usia', 'gender': 'Gender', 'education': 'Pendidikan', 'occupation': 'Pekerjaan', 'personality': 'Kepribadian'}
                elements.append(Paragraph(f"Berdasarkan {field_label.get(ct['field'], ct['field'])}:", h2))
                table_data = [["Kelompok", "N", "Mean", "Std Dev"]]
                for g in ct.get('groups', []):
                    table_data.append([g['group'], str(g['n']), str(g['mean']), str(g.get('std', 0))])

                t = Table(table_data, colWidths=[40*mm, 25*mm, 35*mm, 35*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.3*cm))
        else:
            elements.append(Paragraph("4. Tabulasi Silang Demografi", h1))
            elements.append(Paragraph("Data tidak mencukupi untuk tabulasi silang (min. 2 kelompok demografi diperlukan).", small))

        # 5. Interpretation
        elements.append(PageBreak())
        elements.append(Paragraph("5. Interpretasi", h1))
        interpretation = cls._generate_interpretation(statistics, survey_config)
        elements.append(Paragraph(interpretation, body))

        # Footer
        elements.append(Spacer(1, 3*cm))
        elements.append(Paragraph(f"— Laporan digenerate otomatis oleh MiroFish Survey Engine —", small))

        doc.build(elements)
        logger.info(f"PDF report generated: {output_path}")
        return output_path

    @classmethod
    def _generate_bar_chart(cls, chart_dir: str, qid: str, distribution: Dict, title: str, scale: int) -> Optional[str]:
        """Generate a bar chart for Likert frequency distribution."""
        if not MATPLOTLIB_AVAILABLE:
            return None

        try:
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

            labels = []
            values = []
            for i in range(1, scale + 1):
                key = str(i)
                labels.append(str(i))
                values.append(distribution.get(key, {}).get('count', 0))

            fig, ax = plt.subplots(figsize=(8, 4))
            colors = ['#FF4500' if v == max(values) else '#333333' for v in values]
            bars = ax.bar(labels, values, color=colors, edgecolor='white', linewidth=0.5)

            for bar, val in zip(bars, values):
                if val > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                            str(val), ha='center', va='bottom', fontsize=10, fontweight='bold')

            ax.set_xlabel('Skor Likert', fontsize=9)
            ax.set_ylabel('Frekuensi', fontsize=9)
            ax.set_title(title[:80], fontsize=11, fontweight='bold', pad=10)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.tick_params(axis='both', labelsize=8)
            ax.set_ylim(0, max(values) * 1.2 + 0.5)

            path = os.path.join(chart_dir, f"{qid}.png")
            plt.tight_layout()
            fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close(fig)
            return path

        except Exception as e:
            logger.warning(f"Chart generation failed for {qid}: {e}")
            return None

    @classmethod
    def _generate_interpretation(cls, statistics: Dict[str, Any], survey_config: Optional[Dict] = None) -> str:
        """Generate a plain-language interpretation of the statistics."""
        summary = statistics.get('summary', {})
        if summary.get('text'):
            base = summary['text']
        else:
            base = "Hasil survei menunjukkan variasi respons di antara para responden."

        descriptives = statistics.get('descriptives', {})
        if descriptives:
            means = [d['mean'] for d in descriptives.values() if 'mean' in d]
            if means:
                highest = max(descriptives.items(), key=lambda x: x[1].get('mean', 0))
                lowest = min(descriptives.items(), key=lambda x: x[1].get('mean', 0))
                base += (
                    f"\n\nPertanyaan dengan tingkat persetujuan tertinggi adalah "
                    f"\"{highest[1].get('question_text', highest[0])[:60]}\" "
                    f"(Mean = {highest[1].get('mean', 0):.2f}). "
                    f"Pertanyaan dengan tingkat persetujuan terendah adalah "
                    f"\"{lowest[1].get('question_text', lowest[0])[:60]}\" "
                    f"(Mean = {lowest[1].get('mean', 0):.2f})."
                )

        alpha = statistics.get('cronbach_alpha')
        if alpha is not None:
            if alpha >= 0.7:
                base += f"\n\nInstrumen survei memiliki konsistensi internal yang baik (α = {alpha:.3f}), menunjukkan bahwa pertanyaan-pertanyaan dalam survei ini reliabel dan dapat dipercaya."
            elif alpha >= 0.5:
                base += f"\n\nInstrumen survei memiliki konsistensi internal yang cukup (α = {alpha:.3f}), namun masih dapat ditingkatkan dengan merevisi beberapa pertanyaan."
            else:
                base += f"\n\nInstrumen survei memiliki konsistensi internal yang rendah (α = {alpha:.3f}). Disarankan untuk meninjau kembali pertanyaan-pertanyaan dalam survei."

        cross_tabs = statistics.get('cross_tabs', [])
        if cross_tabs:
            base += "\n\nAnalisis tabulasi silang menunjukkan variasi respons antar kelompok demografi:"
            for ct in cross_tabs:
                groups = ct.get('groups', [])
                if groups:
                    max_g = max(groups, key=lambda g: g.get('mean', 0))
                    min_g = min(groups, key=lambda g: g.get('mean', 0))
                    field_label = {'age': 'usia', 'gender': 'gender', 'education': 'pendidikan', 'occupation': 'pekerjaan', 'personality': 'kepribadian'}
                    base += f"\n- Berdasarkan {field_label.get(ct['field'], ct['field'])}: kelompok \"{max_g['group']}\" memiliki mean tertinggi ({max_g.get('mean', 0):.2f}) dan \"{min_g['group']}\" terendah ({min_g.get('mean', 0):.2f})."

        return base

    @classmethod
    def get_report_path(cls, project_id: str) -> Optional[str]:
        """Get the path to a generated PDF report."""
        path = os.path.join(REPORTS_DIR, f"{project_id}.pdf")
        return path if os.path.exists(path) else None

    @classmethod
    def delete_report(cls, project_id: str) -> bool:
        """Delete a generated PDF report."""
        path = cls.get_report_path(project_id)
        if path:
            os.remove(path)
            return True
        return False
