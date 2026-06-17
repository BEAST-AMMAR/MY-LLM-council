import os
try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not installed. Run: pip install fpdf2")
    import sys
    sys.exit(1)

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 16)
        self.set_text_color(20, 50, 100)
        self.cell(0, 10, 'LLM Council v3.0 - Comprehensive Project Report', border=0, align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 14)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, f" {title}", border=0, fill=True, align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('helvetica', '', 11)
        self.set_text_color(0)
        self.multi_cell(0, 7, body)
        self.ln()

def generate_report():
    pdf = PDF()
    pdf.add_page()
    
    # Overview
    pdf.chapter_title('1. Project Overview & Architecture')
    body1 = (
        "LLM Council v3.0 is a fully offline, multi-agent AI deliberation system designed to provide high-quality "
        "reasoning on complex queries. It simulates a panel of 4 distinct AI agents (Philosopher, Logician, Visionary, Challenger) "
        "and 1 Judge. This architecture provides robust, multi-faceted analysis without relying on any external APIs.\n\n"
        "Architecture Stack:\n"
        "- Frontend: Next.js (App Router), React, Tailwind CSS, Framer Motion for JARVIS-style holographic UI.\n"
        "- ML Inference Engine: Asynchronous Python microservice (aiohttp) paired with llama-cpp-python.\n"
        "- Containerization: Fully Dockerized via docker-compose with seamless internal networking."
    )
    pdf.chapter_body(body1)
    
    # UI/UX & Features
    pdf.chapter_title('2. User Interface & Advanced Features')
    body2 = (
        "The frontend is designed with premium 'glassmorphism' aesthetics and includes several advanced features:\n"
        "- Voice Input: Integrated with the Web Speech API (webkitSpeechRecognition) for seamless verbal query input.\n"
        "- Text-to-Speech (TTS): Synthesizes the Judge's final verdict using the browser's native SpeechSynthesis API.\n"
        "- Real-Time Inference: Utilizes Server-Sent Events (SSE) to stream multiple LLM outputs concurrently to the browser.\n"
        "- Exporting: Allows the user to instantly download the complete council debate as JSON or Markdown."
    )
    pdf.chapter_body(body2)

    # Security
    pdf.chapter_title('3. Security & Privacy Levels')
    body3 = (
        "Security is absolute in v3.0:\n"
        "- Strict Headers: The Next.js application enforces Content-Security-Policy (CSP), X-Frame-Options (SAMEORIGIN), "
        "and Strict-Transport-Security to defend against XSS, clickjacking, and MITM attacks.\n"
        "- Offline Isolation: 100% of inference is executed locally using quantized GGUF models. Zero telemetry or data is sent to external APIs.\n"
        "- API Protection: The ML Engine employs strict CORS policies restricting access only to the frontend container, plus memory-based rate limiting to prevent abuse.\n"
        "- Dependency Risk: All dependencies are locked, and outdated legacy API wrappers have been removed."
    )
    pdf.chapter_body(body3)

    # Models
    pdf.chapter_title('4. Council Members & ML Models')
    body4 = (
        "The project leverages highly-optimized 1B to 3B parameter models designed for local CPU/GPU execution:\n"
        "1. Sage (Philosopher) -> Llama-3.2-1B-Instruct-Q4\n"
        "2. Analyst (Logician) -> Qwen2.5-1.5B-Instruct-Q4\n"
        "3. Strategist (Visionary) -> Phi-3-mini-4k-instruct-Q4\n"
        "4. Skeptic (Challenger) -> Gemma-2-2B-it-Q4\n"
        "5. Judge (Head) -> Llama-3.2-3B-Instruct-Q4"
    )
    pdf.chapter_body(body4)
    
    # Deployment
    pdf.chapter_title('5. Deployment Guidelines')
    body5 = (
        "The project is fully pre-configured for production deployment via Docker Compose:\n"
        "- Execute `docker-compose up --build -d` to launch both the frontend and ML engine containers.\n"
        "- The Next.js frontend will be exposed on port 3000, connecting internally to the ML engine on port 8001.\n"
        "- Hardware Requirements: Minimum 16GB RAM for concurrent inference of the 5 quantized models, with optional NVIDIA GPU acceleration config."
    )
    pdf.chapter_body(body5)

    # Output
    output_path = os.path.join(os.path.dirname(__file__), "LLM_Council_Project_Report.pdf")
    pdf.output(output_path)
    print(f"Report generated successfully at: {output_path}")

if __name__ == '__main__':
    generate_report()
