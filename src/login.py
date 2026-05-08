import json
import os
import subprocess
import sys
import threading
import customtkinter as ctk
from tkinter import messagebox

from blockchain import BlockchainManager, load_blockchain_config, provision_doctor_identity
from storage import (
    get_doctor_by_wallet,
    get_registered_wallets,
    upsert_doctor_profile,
    write_current_user,
)


BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, "preferences.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")


class App(ctk.CTk):
    """Wallet-based doctor entrypoint."""

    def __init__(self):
        super().__init__()
        self.title("Connect Wallet")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 680
        window_height = 620
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(620, 560)

        if os.path.exists(PREFERENCES_PATH):
            with open(PREFERENCES_PATH, "r", encoding="utf-8") as preferences_file:
                preferences = json.load(preferences_file)
            ctk.set_appearance_mode(preferences.get("Appearance", "system"))
            ctk.set_default_color_theme(preferences.get("ThemeColor", "green"))

        self.manager = BlockchainManager()
        self.wallets = []
        self.selected_wallet = None
        self.wallet_menu = None
        self.status_label = None
        self.show_wallet_screen()
        self.refresh_wallets()

    def clear_ui(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_wallet_screen(self):
        self.clear_ui()

        frame = ctk.CTkFrame(self)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="Connect Doctor Wallet", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(28, 10))

        subtitle = ctk.CTkLabel(
            frame,
            text="Your wallet is now your doctor identity.",
            font=ctk.CTkFont(size=13),
        )
        subtitle.pack(pady=(0, 22))

        ctk.CTkLabel(frame, text="Available wallets").pack(pady=(0, 8))
        self.wallet_menu = ctk.CTkOptionMenu(frame, values=["Loading wallets..."])
        self.wallet_menu.pack(padx=28, pady=(0, 16), fill="x")
        self.wallet_menu.set("Loading wallets...")

        connect_button = ctk.CTkButton(frame, text="Connect Wallet", height=42, command=self.connect_selected_wallet)
        connect_button.pack(padx=28, pady=(0, 12), fill="x")

        refresh_button = ctk.CTkButton(frame, text="Refresh Wallets", command=self.refresh_wallets)
        refresh_button.pack(padx=28, pady=(0, 22), fill="x")

        self.status_label = ctk.CTkLabel(frame, text="", wraplength=460, justify="left")
        self.status_label.pack(padx=28, pady=(0, 18), fill="x")

    def set_status(self, message):
        if self.status_label:
            self.status_label.configure(text=message)

    def refresh_wallets(self):
        self.set_status("Connecting to the local blockchain and reading wallets...")

        def worker():
            wallets = []
            error = ""
            try:
                if self.manager.connect_to_blockchain():
                    wallets = self.manager.get_local_accounts()
                else:
                    error = self.manager.get_last_error()
            except Exception as exc:
                error = str(exc)

            self.after(0, lambda: self.finish_wallet_refresh(wallets, error))

        threading.Thread(target=worker, daemon=True).start()

    def finish_wallet_refresh(self, wallets, error):
        config = load_blockchain_config()
        configured_wallet = config.get("doctor_account_address")
        self.wallets = wallets or ([configured_wallet] if configured_wallet else [])

        if self.wallets:
            self.wallet_menu.configure(values=self.wallets)
            self.wallet_menu.set(self.wallets[0])
            self.set_status("Choose the wallet you want to use as your doctor identity.")
            return

        self.wallet_menu.configure(values=["No wallets found"])
        self.wallet_menu.set("No wallets found")
        self.set_status(error or "No local wallets were detected.")

    def connect_selected_wallet(self):
        wallet_address = self.wallet_menu.get().strip() if self.wallet_menu else ""
        if not wallet_address or wallet_address == "No wallets found" or wallet_address == "Loading wallets...":
            messagebox.showerror("Wallet required", "Please select a wallet first.")
            return

        self.selected_wallet = wallet_address
        profile = get_doctor_by_wallet(wallet_address)
        if profile and profile.get("Name"):
            if not bool(profile.get("BlockchainRegistered")):
                result = self.ensure_blockchain_profile(
                    profile.get("Name", ""),
                    profile.get("Email", ""),
                    profile.get("Hospital", ""),
                    wallet_address,
                )
                if not result["success"]:
                    messagebox.showerror("Blockchain Error", result["error"])
                    return
                profile = upsert_doctor_profile(
                    profile.get("Name", ""),
                    profile.get("Email", ""),
                    profile.get("Hospital", ""),
                    result["wallet_address"],
                    True,
                )

            write_current_user(profile)
            self.launch_main()
            return

        self.show_profile_screen(wallet_address)

    def show_profile_screen(self, wallet_address):
        self.clear_ui()

        frame = ctk.CTkFrame(self)
        frame.pack(pady=20, padx=20, fill="both", expand=True)

        title = ctk.CTkLabel(frame, text="Register Wallet Profile", font=ctk.CTkFont(size=22, weight="bold"))
        title.pack(pady=(26, 8))

        wallet_label = ctk.CTkLabel(frame, text=f"Wallet:\n{wallet_address}", wraplength=460, justify="left")
        wallet_label.pack(padx=28, pady=(0, 20), fill="x")

        entries = {}
        for label, key in [
            ("Full Name", "name"),
            ("Email", "email"),
            ("Hospital", "hospital"),
        ]:
            entry = ctk.CTkEntry(frame, placeholder_text=label)
            entry.pack(padx=28, pady=(0, 14), fill="x")
            entries[key] = entry

        register_button = ctk.CTkButton(
            frame,
            text="Register This Wallet",
            height=42,
            command=lambda: self.register_wallet_profile(wallet_address, entries),
        )
        register_button.pack(padx=28, pady=(8, 12), fill="x")

        back_button = ctk.CTkButton(frame, text="Choose Another Wallet", command=self.return_to_wallet_screen)
        back_button.pack(padx=28, pady=(0, 18), fill="x")

    def return_to_wallet_screen(self):
        self.show_wallet_screen()
        self.refresh_wallets()

    def ensure_blockchain_profile(self, name, email, hospital, wallet_address):
        try:
            return provision_doctor_identity(
                doctor_name=name,
                doctor_email=email,
                doctor_hospital=hospital,
                preferred_wallet=wallet_address,
                used_wallets=get_registered_wallets(exclude_wallet=wallet_address),
            )
        except Exception as exc:
            return {
                "success": False,
                "error": f"Blockchain identity setup failed: {exc}",
                "wallet_address": wallet_address,
            }

    def register_wallet_profile(self, wallet_address, entries):
        name = entries["name"].get().strip()
        email = entries["email"].get().strip()
        hospital = entries["hospital"].get().strip()

        if not all([name, email, hospital]):
            messagebox.showerror("Missing data", "Please fill in your name, email, and hospital.")
            return

        result = self.ensure_blockchain_profile(name, email, hospital, wallet_address)
        if not result["success"]:
            messagebox.showerror("Blockchain Error", result["error"])
            return

        profile = upsert_doctor_profile(
            name,
            email,
            hospital,
            result["wallet_address"],
            True,
        )
        write_current_user(profile)
        messagebox.showinfo("Wallet connected", "Wallet profile registered successfully.")
        self.launch_main()

    def launch_main(self):
        self.destroy()

        try:
            subprocess.Popen([sys.executable, MAIN_SCRIPT], cwd=BASE_DIR)
        except Exception as exc:
            print(f"Error launching application: {exc}")
        finally:
            sys.exit(0)


if __name__ == "__main__":
    app = App()
    app.mainloop()
