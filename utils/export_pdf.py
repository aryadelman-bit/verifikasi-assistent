from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from utils.generator import generate_return_text

def create_pdf():
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    title_style = styles['Heading1']
    title_style.alignment = 1 
    
    normal_style = styles['Normal']
    normal_style.fontSize = 11
    normal_style.spaceAfter = 8
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=5
    )

    story = []
    story.append(Paragraph("<b>Hasil Verifikasi Dokumen Standar Kegiatan Usaha</b>", title_style))
    story.append(Spacer(1, 20))
    
    text = generate_return_text()
    
    for line in text.split('\n'):
        line_str = line.strip()
        if not line_str:
            continue
            
        if line_str.startswith('- '):
            story.append(Paragraph(line_str, bullet_style))
        elif "Yth." in line_str or "Berkenaan dengan" in line_str or "Demikian disampaikan" in line_str or line_str.startswith("*"):
            story.append(Paragraph(line_str, normal_style))
        else:
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>{line_str}</b>", normal_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer