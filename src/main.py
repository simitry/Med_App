import customtkinter as ctk
from tkinter import filedialog, simpledialog
import json
import os
import threading
from datetime import datetime
from tkinter import messagebox
import sys
from uuid import uuid4
sys.path.append(os.path.dirname(__file__))
from pdf import PDF
from agent_app import open_verifier_window

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, 'preferences.json')
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config.json')

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
        self.scan_output = None
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
        self.wallet_address = None
        self.blockchain_registered = False
        self.verifier_window = None
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, encoding="utf-8") as f:
                data = json.load(f)
                self.name = data.get('name', self.name)
                self.wallet_address = data.get("wallet_address")
                self.blockchain_registered = data.get("blockchain_registered", False)
        
        # Display welcome message
        label2 = ctk.CTkLabel(self.frame2, text=f"Hello {self.name}!", font=("Arial", 16))
        label2.pack(pady=10, padx=0)
        
        # Label for button
        label1 = ctk.CTkLabel(self.frame2, text="X-Ray Image", font=("Arial", 12))
        label1.pack(pady=(10,0), padx=0)
        
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

        verify_button = ctk.CTkButton(
            self.frame2,
            text='Verify Existing Report',
            command=self.open_verifier
        )
        verify_button.pack(pady=(0, 20), padx=20, fill="both")

        if self.wallet_address:
            wallet_label = ctk.CTkLabel(
                self.frame2,
                text=f"Wallet: {self.wallet_address}",
                wraplength=250,
                justify="left"
            )
            wallet_label.pack(padx=20, pady=(0, 10))

        status_text = "Registered on blockchain" if self.blockchain_registered else "Blockchain registration pending"
        status_label = ctk.CTkLabel(self.frame2, text=status_text, font=("Arial", 12))
        status_label.pack(padx=20, pady=(0, 10))

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
                self.scan_output = self.scan_image(file_path)
                self.display_results(self.scan_output)
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

    def open_verifier(self):
        """Open the verification tool inside the current desktop app."""
        if self.verifier_window and self.verifier_window.winfo_exists():
            self.verifier_window.focus()
            return

        self.verifier_window = open_verifier_window(self)

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

    def generate_report_metadata(self):
        """Create a human-friendly filename and a short internal report ID."""
        now = datetime.now()
        report_id = f"REP-{now.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        filename = f"Report_{now.strftime('%A_%Y-%m-%d_%H-%M-%S')}_{report_id}.pdf"
        return report_id, filename

    def write_report_metadata_file(self, file_path, document_id, blockchain_report_id, patient_name, patient_age):
        """Save report identifiers next to the PDF so the agent can recover them later."""
        metadata_path = f"{os.path.splitext(file_path)[0]}.json"
        metadata = {
            "pdf_file": os.path.basename(file_path),
            "document_id": document_id,
            "blockchain_report_id": blockchain_report_id,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        }
        with open(metadata_path, "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=2)
        return metadata_path

    def Generate_pdf_file(self):
        if not self.scan_output:
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

        report_id, default_filename = self.generate_report_metadata()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            initialfile=default_filename,
            title="Save PDF Report As"
        )
        if not file_path:
            return

        pdf = PDF()
        pdf.add_page()
        pdf.Header(Pname, Page, self.name, report_id)
        pdf.Body(self.scan_output)
        pdf.output(file_path)

        from blockchain import hash_pdf, generate_report_id

        pdf_hash = hash_pdf(file_path)
        blockchain_report_id = generate_report_id(pdf_hash) if pdf_hash else None
        metadata_path = self.write_report_metadata_file(
            file_path,
            report_id,
            blockchain_report_id,
            Pname,
            Page,
        )
        
        # Blockchain integration
        try:
            from blockchain import publish_report_detailed, load_blockchain_config
            
            blockchain_choice = messagebox.askyesno(
                "Blockchain Verification", 
                "Would you like to publish this report to the blockchain for verification?"
            )
            
            if blockchain_choice:
                blockchain_config = load_blockchain_config()
                provider_url = blockchain_config.get("rpc_url")
                contract_address = blockchain_config.get("report_contract_address")
                
                result = publish_report_detailed(
                    file_path, 
                    Pname, 
                    Page,
                    provider_url,
                    contract_address,
                    doctor_account_address=self.wallet_address
                )
                
                if result["success"]:
                    messagebox.showinfo(
                        "Blockchain Success", 
                        "Report published to blockchain successfully!\n\n"
                        f"Document ID:\n{report_id}\n\n"
                        "The report was uploaded to Pinata and anchored on your local chain.\n"
                        f"Report ID:\n{result.get('report_id', 'Unavailable')}\n\n"
                        f"Metadata file saved at:\n{metadata_path}\n\n"
                        "The agent verifier can use this metadata file or auto-compute the ID from the PDF."
                    )
                else:
                    messagebox.showwarning(
                        "Blockchain Warning", 
                        "PDF saved successfully, but blockchain publishing failed.\n\n"
                        f"Document ID:\n{report_id}\n\n"
                        f"{result['error']}\n\n"
                        f"Expected Report ID:\n{result.get('report_id', 'Unavailable')}\n\n"
                        f"Metadata file saved at:\n{metadata_path}"
                    )
            else:
                messagebox.showinfo(
                    "Success",
                    f"PDF report saved successfully at:\n{file_path}\n\n"
                    f"Document ID:\n{report_id}\n\n"
                    f"Predicted Blockchain Report ID:\n{blockchain_report_id or 'Unavailable'}\n\n"
                    f"Metadata file:\n{metadata_path}"
                )
                
        except ImportError:
            messagebox.showwarning(
                "Blockchain Module Missing", 
                "Blockchain module not found. PDF saved successfully.\n\n"
                "Install blockchain dependencies: pip install web3 eth-account eth-utils"
            )
            messagebox.showinfo(
                "Success",
                f"PDF report saved successfully at:\n{file_path}\n\n"
                f"Document ID:\n{report_id}\n\n"
                f"Predicted Blockchain Report ID:\n{blockchain_report_id or 'Unavailable'}\n\n"
                f"Metadata file:\n{metadata_path}"
            )
        except Exception as e:
            messagebox.showerror(
                "Blockchain Error", 
                f"PDF saved successfully, but blockchain error occurred:\n{str(e)}"
            )
            messagebox.showinfo(
                "Success",
                f"PDF report saved successfully at:\n{file_path}\n\n"
                f"Document ID:\n{report_id}\n\n"
                f"Predicted Blockchain Report ID:\n{blockchain_report_id or 'Unavailable'}\n\n"
                f"Metadata file:\n{metadata_path}"
            )

if __name__ == "__main__":
    app = App(ai_ready=False)
    app.mainloop()
