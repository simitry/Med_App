import customtkinter as ctk
import subprocess
import sys
import json
import os
import signal

data = {
    "Appearance": "system",
    "ThemeColor": "green",
}

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, "preferences.json")
WALLET_SCRIPT = os.path.join(BASE_DIR, "login.py")
AGENT_SCRIPT = os.path.join(BASE_DIR, "agent_app.py")


def load_preferences():
    """Load saved preferences or return defaults."""
    if not os.path.exists(PREFERENCES_PATH):
        return dict(data)

    with open(PREFERENCES_PATH, "r", encoding="utf-8") as preferences_file:
        loaded_data = json.load(preferences_file)

    preferences = dict(data)
    if loaded_data.get("ThemeColor") and loaded_data.get("Appearance"):
        preferences.update(loaded_data)
    return preferences

class SignalHandler:
    """handle the the case of quiting or destroying the app"""
    def __init__(self, app):
        self.app = app
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)
    
    def request_shutdown(self, signum, frame):
        print("\nShutdown requested...")
        self.shutdown_requested = True
        self.app.quit()
    
    def can_run(self):
        return not self.shutdown_requested

class App(ctk.CTk):
    """Startup app class."""
    def __init__(self):
        super().__init__()
        self.title("Med App")
        
        #center the app in the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        window_width = 620
        window_height = 620
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(560, 560)

        preferences = load_preferences()
        data.update(preferences)
        ctk.set_appearance_mode(data["Appearance"])
        ctk.set_default_color_theme(data["ThemeColor"])
        if not os.path.exists(PREFERENCES_PATH):
            self.create_pref()
            print("Json file created")

        self.show_role_selection()
                
    def clear_ui(self):
        """Destroy all current widgets before rebuilding the screen."""
        for widget in self.winfo_children():
            widget.destroy()

    def show_role_selection(self):
        """Show the first window where the user chooses doctor or agent mode."""
        self.clear_ui()

        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)

        title = ctk.CTkLabel(self.frame, text="Welcome to Med App", font=ctk.CTkFont(size=24, weight="bold"))
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            self.frame,
            text="Choose how you want to enter the application.",
            font=ctk.CTkFont(size=13)
        )
        subtitle.pack(pady=(0, 24))

        doctor_button = ctk.CTkButton(self.frame, text="Doctor", height=42, command=self.launch_wallet_connect)
        doctor_button.pack(padx=30, pady=(0, 14), fill="x")

        agent_button = ctk.CTkButton(self.frame, text="Agent", height=42, command=self.launch_agent)
        agent_button.pack(padx=30, pady=(0, 28), fill="x")

        settings_label = ctk.CTkLabel(self.frame, text="Display Settings", font=ctk.CTkFont(size=15, weight="bold"))
        settings_label.pack(pady=(0, 12))

        self.theme_label = ctk.CTkLabel(self.frame, text="Color Theme:")
        self.theme_label.pack(pady=(10, 5))

        self.theme_menu = ctk.CTkOptionMenu(
            self.frame,
            values=["blue", "green", "dark-blue"],
            command=self.change_color_theme
        )
        self.theme_menu.pack(pady=5)
        self.theme_menu.set(data["ThemeColor"])
        
        # Dark/light mode switcher
        self.mode_label = ctk.CTkLabel(self.frame, text="Appearance Mode:")
        self.mode_label.pack(pady=(10, 5))
        
        self.mode_menu = ctk.CTkOptionMenu(
            self.frame,
            values=["system", "dark", "light"],
            command=self.change_appearance_mode
        )
        self.mode_menu.pack(pady=5)
        self.mode_menu.set(data["Appearance"])

        save_button = ctk.CTkButton(self.frame, text="Save Preferences", command=self.confirm)
        save_button.pack(padx=30, pady=(24, 20), fill="x")
    
    def change_color_theme(self, new_theme):
        """Change color theme and refresh the startup screen."""
        data["ThemeColor"] = new_theme
        ctk.set_default_color_theme(new_theme)
        self.show_role_selection()
    
    def change_appearance_mode(self, new_mode):
        """Changes light/dark mode (works instantly)"""
        data["Appearance"] = new_mode
        ctk.set_appearance_mode(new_mode)
        
    def create_pref(self):
        with open(PREFERENCES_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print('Json file created')

    def launch_wallet_connect(self):
        """Close the preferences window and open wallet-based doctor entry."""
        self.destroy()

        try:
            subprocess.Popen([sys.executable, WALLET_SCRIPT], cwd=BASE_DIR)
        except Exception as e:
            print(f"Error launching application: {e}")
        finally:
            sys.exit(0)

    def launch_agent(self):
        """Close the startup window and open the agent verifier."""
        self.destroy()

        try:
            subprocess.Popen([sys.executable, AGENT_SCRIPT], cwd=BASE_DIR)
        except Exception as e:
            print(f"Error launching application: {e}")
        finally:
            sys.exit(0)
    
    def confirm(self):
        self.create_pref()
        self.show_role_selection()

if __name__ == "__main__":
    app = App()
    handler = SignalHandler(app)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user")
        app.quit()
