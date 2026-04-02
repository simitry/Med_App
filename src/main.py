import customtkinter as ctk
from tkinter import filedialog, simpledialog
import json
import os
import threading
from tkinter import messagebox
import sys
sys.path.append(os.path.dirname(__file__))
from pdf import PDF

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, 'preferences.json')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.json')

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
        with open(PREFERENCES_PATH, encoding="utf-8") as f:
            data = json.load(f)
            ctk.set_appearance_mode(data['Appearance'])
            ctk.set_default_color_theme(data['ThemeColor'])

        self.scan_image = None
        self.ai_loading = False
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
        self.name = "Doctor"
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get('name', self.name)
        
        # Display welcome message
        label2 = ctk.CTkLabel(self.frame2, text=f"Hello {self.name}!", font=("Arial", 16))
        label2.pack(pady=10, padx=0)
        
        # Label for button
        label1 = ctk.CTkLabel(self.frame2, text="X-Ray Image", font=("Arial", 12))
        label1.pack(pady=(10,0), padx=0)
        
        # Delete config file
        try:
            os.remove(CONFIG_PATH)
        except OSError:
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
        if not self.ensure_ai_loaded():
            return

        file_path = filedialog.askopenfilename(
            title="Select a file", 
            filetypes=[("Images", "*.jpg *.jpeg *.png")]
        )
        
        if file_path:
            try:
                global scan_output
                scan_output = self.scan_image(file_path)
                self.display_results(scan_output)
            except Exception as e:
                messagebox.showerror("Error", f"Error processing image: {e}")

    def ensure_ai_loaded(self):
        """Load the AI model on demand before scanning."""
        if callable(self.scan_image):
            return True

        if self.ai_loading:
            messagebox.showinfo("Loading", "AI components are still loading. Please try again in a moment.")
            return False

        self.ai_loading = True
        loading_dialog = ctk.CTkToplevel(self)
        loading_dialog.title("Loading")
        loading_dialog.geometry("320x120")
        loading_dialog.transient(self)
        loading_dialog.grab_set()

        label = ctk.CTkLabel(loading_dialog, text="Loading AI components...")
        label.pack(pady=(20, 10))

        progress = ctk.CTkProgressBar(loading_dialog)
        progress.pack(padx=20, fill="x")
        progress.start()

        error_holder = {"message": None}

        def loader():
            try:
                from torch_ai import scan_image as ai_scan_image
                self.scan_image = ai_scan_image
            except Exception as exc:
                error_holder["message"] = str(exc)
            finally:
                self.after(0, finish_loading)

        def finish_loading():
            progress.stop()
            loading_dialog.grab_release()
            loading_dialog.destroy()
            self.ai_loading = False

            if error_holder["message"]:
                messagebox.showerror("AI Error", f"Failed to load AI components: {error_holder['message']}")

        threading.Thread(target=loader, daemon=True).start()
        self.wait_window(loading_dialog)
        return callable(self.scan_image)

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
            return

        Pname = simpledialog.askstring(
            "Patient name", 
            "Enter the patient name:", 
            parent=self
        )
        if not Pname:
            return

        Page = simpledialog.askstring(
            "Patient age", 
            "Enter the patient age:", 
            parent=self
        )
        if not Page:
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile="Rapport.pdf",
            title="Save PDF Report As"
        )
        if not file_path:
            return

        pdf = PDF()
        pdf.add_page()
        pdf.Header(Pname, Page, self.name)
        pdf.Body(scan_output)
        pdf.output(file_path)
        
        # Blockchain integration
        try:
            from blockchain import publish_report
            
            blockchain_choice = messagebox.askyesno(
                "Blockchain Verification", 
                "Would you like to publish this report to the blockchain for verification?"
            )
            
            if blockchain_choice:
                provider_url = "https://mainnet.infura.io/v3/YOUR_INFURA_KEY"
                contract_address = "0xYOUR_CONTRACT_ADDRESS"
                
                success = publish_report(
                    file_path, 
                    Pname, 
                    Page,
                    provider_url,
                    contract_address
                )
                
                if success:
                    messagebox.showinfo(
                        "Blockchain Success", 
                        "Report published to blockchain successfully!\n\n"
                        "You can now verify the report integrity using the verification script."
                    )
                else:
                    messagebox.showwarning(
                        "Blockchain Warning", 
                        "PDF saved successfully, but blockchain publishing failed.\n\n"
                        "Please check your blockchain configuration and try again."
                    )
            else:
                messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")
                
        except ImportError:
            messagebox.showwarning(
                "Blockchain Module Missing", 
                "Blockchain module not found. PDF saved successfully.\n\n"
                "Install blockchain dependencies: pip install web3 eth-account eth-utils"
            )
            messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")
        except Exception as e:
            messagebox.showerror(
                "Blockchain Error", 
                f"PDF saved successfully, but blockchain error occurred:\n{str(e)}"
            )
            messagebox.showinfo("Success", f"PDF report saved successfully at:\n{file_path}")

if __name__ == "__main__":
    app = App(ai_ready=False)
    app.mainloop()
