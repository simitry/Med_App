from fpdf import FPDF

class PDF(FPDF):
    def Header(self,Pname,Page,Dname):
        self.set_font("helvetica", style="B", size=18)
        self.cell(0,10, "Rapport",1, align='C')
        self.ln(30)
        self.set_font("helvetica" , style="U", size=13)
        self.cell(0,10, f"Doctor : {Dname}",align='L')
        self.ln(15)
        self.cell(0,10, f"Patient : {Pname}",align='L')
        self.ln(15)
        self.cell(0,10, f"Patient's age : {Page}",align='L')
        
        self.cell(40)
        self.image("img/SRLF_1117647020.jpg",100,30,100)
        self.cell(5)
        self.ln(40)
        self.set_font("helvetica", style="U", size=18)
        self.cell(100,10,"Scan Results :", align='C')
        self.ln(15)

    def Body(self, scan):
        self.scan_output = scan
        self.set_font("helvetica", size=10)
        for disease in self.scan_output:
            self.cell(20,10,f"{disease} : {self.scan_output[disease]:.2%}", new_x='LMARGIN', new_y='NEXT')

