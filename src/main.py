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
from storage import add_doctor_scan, get_scans_for_wallet

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
        window_width = 1100
        window_height = 720
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(980, 640)
        
        # Load appearance settings
        with open(PREFERENCES_PATH, encoding="utf-8") as f:
            data = json.load(f)
            ctk.set_appearance_mode(data['Appearance'])
            ctk.set_default_color_theme(data['ThemeColor'])

        self.scan_image = None
        self.current_scan_image_path = None
        self.ai_loading = False
        self.scan_output = None
        self.scan_history = []
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
        self.frame2.pack(side='right', pady=20, padx=(5,20), fill="y")
        self.frame2.configure(width=320)
        self.frame2.pack_propagate(False)
        
        self.tabview = ctk.CTkTabview(self.frame1)
        self.tabview.pack(pady=10, padx=10, fill="both", expand=True)
        self.current_scan_tab = self.tabview.add("Current Scan")
        self.history_tab = self.tabview.add("Previous Scans")

        self.results_frame = ctk.CTkScrollableFrame(self.current_scan_tab)
        self.results_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.history_frame = ctk.CTkScrollableFrame(self.history_tab)
        self.history_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
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

        self.refresh_scan_history()

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
                self.current_scan_image_path = file_path
                self.scan_output = self.scan_image(file_path)
                self.display_results(self.scan_output)
                self.tabview.set("Current Scan")
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

    def refresh_scan_history(self):
        """Reload this doctor's previous reports from local storage."""
        self.scan_history = get_scans_for_wallet(self.wallet_address) if self.wallet_address else []
        self.display_scan_history()

    def display_scan_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        title = ctk.CTkLabel(
            self.history_frame,
            text="Previous Scans",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title.pack(pady=(0, 10), anchor="w")

        if not self.scan_history:
            empty_label = ctk.CTkLabel(
                self.history_frame,
                text="No previous scans for this wallet yet.",
                font=ctk.CTkFont(size=12)
            )
            empty_label.pack(anchor="w", pady=(0, 8))
            return

        for scan in self.scan_history:
            row = ctk.CTkFrame(self.history_frame)
            row.pack(fill="x", pady=(0, 8))

            created_at = scan.get("CreatedAt", "")
            patient = scan.get("PatientName") or "Unknown patient"
            status = scan.get("BlockchainStatus") or "local"
            document_id = scan.get("DocumentId") or "No document ID"
            encrypted_cid = scan.get("EncryptedCid") or ""
            pdf_path = scan.get("PdfPath") or ""
            pdf_name = os.path.basename(pdf_path) if pdf_path else "No PDF saved"

            summary = (
                f"{created_at}\n"
                f"Patient: {patient} ({scan.get('PatientAge') or 'age unknown'})\n"
                f"Document: {document_id}\n"
                f"Blockchain: {status}\n"
                f"PDF: {pdf_name}"
            )
            if encrypted_cid:
                summary += f"\nEncrypted CID: {encrypted_cid}"

            ctk.CTkLabel(row, text=summary, justify="left", wraplength=560).pack(
                side="left",
                padx=10,
                pady=10,
                fill="x",
                expand=True,
            )

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.pack(side="right", padx=10, pady=10)

            pdf_exists = bool(pdf_path and os.path.exists(pdf_path))
            view_button = ctk.CTkButton(
                actions,
                text="View PDF",
                width=96,
                state="normal" if pdf_exists else "disabled",
                command=lambda path=pdf_path: self.open_pdf(path),
            )
            view_button.pack(pady=(0, 8))

            folder_button = ctk.CTkButton(
                actions,
                text="Folder",
                width=96,
                state="normal" if pdf_exists else "disabled",
                command=lambda path=pdf_path: self.open_pdf_folder(path),
            )
            folder_button.pack()

    def open_pdf_folder(self, pdf_path):
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Missing file", "The PDF file for this scan was not found.")
            return

        try:
            if os.name == "nt":
                import subprocess
                subprocess.Popen(["explorer", "/select,", os.path.normpath(pdf_path)])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", os.path.dirname(pdf_path)])
        except Exception as exc:
            messagebox.showerror("Open folder", f"Could not open the PDF folder: {exc}")

    def open_pdf(self, pdf_path):
        if not pdf_path or not os.path.exists(pdf_path):
            messagebox.showerror("Missing file", "The PDF file for this scan was not found.")
            return

        try:
            if os.name == "nt":
                os.startfile(pdf_path)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", pdf_path])
        except Exception as exc:
            messagebox.showerror("Open PDF", f"Could not open the PDF: {exc}")

    def generate_report_metadata(self):
        """Create a human-friendly filename and a short internal report ID."""
        now = datetime.now()
        report_id = f"REP-{now.strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        filename = f"Report_{now.strftime('%A_%Y-%m-%d_%H-%M-%S')}_{report_id}.pdf"
        return report_id, filename

    def write_report_metadata_file(
        self,
        file_path,
        document_id,
        blockchain_report_id,
        patient_name,
        patient_age,
        extra_metadata=None
    ):
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
        if extra_metadata:
            metadata.update(extra_metadata)
        with open(metadata_path, "w", encoding="utf-8") as metadata_file:
            json.dump(metadata, metadata_file, indent=2)
        return metadata_path

    def remember_scan(
        self,
        patient_name,
        patient_age,
        file_path,
        metadata_path,
        document_id,
        pdf_hash,
        blockchain_report_id,
        blockchain_status,
        publish_result=None,
    ):
        publish_result = publish_result or {}
        add_doctor_scan({
            "wallet_address": self.wallet_address or "",
            "doctor_name": self.name,
            "patient_name": patient_name,
            "patient_age": patient_age,
            "scan_image_path": self.current_scan_image_path,
            "pdf_path": file_path,
            "metadata_path": metadata_path,
            "document_id": document_id,
            "blockchain_report_id": blockchain_report_id,
            "pdf_hash": pdf_hash,
            "encrypted_cid": publish_result.get("encrypted_cid") or publish_result.get("cid"),
            "encryption_algorithm": publish_result.get("encryption_algorithm"),
            "blockchain_status": blockchain_status,
        })
        self.refresh_scan_history()

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
        blockchain_status = "not_published"
        publish_result = {}
        
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
                publish_result = result
                
                if result["success"]:
                    blockchain_status = "published"
                    metadata_path = self.write_report_metadata_file(
                        file_path,
                        report_id,
                        result.get("report_id") or blockchain_report_id,
                        Pname,
                        Page,
                        {
                            "pdf_hash": result.get("pdf_hash"),
                            "encrypted_cid": result.get("encrypted_cid"),
                            "encrypted_sha256": result.get("encrypted_sha256"),
                            "encryption_algorithm": result.get("encryption_algorithm"),
                            "encryption_key": result.get("encryption_key"),
                            "encryption_nonce": result.get("encryption_nonce"),
                            "encryption_tag": result.get("encryption_tag"),
                        },
                    )
                    messagebox.showinfo(
                        "Blockchain Success", 
                        "Report published to blockchain successfully!\n\n"
                        f"Document ID:\n{report_id}\n\n"
                        "The encrypted report was uploaded to Pinata and anchored on your local chain.\n"
                        f"Report ID:\n{result.get('report_id', 'Unavailable')}\n\n"
                        f"Metadata file saved at:\n{metadata_path}\n\n"
                        "The agent verifier can use this metadata file or auto-compute the ID from the PDF."
                    )
                else:
                    blockchain_status = "publish_failed"
                    metadata_path = self.write_report_metadata_file(
                        file_path,
                        report_id,
                        result.get("report_id") or blockchain_report_id,
                        Pname,
                        Page,
                        {
                            "pdf_hash": result.get("pdf_hash"),
                            "publish_error": result.get("error"),
                        },
                    )
                    messagebox.showwarning(
                        "Blockchain Warning", 
                        "PDF saved successfully, but blockchain publishing failed.\n\n"
                        f"Document ID:\n{report_id}\n\n"
                        f"{result['error']}\n\n"
                        f"Expected Report ID:\n{result.get('report_id', 'Unavailable')}\n\n"
                        f"Metadata file saved at:\n{metadata_path}"
                    )
            else:
                blockchain_status = "skipped"
                messagebox.showinfo(
                    "Success",
                    f"PDF report saved successfully at:\n{file_path}\n\n"
                    f"Document ID:\n{report_id}\n\n"
                    f"Predicted Blockchain Report ID:\n{blockchain_report_id or 'Unavailable'}\n\n"
                    f"Metadata file:\n{metadata_path}"
                )

            self.remember_scan(
                Pname,
                Page,
                file_path,
                metadata_path,
                report_id,
                pdf_hash,
                publish_result.get("report_id") or blockchain_report_id,
                blockchain_status,
                publish_result,
            )
                
        except ImportError:
            self.remember_scan(
                Pname,
                Page,
                file_path,
                metadata_path,
                report_id,
                pdf_hash,
                blockchain_report_id,
                "blockchain_module_missing",
            )
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
            self.remember_scan(
                Pname,
                Page,
                file_path,
                metadata_path,
                report_id,
                pdf_hash,
                blockchain_report_id,
                "blockchain_error",
            )
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
