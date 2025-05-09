import customtkinter as ctk
from tkinter import filedialog, simpledialog
import json
import os
import threading
from tkinter import messagebox
from pdf import *

scan_output = " "

class App(ctk.CTk):
    """main app class"""
    def __init__(self, ai_ready=False):
        super().__init__()
        
        self.title("Med-App")
        self.ai_ready = ai_ready
        
        # Center the window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (800 // 2)
        y = (screen_height // 2) - (500 // 2)
        self.geometry(f"800x500+{x}+{y}")
        
        # Load appearance settings
        with open('preferences.json') as f:
            data = json.load(f)
            ctk.set_appearance_mode(data['Appearance'])
            ctk.set_default_color_theme(data['ThemeColor'])
            
        if not self.ai_ready:
            self.show_loading_screen()
            self.after(100, self.check_ai_status)
        else:
            self.show_main_interface()
    
    def show_loading_screen(self):
        """Show loading screen while AI loads"""
        self.loading_frame = ctk.CTkFrame(self)
        self.loading_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        self.loading_label = ctk.CTkLabel(
            self.loading_frame,
            text="Loading AI components...",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.loading_label.pack(pady=(150,50))
        
        self.progress = ctk.CTkProgressBar(self.loading_frame)
        self.progress.pack(pady=10, padx=20)
        self.progress.set(0)
        self.progress.start()
    
    def check_ai_status(self):
        """Check if AI is ready"""
        if hasattr(self, 'scan_image'):
            self.progress.stop()
            self.progress.set(1)
            self.after(500, self.show_main_interface)
        else:
            self.after(100, self.check_ai_status)
    
    def show_main_interface(self):
        """Show the main application interface"""
        # Clear loading screen if it exists
        if hasattr(self, 'loading_frame'):
            self.loading_frame.destroy()
        
        # Create main frames
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.pack(side='left', pady=20, padx=(20,5), fill="both", expand=True)
        
        self.frame2 = ctk.CTkFrame(self)
        self.frame2.pack(side='right', pady=20, padx=(5,20), fill="both", expand=True)
        
        # Results display area in frame1
        self.results_frame = ctk.CTkScrollableFrame(self.frame1)
        self.results_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Load user name
        with open('config.json') as f:
            data = json.load(f)
            self.name = data['name']
        
        # Display welcome message
        label2 = ctk.CTkLabel(self.frame2, text=f"Hello {self.name}!", font=("Arial", 16))
        label2.pack(pady=10, padx=0)
        
        # Label for button
        label1 = ctk.CTkLabel(self.frame2, text="X-Ray Image", font=("Arial", 12))
        label1.pack(pady=(10,0), padx=0)
        
        # Delete config file
        try:
            os.remove("config.json")
        except:
            pass
        
        # Add browse button
        browse = ctk.CTkButton(
            self.frame2, 
            text='Browse', 
            command=self.upload_file
        )
        browse.pack(pady=(0,20), padx=20, fill="both")
        
        Open_PDF = ctk.CTkButton(
            self.frame2, 
            text='Create PDF Report', 
            command=self.Generate_pdf_file
        )
        Open_PDF.pack(pady=(0,20), padx=20, fill="both")

    def upload_file(self):
        """Handle file upload and processing"""
        file_path = filedialog.askopenfilename(
            title="Select a file", 
            filetypes=[("Images", "*.jpg *.png")]
        )
        
        if file_path:
            try:
                global scan_output
                scan_output = self.scan_image(file_path)
                self.display_results(scan_output)
            except Exception as e:
                messagebox.showerror("Error", f"Error processing image: {e}")

    def display_results(self, results):
        """Display scan results in the results frame"""
        # Clear previous results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        # Add title
        title_label = ctk.CTkLabel(
            self.results_frame,
            text="Scan Results:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # Add each disease with probability
        for disease, probability in results.items():
            result_label = ctk.CTkLabel(
                self.results_frame,
                text=f"{disease}: {probability:.2%}",
                font=ctk.CTkFont(size=12)
            )
            result_label.pack(anchor="w", pady=2)

    def Generate_pdf_file(self):
        if scan_output == " ":
            messagebox.showinfo("Error", "You need to choose an image first!")
        else:
            Pname = simpledialog.askstring(
                "Patient name", 
                "Enter the patient name:", 
                parent=self
            )
            if Pname:  # Only proceed if name was entered
                Page = simpledialog.askstring(
                    "Patient age", 
                    "Enter the patient age:", 
                    parent=self
                )
                if Page:  # Only proceed if age was entered
                    
                    # Ask user where to save the file
                    file_path = filedialog.asksaveasfilename(
                    defaultextension=".pdf",
                    filetypes=[("PDF Files", "*.pdf")],
                    initialfile="Rapport.pdf",
                    title="Save PDF Report As"
                )
                
                if file_path:  # Only proceed if user didn't cancel
                    pdf = PDF()
                    pdf.add_page()
                    pdf.Header(Pname, Page, self.name)
                    pdf.Body(scan_output)
                    pdf.output(file_path)
                    messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")

def load_ai_components(app):
    """Load AI components in background"""
    try:
        from torch_ai import scan_image
        app.scan_image = scan_image
    except Exception as e:
        print(f"Failed to load AI components: {e}")

if __name__ == "__main__":
    # Create app with loading screen
    app = App(ai_ready=False)
    
    # Start loading AI components in background
    threading.Thread(target=load_ai_components, args=(app,), daemon=True).start()
    
    # Start the app
    app.mainloop()