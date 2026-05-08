import json
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from blockchain import BlockchainManager, load_blockchain_config


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, "preferences.json")


def apply_preferences():
    """Apply the saved CustomTkinter appearance settings when available."""
    if not os.path.exists(PREFERENCES_PATH):
        return

    with open(PREFERENCES_PATH, "r", encoding="utf-8") as preferences_file:
        preferences = json.load(preferences_file)

    ctk.set_appearance_mode(preferences.get("Appearance", "system"))
    ctk.set_default_color_theme(preferences.get("ThemeColor", "green"))


class VerifierMixin:
    """Shared report verification UI used by both standalone and child windows."""

    def _build_verifier_ui(self):
        self.pdf_path = None
        self.blockchain_config = load_blockchain_config()
        self.manager = BlockchainManager()

        title = ctk.CTkLabel(self, text="Medical Report Verifier", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(20, 10))

        rpc_url = self.blockchain_config.get("rpc_url", "Not configured")
        contract_address = self.blockchain_config.get("report_contract_address", "Not configured")

        ctk.CTkLabel(self, text=f"RPC URL: {rpc_url}", wraplength=560, justify="left").pack(padx=20, pady=(0, 6))
        ctk.CTkLabel(
            self,
            text=f"Report Contract: {contract_address}",
            wraplength=560,
            justify="left"
        ).pack(padx=20, pady=(0, 15))

        self.select_button = ctk.CTkButton(self, text="Select PDF Report", command=self.select_pdf)
        self.select_button.pack(pady=(0, 10))

        self.file_label = ctk.CTkLabel(self, text="No file selected")
        self.file_label.pack(pady=(0, 16))

        ctk.CTkLabel(self, text="Report ID").pack(pady=(0, 8))
        self.report_id_entry = ctk.CTkEntry(
            self,
            width=520,
            placeholder_text="Auto-filled from metadata or computed from the PDF"
        )
        self.report_id_entry.pack(padx=20, pady=(0, 16))

        self.report_id_hint = ctk.CTkLabel(self, text="Select a PDF to auto-fill the blockchain Report ID.")
        self.report_id_hint.pack(pady=(0, 12))

        self.verify_button = ctk.CTkButton(
            self,
            text="Verify Authenticity",
            command=self.verify_report
        )
        self.verify_button.pack(pady=(0, 16))

        self.result_box = ctk.CTkTextbox(self, width=580, height=180)
        self.result_box.pack(padx=20, pady=(0, 20), fill="both", expand=True)
        self._write_result("Choose a PDF and enter a report ID to verify the document against the blockchain.")

    def _write_result(self, text):
        self.result_box.configure(state="normal")
        self.result_box.delete("1.0", "end")
        self.result_box.insert("end", text)
        self.result_box.configure(state="disabled")

    def select_pdf(self):
        file_path = filedialog.askopenfilename(
            title="Select a report",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not file_path:
            return

        self.pdf_path = file_path
        self.file_label.configure(text=os.path.basename(file_path))
        self.autofill_report_id()

    def autofill_report_id(self):
        """Load the report id from the sidecar JSON file or compute it from the PDF."""
        if not self.pdf_path:
            return

        metadata_path = f"{os.path.splitext(self.pdf_path)[0]}.json"
        detected_report_id = None
        source_message = None

        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, "r", encoding="utf-8") as metadata_file:
                    metadata = json.load(metadata_file)
                detected_report_id = metadata.get("blockchain_report_id")
                if detected_report_id:
                    source_message = f"Report ID loaded from {os.path.basename(metadata_path)}."
            except Exception:
                detected_report_id = None

        if not detected_report_id:
            pdf_hash = self.manager.hash_pdf(self.pdf_path)
            if pdf_hash:
                detected_report_id = self.manager.generate_report_id(pdf_hash)
                source_message = "Report ID computed directly from the selected PDF."

        if detected_report_id:
            self.report_id_entry.delete(0, "end")
            self.report_id_entry.insert(0, detected_report_id)
            self.report_id_hint.configure(text=source_message or "Report ID detected.")
        else:
            self.report_id_hint.configure(text="Could not detect the Report ID automatically. Enter it manually.")

    def verify_report(self):
        report_id = self.report_id_entry.get().strip()
        if not self.pdf_path or not report_id:
            messagebox.showwarning("Missing data", "Please choose a PDF file and enter a report ID.")
            return

        if not self.manager.connect_to_blockchain():
            error_message = self.manager.get_last_error() or "Failed to connect to blockchain."
            self._write_result(f"Connection failed.\n\n{error_message}")
            messagebox.showerror("Connection error", error_message)
            return

        result = self.manager.verify_report(self.pdf_path, report_id)
        error_message = self.manager.get_last_error()

        if result == "VALID":
            verdict = "VERDICT: VALID\n\nThe PDF matches the blockchain record."
            self._write_result(verdict)
            messagebox.showinfo("Verification complete", "The report is valid.")
            return

        if result == "MODIFIED":
            verdict = "VERDICT: MODIFIED\n\nThe PDF hash does not match the blockchain record."
            self._write_result(verdict)
            messagebox.showerror("Verification failed", "The report appears to have been modified.")
            return

        self._write_result(f"VERDICT: ERROR\n\n{error_message or 'Verification failed.'}")
        messagebox.showerror("Verification error", error_message or "Verification failed.")


class VerifierWindow(ctk.CTkToplevel, VerifierMixin):
    """Verification tool embedded inside the main application."""

    def __init__(self, parent):
        super().__init__(parent)
        apply_preferences()
        self.title("Med App - Report Verifier")
        self.geometry("760x620")
        self.minsize(680, 560)
        self.transient(parent)
        self._build_verifier_ui()


class VerifierApp(ctk.CTk, VerifierMixin):
    """Standalone verifier entrypoint."""

    def __init__(self):
        super().__init__()
        apply_preferences()
        self.title("Med App - Report Verifier")
        self.geometry("760x620")
        self.minsize(680, 560)
        self._build_verifier_ui()


def open_verifier_window(parent):
    """Convenience helper for the main app."""
    window = VerifierWindow(parent)
    window.focus()
    return window


if __name__ == "__main__":
    app = VerifierApp()
    app.mainloop()
