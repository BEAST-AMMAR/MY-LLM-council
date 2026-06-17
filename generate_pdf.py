import os
try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Run: pip install fpdf2")
    import sys
    sys.exit(1)

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'LLM Council v3.0 - Project Report', border=0, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 8, title, border=0, fill=True, align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.multi_cell(0, 6, body)
        self.ln()

def generate_report():
    pdf = PDF()
    pdf.add_page()
    
    # Overview
    pdf.chapter_title('1. Project Overview & Architecture')
    body1 = (
        "LLM Council v3.0 is a monumental shift from the legacy FastAPI/LiteLLM architecture to a fully offline, "
        "production-ready local inference stack. The platform is designed to provide secure, local, and private "
        "deliberations via a council of 5 independent AI models.\n\n"
        "Architecture Stack:\n"
        "- Frontend: Next.js (App Router), React, Tailwind CSS, Framer Motion for premium animations.\n"
        "- ML Inference Engine: Asynchronous Python microservice (aiohttp) paired with llama-cpp-python.\n"
        "- Containerization: Fully Dockerized via docker-compose with seamless network orchestration."
    )
    pdf.chapter_body(body1)
    
    # Security
    pdf.chapter_title('2. Security & Privacy Levels')
    body2 = (
        "Security is absolute in v3.0:\n"
        "- Offline Isolation: 100% of inference is executed locally using quantized GGUF models. No data is sent to external APIs (OpenAI/Anthropic).\n"
        "- API Protection: The ML Engine employs strict CORS policies. The frontend sanitizes all queries before sending them via Server Actions or sanitized REST hooks.\n"
        "- Dependency Risk: Removed obsolete, vulnerable libraries. Locked Next.js and Python dependencies."
    )
    pdf.chapter_body(body2)

    # Models
    pdf.chapter_title('3. Council Members & ML Models')
    body3 = (
        "The project automatically downloads heavily-optimized 1B to 3B parameter models for standard hardware:\n"
        "1. Sage (Philosopher) -> Llama-3.2-1B-Instruct-Q4\n"
        "2. Analyst (Logician) -> Qwen2.5-1.5B-Instruct-Q4\n"
        "3. Strategist (Visionary) -> Phi-3-mini-4k-instruct-Q4\n"
        "4. Skeptic (Challenger) -> Gemma-2-2B-it-Q4\n"
        "5. Judge (Head) -> Llama-3.2-3B-Instruct-Q4"
    )
    pdf.chapter_body(body3)

    # Output
    output_path = os.path.join(os.path.dirname(__file__), "LLM_Council_Project_Report.pdf")
    pdf.output(output_path)
    print(f"Report generated successfully at: {output_path}")

if __name__ == '__main__':
    generate_report()
