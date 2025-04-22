import customtkinter as ctk
import subprocess
import sys
import json
import os
import signal

data = {
    "Appearance": " ",
    "ThemeColor": " ",
}

class SignalHandler:
    """handle the the case of quiting or destroying the app"""
    def __init__(self, app):
        self.app = app
        self.shutdown_requested = False
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)
    
    def request_shutdown(self):
        print("\nShutdown requested...")
        self.shutdown_requested = True
        self.app.quit()
    
    def can_run(self):
        return not self.shutdown_requested

class App(ctk.CTk):
    """preference app class"""
    def __init__(self):
        super().__init__()
        self.title("Med App")
        
        #center the app in the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (500 // 2)
        
        self.geometry(f"400x400+{x}+{y}")
        
        # Set initial theme
        ctk.set_appearance_mode("system")  # "system", "dark", or "light"
        ctk.set_default_color_theme("green")  # Default theme green
        
        # Build the UI
        self.rebuild_ui() 
        
        if os.path.exists("preferences.json"):
            with open("preferences.json", "r") as f:
                loaded_data = json.load(f)
                if loaded_data != data and loaded_data != " ":
                    self.confirm()
        else:
            with open("preferences.json", "w") as f:
                json.dump(data, f, indent=4)
            print('Json file created')
                
    def rebuild_ui(self):
        """Destroys and recreates all widgets (to apply new theme)"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        # Main frame
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Sample button
        self.button = ctk.CTkButton(self.frame, text="confirm", command=self.confirm)
        self.button.pack(pady=10)
        
        # Color theme switcher
        self.theme_label = ctk.CTkLabel(self.frame, text="Color Theme:")
        self.theme_label.pack(pady=(10, 5))
        
        self.theme_menu = ctk.CTkOptionMenu(
            self.frame,
            values=[" ","blue", "green", "dark-blue"],
            command=self.change_color_theme
        )
        self.theme_menu.pack(pady=5)
        
        # Dark/light mode switcher
        self.mode_label = ctk.CTkLabel(self.frame, text="Appearance Mode:")
        self.mode_label.pack(pady=(10, 5))
        
        self.mode_menu = ctk.CTkOptionMenu(
            self.frame,
            values=[" ","system", "dark", "light"],
            command=self.change_appearance_mode
        )
        self.mode_menu.pack(pady=5)
    
    def change_color_theme(self, new_theme):
        """Changes color theme and refreshes UI"""
        data["ThemeColor"] = new_theme
        ctk.set_default_color_theme(new_theme)
        self.rebuild_ui()  # Recreate widgets
    
    def change_appearance_mode(self, new_mode):
        """Changes light/dark mode (works instantly)"""
        data["Appearance"] = new_mode
        ctk.set_appearance_mode(new_mode)
        
    def create_pref(self):
        with open("preferences.json", "w") as f:
            json.dump(data, f, indent=4)
        print('Json file created')
    
    def confirm(self):
        if os.path.exists("preferences.json"):
            with open("preferences.json", "r") as f:
                loaded_data = json.load(f)
                if loaded_data["ThemeColor"] == " " or loaded_data["Appearance"] == " ":
                    self.create_pref()
        
        self.destroy()
        
        try:
            subprocess.Popen([sys.executable, "login.py"])
        except Exception as e:
            print(f"Error launching application: {e}")
        finally:
            sys.exit(0)

if __name__ == "__main__":
    app = App()
    handler = SignalHandler(app)
    
    try:
        app.mainloop()
    except KeyboardInterrupt:
        print("Application closed by user")
        app.quit()