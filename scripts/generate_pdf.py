import os
from fpdf import FPDF

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Use fpdf2's built-in Unicode font for full UTF-8 support.
        # This avoids the latin-1 encoding issue that drops non-ASCII characters.
        self.add_font('DejaVu', '', os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf'), uni=True) if os.path.exists(os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf')) else None
        self._has_unicode_font = os.path.exists(os.path.join(os.path.dirname(__file__), 'fonts', 'DejaVuSans.ttf'))

    def _safe_text(self, text):
        """Sanitize text for PDF output, handling encoding gracefully."""
        if self._has_unicode_font:
            return text
        # Fallback: replace non-latin-1 characters instead of crashing
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(20, 50, 100)
        self.cell(0, 10, 'LLM Council Debate Report', border=0, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, f" {self._safe_text(title)}", border=0, fill=True, align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.set_text_color(0)
        self.multi_cell(0, 7, self._safe_text(body))
        self.ln(5)

def generate_debate_report(history, messages, verdicts, output_path):
    pdf = PDF()
    pdf.add_page()
    
    pdf.chapter_title('Topic / Prompt')
    pdf.chapter_body(history.title)
    
    pdf.chapter_title('Debate Transcript')
    for msg in messages:
        agent_header = f"[{msg.agent_name.upper()}] - {msg.timestamp.strftime('%H:%M:%S')}"
        pdf.set_font('helvetica', 'B', 11)
        pdf.cell(0, 7, agent_header, new_x="LMARGIN", new_y="NEXT")
        pdf.chapter_body(msg.content)
        
    if verdicts:
        pdf.chapter_title('Final Verdict')
        for v in verdicts:
            pdf.set_font('helvetica', 'B', 11)
            pdf.cell(0, 7, f"[JUDGE VERDICT] - Confidence: {v.confidence}", new_x="LMARGIN", new_y="NEXT")
            pdf.chapter_body(v.verdict_text)
            
    pdf.output(output_path)
    return output_path
