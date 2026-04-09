from fpdf import FPDF
import os

BASE_DIR = os.path.dirname(__file__)
HEADER_IMAGE_PATH = os.path.join(BASE_DIR, "img", "SRLF_1117647020.jpg")

class PDF(FPDF):
    def Header(self,Pname,Page,Dname,report_id):
        self.set_font("helvetica", style="B", size=18)
        self.cell(0,10, "Rapport",1, align='C')
        self.ln(30)
        self.set_font("helvetica" , style="U", size=13)
        self.cell(0,10, f"Doctor : {Dname}",align='L')
        self.ln(15)
        self.cell(0,10, f"Patient : {Pname}",align='L')
        self.ln(15)
        self.cell(0,10, f"Patient's age : {Page}",align='L')
        self.ln(15)
        self.cell(0,10, f"Document ID : {report_id}",align='L')
        
        self.cell(40)
        if os.path.exists(HEADER_IMAGE_PATH):
            self.image(HEADER_IMAGE_PATH,100,30,95)
        self.cell(5)
        self.ln(32)
        self.set_font("helvetica", style="U", size=18)
        self.cell(100,10,"Scan Results :", align='C')
        self.ln(15)

    def Body(self, scan):
        self.scan_output = scan
        self.set_font("helvetica", size=10)
        for disease in self.scan_output:
            self.cell(20,10,f"{disease} : {self.scan_output[disease]:.2%}", new_x='LMARGIN', new_y='NEXT')

