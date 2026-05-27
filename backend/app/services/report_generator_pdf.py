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

REPORTLAB_AVAILABLE = False
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
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    # Daftarkan font Windows untuk dukungan Unicode penuh
    _REGISTERED_FONTS = {}
    _WINDOWS_FONT_DIR = r"C:\Windows\Fonts"
    
    _FONT_CANDIDATES = {
        'Times New Roman': ('times.ttf', 'timesbd.ttf', 'timesi.ttf', 'timesbi.ttf'),
        'Arial': ('arial.ttf', 'arialbd.ttf', 'ariali.ttf', 'arialbi.ttf'),
    }
    
    # Daftarkan font utama (Times New Roman + Arial)
    _FONT_REGISTRY = {}
    if os.path.exists(_WINDOWS_FONT_DIR):
        for _family, _files in _FONT_CANDIDATES.items():
            _variants = ['', 'Bold', 'Italic', 'BoldItalic']
            for _vf, _suffix in zip(_files, _variants):
                _fp = os.path.join(_WINDOWS_FONT_DIR, _vf)
                if os.path.exists(_fp):
                    _rname = f"{_family.replace(' ', '')}{_suffix}"
                    try:
                        if _fp.endswith('.ttc'):
                            pdfmetrics.registerFont(TTFont(_rname, _fp, subfontIndex=0))
                        else:
                            pdfmetrics.registerFont(TTFont(_rname, _fp))
                        _FONT_REGISTRY[_family + _suffix] = _rname
                        logger.info(f"Registered font: {_rname} from {_vf}")
                    except Exception as _e:
                        logger.warning(f"Failed to register {_vf}: {_e}")
    
    _fallback_fonts = []
    if os.path.exists(_WINDOWS_FONT_DIR):
        # Coba daftarkan font untuk Unicode fallback
        for _fn in ['segoeui.ttf', 'seguisym.ttf', 'cambria.ttc', 'calibri.ttf']:
            _fp = os.path.join(_WINDOWS_FONT_DIR, _fn)
            if os.path.exists(_fp):
                try:
                    _name = f"Fallback_{_fn.replace('.','_')}"
                    if _fn.endswith('.ttc'):
                        pdfmetrics.registerFont(TTFont(_name, _fp, subfontIndex=0))
                    else:
                        pdfmetrics.registerFont(TTFont(_name, _fp))
                    _fallback_fonts.append(_name)
                    logger.info(f"Registered fallback font: {_name}")
                except Exception:
                    pass
    
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"reportlab not installed: {e}")

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
    def generate(cls, project_id: str, results: Dict[str, Any], statistics: Dict[str, Any], survey_config: Optional[Dict[str, Any]] = None, report_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a complete PDF report.
        
        Args:
            report_data: Optional dict with 'title', 'summary', 'sections' from Step4 report outline
        
        Returns:
            Path to the generated PDF file
        """
        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("reportlab is required for PDF generation")

        chart_dir = cls._ensure_dirs()
        output_path = os.path.join(REPORTS_DIR, f"{project_id}.pdf")

        # ─── Font Configuration (standar paper ilmiah Indonesia: Times New Roman) ───
        TITLE_FONT = _FONT_REGISTRY.get('Times New Roman', 'Times-Roman')
        TITLE_BOLD = _FONT_REGISTRY.get('Times New RomanBold', 'Times-Bold')
        BODY_FONT = TITLE_FONT
        BODY_BOLD = TITLE_BOLD

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=4*cm,
            bottomMargin=3*cm,
            leftMargin=4*cm,
            rightMargin=3*cm
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title2', parent=styles['Title'], fontSize=14, fontName=TITLE_BOLD, spaceAfter=12, alignment=TA_CENTER, leading=18)
        subtitle_style = ParagraphStyle('Subtitle2', parent=styles['Normal'], fontSize=12, fontName=BODY_FONT, alignment=TA_CENTER, textColor=HexColor('#555555'), spaceAfter=8, leading=16)
        h1 = ParagraphStyle('H1', parent=styles['Heading1'], fontSize=14, fontName=TITLE_BOLD, spaceAfter=10, spaceBefore=18, textColor=HexColor('#000000'), leading=17)
        h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, fontName=BODY_BOLD, spaceAfter=6, spaceBefore=12, textColor=HexColor('#222222'), leading=15)
        body = ParagraphStyle('Body2', parent=styles['Normal'], fontSize=12, fontName=BODY_FONT, leading=18, spaceAfter=6, alignment=TA_JUSTIFY)
        body_center = ParagraphStyle('BodyCenter', parent=body, alignment=TA_CENTER)
        small = ParagraphStyle('Small', parent=styles['Normal'], fontSize=10, fontName=BODY_FONT, textColor=HexColor('#888888'), leading=13)

        h3_report = ParagraphStyle('H3report', parent=styles['Normal'], fontSize=12, fontName=BODY_BOLD, spaceAfter=4, spaceBefore=8, textColor=HexColor('#111111'))
        item_style = ParagraphStyle('Item', parent=body, fontSize=12, fontName=BODY_FONT, leading=17, leftIndent=10)
        table_guide = ParagraphStyle('TableGuide', parent=styles['Normal'], fontSize=10, fontName=BODY_FONT, leading=14, spaceAfter=6, spaceBefore=6, textColor=HexColor('#444444'), leftIndent=5, rightIndent=5, alignment=TA_JUSTIFY)
        table_cell = ParagraphStyle('TableCell', fontName=BODY_FONT, fontSize=8, leading=10, alignment=TA_LEFT)
        table_cell_center = ParagraphStyle('TableCellCenter', parent=table_cell, alignment=TA_CENTER)

        elements = []

        # ─── Title page ───
        elements.append(Spacer(1, 6*cm))
        elements.append(Paragraph("LAPORAN SURVEI AKADEMIK", title_style))
        elements.append(Spacer(1, 0.5*cm))

        title_text = survey_config.get('title', '') if survey_config else ''
        if title_text:
            elements.append(Paragraph(title_text, ParagraphStyle('TitleBig', parent=title_style, fontSize=14, fontName=TITLE_BOLD)))
        elements.append(Spacer(1, 1*cm))

        sim_type = survey_config.get('sim_type', 'academic') if survey_config else 'academic'
        type_map = {'academic': 'Akademik', 'political': 'Politik', 'market': 'Pasar', 'social': 'Sosial', 'custom': 'Kustom'}
        elements.append(Paragraph(f"Tipe: {type_map.get(sim_type, sim_type)}", subtitle_style))

        total_resp = statistics.get('total_respondents', 0)
        total_q = statistics.get('total_questions', 0)
        elements.append(Paragraph(f"Responden: {total_resp} | Pertanyaan: {total_q}", subtitle_style))
        elements.append(Paragraph(f"Diproses: {datetime.now().strftime('%d %B %Y %H:%M')}", ParagraphStyle('Date', parent=subtitle_style, fontSize=10)))
        elements.append(PageBreak())

        # ─── Ringkasan Laporan Simulasi (dari Step4) ───
        if report_data:
            elements.append(Paragraph("Ringkasan Laporan Simulasi", h1))
            r_title = report_data.get('title', '')
            r_summary = report_data.get('summary', '')
            r_sections = report_data.get('sections', [])
            if r_title:
                elements.append(Paragraph(r_title, h2))
            if r_summary:
                elements.append(Paragraph(r_summary, body))
            if r_sections:
                elements.append(Spacer(1, 0.3*cm))
                for sec in r_sections:
                    sec_title = sec.get('title', '') if isinstance(sec, dict) else str(sec)
                    if sec_title:
                        elements.append(Paragraph(f"• {sec_title}", item_style))
            elements.append(PageBreak())

        # ─── 1. Metodologi ───
        elements.append(Paragraph("1. Metodologi", h1))
        elements.append(Paragraph(
            f"Survei ini menggunakan metode kuantitatif dengan instrumen kuesioner daring. "
            f"Data dikumpulkan dari {total_resp} responden yang dipilih secara acak dari populasi simulasi. "
            f"Instrumen terdiri dari {total_q} pertanyaan yang mencakup skala Likert, pilihan ganda, dan pertanyaan terbuka.",
            body
        ))

        likert_scale = statistics.get('likert_scale', 5)
        elements.append(Paragraph(f"Skala Likert {likert_scale}-point digunakan untuk mengukur tingkat persetujuan responden.", body))
        elements.append(Spacer(1, 0.3*cm))

        # Reliability
        alpha = statistics.get('cronbach_alpha')
        if alpha is not None:
            reliability = "Tinggi" if alpha >= 0.7 else "Sedang" if alpha >= 0.5 else "Rendah"
            elements.append(Paragraph(f"Uji Reliabilitas (Cronbach's Alpha): {alpha:.3f} ({reliability})", h2))
        else:
            elements.append(Paragraph("Uji Reliabilitas: Tidak tersedia (min. 2 pertanyaan Likert diperlukan)", small))

        # ─── 2. Statistik Deskriptif (LANGSUNG, tanpa PageBreak) ───
        elements.append(Paragraph("2. Statistik Deskriptif", h1))
        descriptives = statistics.get('descriptives', {})
        if descriptives:
            elements.append(Paragraph(
                "Tabel berikut menyajikan statistik deskriptif dari setiap pertanyaan dalam survei. "
                "Kolom <b>N</b> menunjukkan jumlah responden yang menjawab pertanyaan tersebut. "
                "<b>Mean</b> (rata-rata) adalah nilai tengah dari seluruh jawaban responden pada skala Likert. "
                "<b>SD</b> (Standar Deviasi) mengukur seberapa bervariasi jawaban responden — semakin kecil nilai SD, "
                "maka jawaban responden cenderung seragam. Sebaliknya, SD yang besar berarti jawaban tersebar luas. "
                "Selain itu, <b>Min</b> dan <b>Max</b> menunjukkan skor terendah dan tertinggi, "
                "<b>Median</b> adalah nilai tengah dari data yang telah diurutkan, "
        "dan <b>Rel. Mean (%)</b> menyatakan rata-rata dalam bentuk persentase terhadap skala maksimum.",
                table_guide
            ))
            table_data = [["No", "Pertanyaan", "N", "Mean", "SD", "Min", "Max", "Median", "Rel. Mean (%)"]]
            for i, (qid, desc) in enumerate(descriptives.items(), 1):
                q_text = desc.get('question_text', qid)
                table_data.append([
                    str(i),
                    Paragraph(q_text, table_cell),
                    str(desc.get('n', 0)),
                    str(desc.get('mean', 0)),
                    str(desc.get('std_dev', 0)),
                    str(desc.get('min', 0)),
                    str(desc.get('max', 0)),
                    str(desc.get('median', 0)),
                    str(desc.get('relative_mean', 0))
                ])

            col_w = [10*mm, 50*mm, 10*mm, 12*mm, 10*mm, 10*mm, 10*mm, 12*mm, 16*mm]
            t = Table(table_data, colWidths=col_w, repeatRows=1)
            t.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, 0), BODY_BOLD),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                ('TEXTCOLOR', (0, 0), (-1, 0), white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F5F5F5')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 2),
                ('RIGHTPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(t)
            # Penjelasan setelah tabel
            elem_count = len(descriptives)
            elements.append(Paragraph(
                f"Tabel di atas merangkum data dari {elem_count} pertanyaan. "
                f"Untuk melihat kecenderungan jawaban, perhatikan nilai <b>Mean</b>: jika berada di atas titik tengah skala, "
                f"artinya responden cenderung setuju terhadap pernyataan tersebut. "
                f"<b>SD</b> yang kecil pada suatu pertanyaan menunjukkan pendapat responden relatif seragam. "
                f"Sementara itu, <b>Rel. Mean (%)</b> yang mendekati 100% berarti hampir seluruh responden memberikan skor tertinggi.",
                table_guide
            ))
        else:
            elements.append(Paragraph("Tidak ada data deskriptif yang tersedia.", body))

        elements.append(Spacer(1, 0.3*cm))

        # Summary text
        summary = statistics.get('summary', {})
        if summary and summary.get('text'):
            elements.append(Paragraph("Ringkasan:", h2))
            elements.append(Paragraph(summary['text'], body))

        # ─── 3. Distribusi Frekuensi (dengan grafik) ───
        elements.append(Paragraph("3. Distribusi Frekuensi", h1))
        frequencies = statistics.get('frequencies', {})

        for qid, freq in frequencies.items():
            q_text = freq.get('question_text', qid)
            elements.append(Paragraph(f"{qid}: {q_text}", h2))

            q_type = freq.get('type', 'likert')
            dist = freq.get('distribution', {})

            if q_type == 'likert' and dist:
                elements.append(Paragraph(
                    "Tabel berikut menunjukkan sebaran jawaban responden untuk setiap skor pada skala Likert. "
                    "Kolom <b>Skor</b> adalah nilai pada skala (misalnya 1–5). "
                    "<b>Frekuensi</b> adalah jumlah responden yang memilih skor tertentu, "
                    "dan <b>Persentase (%)</b> adalah proporsinya terhadap total responden (<b>N</b>). "
                    "Grafik batang di bawah tabel memvisualisasikan distribusi ini agar lebih mudah dipahami.",
                    table_guide
                ))
                table_data = [["Skor", "Frekuensi", "Persentase (%)"]]
                for score, data in dist.items():
                    table_data.append([score, str(data['count']), str(data['percentage'])])
                table_data.append(["Total", str(freq.get('total', 0)), "100.0"])

                t = Table(table_data, colWidths=[30*mm, 40*mm, 40*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), BODY_BOLD),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                    ('FONTNAME', (0, -1), (-1, -1), BODY_BOLD),
                ]))
                elements.append(t)

                # Cari skor dengan frekuensi tertinggi
                max_score = max(dist.items(), key=lambda x: x[1]['count'])
                elements.append(Paragraph(
                    f"Mayoritas responden memilih skor {max_score[0]} ({max_score[1]['percentage']}%), "
                    f"menunjukkan kecenderungan yang cukup jelas pada pertanyaan ini.",
                    table_guide
                ))

                chart_path = cls._generate_bar_chart(chart_dir, qid, dist, q_text, likert_scale)
                if chart_path:
                    elements.append(Spacer(1, 4*mm))
                    img = Image(chart_path, width=14*cm, height=8*cm)
                    elements.append(img)

            elif q_type == 'mcq' and dist:
                elements.append(Paragraph(
                    "Tabel berikut menampilkan distribusi jawaban untuk pertanyaan pilihan ganda. "
                    "Kolom <b>Pilihan</b> berisi opsi jawaban yang tersedia, "
                    "<b>Frekuensi</b> adalah jumlah responden yang memilih opsi tersebut, "
                    "dan <b>Persentase (%)</b> menyatakan proporsinya terhadap total responden (<b>N</b>).",
                    table_guide
                ))
                table_data = [["Pilihan", "Frekuensi", "Persentase (%)"]]
                for opt, data in dist.items():
                    table_data.append([str(opt)[:50], str(data['count']), str(data['percentage'])])
                table_data.append(["Total", str(freq.get('total', 0)), "100.0"])

                t = Table(table_data, colWidths=[70*mm, 30*mm, 30*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), BODY_BOLD),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                ]))
                elements.append(t)

                # Opsi dengan frekuensi tertinggi
                max_opt = max(dist.items(), key=lambda x: x[1]['count'])
                elements.append(Paragraph(
                    f"Opsi yang paling banyak dipilih adalah \"{max_opt[0]}\" ({max_opt[1]['count']} responden, {max_opt[1]['percentage']}%).",
                    table_guide
                ))

            elif q_type == 'open':
                responses = freq.get('responses', [])
                elements.append(Paragraph(
                    "Berikut adalah seluruh jawaban terbuka yang diberikan oleh responden. "
                    "Teks ini disajikan apa adanya tanpa perubahan ejaan atau tata bahasa.",
                    table_guide
                ))
                open_style = ParagraphStyle('OpenResponse', fontName=BODY_FONT, fontSize=11, leading=15, leftIndent=5, spaceAfter=3)
                for i, resp in enumerate(responses, 1):
                    elements.append(Paragraph(f"{i}. {resp}", open_style))

            elements.append(Spacer(1, 0.5*cm))

        # 4. Cross-tabulations
        cross_tabs = statistics.get('cross_tabs', [])
        if cross_tabs:
            elements.append(Paragraph("4. Tabulasi Silang Demografi", h1))
            elements.append(Paragraph(
                "Tabel berikut membandingkan rata-rata skor jawaban antar kelompok demografi. "
                "Tujuannya adalah untuk melihat apakah latar belakang responden memengaruhi cara mereka menjawab. "
                "Kolom <b>Kelompok</b> menunjukkan kategori demografi (misalnya pria/wanita untuk gender). "
                "<b>N</b> adalah jumlah responden di kelompok tersebut. "
                "<b>Mean</b> adalah rata-rata skor jawaban mereka, dan <b>Std Dev</b> menunjukkan seberapa bervariasi jawaban di dalam kelompok tersebut. "
                "Semakin kecil Std Dev, maka jawaban anggota kelompok tersebut semakin seragam.",
                table_guide
            ))
            for ct in cross_tabs:
                field_label = {'age': 'Usia', 'gender': 'Gender', 'education': 'Pendidikan', 'occupation': 'Pekerjaan', 'personality': 'Kepribadian'}
                elements.append(Paragraph(f"Berdasarkan {field_label.get(ct['field'], ct['field'])}:", h2))
                table_data = [["Kelompok", "N", "Mean", "Std Dev"]]
                for g in ct.get('groups', []):
                    table_data.append([g['group'], str(g['n']), str(g['mean']), str(g.get('std', 0))])

                t = Table(table_data, colWidths=[40*mm, 25*mm, 35*mm, 35*mm], repeatRows=1)
                t.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, 0), BODY_BOLD),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 0), (-1, 0), HexColor('#333333')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#F9F9F9')]),
                ]))
                elements.append(t)
                # Penjelasan setelah tabel cross-tab
                groups = ct.get('groups', [])
                if groups:
                    max_g = max(groups, key=lambda g: g.get('mean', 0))
                    min_g = min(groups, key=lambda g: g.get('mean', 0))
                    max_std = max(groups, key=lambda g: g.get('std', 0))
                    elements.append(Paragraph(
                        f"Dari tabel di atas, kelompok \"{max_g['group']}\" memiliki rata-rata skor tertinggi ({max_g.get('mean', 0):.2f}), "
                        f"sementara \"{min_g['group']}\" memiliki rata-rata terendah ({min_g.get('mean', 0):.2f}). "
                        f"Kelompok \"{max_std['group']}\" memiliki Std Dev paling besar ({max_std.get('std', 0):.2f}), "
                        f"yang berarti jawaban di kelompok tersebut paling bervariasi dibandingkan kelompok lainnya. "
                        f"Secara umum, perbedaan antar kelompok ini menunjukkan bahwa faktor "
                        f"{field_label.get(ct['field'], ct['field'])} memengaruhi persepsi dan jawaban responden.",
                        table_guide
                    ))
                elements.append(Spacer(1, 0.3*cm))
        else:
            elements.append(Paragraph("4. Tabulasi Silang Demografi", h1))
            elements.append(Paragraph("Data tidak mencukupi untuk tabulasi silang (min. 2 kelompok demografi diperlukan).", small))

        # 5. Interpretation
        elements.append(Paragraph("5. Interpretasi", h1))
        interpretation = cls._generate_interpretation(statistics, survey_config)
        elements.append(Paragraph(interpretation, body))

        # 6. Conclusion
        elements.append(Paragraph("6. Kesimpulan", h1))
        conclusion = cls._generate_conclusion(statistics, total_resp, total_q)
        elements.append(Paragraph(conclusion, body))

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
            plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica', 'Microsoft YaHei', 'SimHei', 'SimSun']

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
    def _generate_conclusion(cls, statistics: Dict[str, Any], total_resp: int, total_q: int) -> str:
        """Generate an overall conclusion summarizing all findings."""
        lines = [
            f"Berdasarkan hasil analisis terhadap {total_resp} responden dengan {total_q} butir pertanyaan, "
            f"berikut adalah kesimpulan utama dari survei ini."
        ]

        descriptives = statistics.get('descriptives', {})
        if descriptives:
            means = [d['mean'] for d in descriptives.values() if 'mean' in d]
            if means:
                overall_mean = sum(means) / len(means)
                scale = statistics.get('likert_scale', 5)
                midpoint = (scale + 1) / 2
                direction = "cenderung positif/setuju" if overall_mean > midpoint else "cenderung negatif/tidak setuju" if overall_mean < midpoint else "berada pada titik netral"

                highest = max(descriptives.items(), key=lambda x: x[1].get('mean', 0))
                lowest = min(descriptives.items(), key=lambda x: x[1].get('mean', 0))
                lines.append(
                    f"Secara keseluruhan, rata-rata skor jawaban responden adalah {overall_mean:.2f} dari skala {scale} "
                    f"({direction}). Aspek dengan persetujuan tertinggi adalah "
                    f"\"{highest[1].get('question_text', highest[0])}\" "
                    f"(Mean = {highest[1].get('mean', 0):.2f}), sedangkan aspek dengan persetujuan terendah adalah "
                    f"\"{lowest[1].get('question_text', lowest[0])}\" "
                    f"(Mean = {lowest[1].get('mean', 0):.2f})."
                )

        alpha = statistics.get('cronbach_alpha')
        if alpha is not None:
            if alpha >= 0.7:
                lines.append(f"Instrumen survei memiliki reliabilitas yang baik (α = {alpha:.3f}), sehingga hasil yang diperoleh dapat dipercaya.")
            elif alpha >= 0.5:
                lines.append(f"Reliabilitas instrumen berada pada tingkat cukup (α = {alpha:.3f}). Beberapa pertanyaan mungkin perlu disesuaikan untuk meningkatkan konsistensi internal.")
            else:
                lines.append(f"Reliabilitas instrumen tergolong rendah (α = {alpha:.3f}). Disarankan untuk meninjau ulang konstruk pertanyaan pada survei selanjutnya.")

        cross_tabs = statistics.get('cross_tabs', [])
        if cross_tabs:
            lines.append("Analisis berdasarkan karakteristik demografi menunjukkan adanya perbedaan pola respons antar kelompok, yang menandakan bahwa latar belakang responden turut memengaruhi persepsi dan jawaban mereka.")

        lines.append(
            "Kesimpulan ini diharapkan dapat menjadi acuan bagi pengambil keputusan dalam menentukan langkah "
            "selanjutnya, baik untuk pengembangan instrumen maupun untuk tindakan lanjutan berdasarkan temuan survei."
        )

        return " ".join(lines)

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
