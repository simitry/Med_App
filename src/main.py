import customtkinter as ctk
from tkinter import filedialog
import json
import os
import threading
import time

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
        self.frame1.pack(side='left', pady=20, padx=(20,5), fill="both", expand=True,ipadx=200,ipady=200)
        
        self.frame2 = ctk.CTkFrame(self)
        self.frame2.pack(side='right', pady=20, padx=(5,20), fill="both", expand=True)
        
        # Load user name
        with open('config.json') as f:
            data = json.load(f)
            name = data['name']
        
        # Label for button
        label1 = ctk.CTkLabel(self.frame2, text ="X-Ray Image", font=("Arial", 12))
        label1.pack(pady=(10,0), padx=0)
        
        # Display welcome message
        label2 = ctk.CTkLabel(self.frame1, text=f"Hello {name}!", font=("Arial", 12))
        label2.pack(pady=20, padx=0)
        
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

        
    def upload_file(self):
        """Handle file upload and processing"""
        if not hasattr(self, 'scan_image'):
            print("AI components not fully loaded yet")
            return
            
        file_path = filedialog.askopenfilename(
            title="Select a file", 
            filetypes=[("Images", "*.jpg *.png")]
        )
        
        if file_path:
            try:
                scan_output = self.scan_image(file_path)
                for disease in scan_output:
                    print(f"{disease} : {scan_output[disease]:.2%}")
            except Exception as e:
                print(f"Error processing image: {e}")

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