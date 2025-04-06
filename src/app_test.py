import customtkinter as ctk
from tkinter import messagebox

# Set appearance mode and color theme
ctk.set_appearance_mode("System")  # "Light", "Dark", or "System"
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configure window
        self.title("CustomTkinter Example")
        self.geometry("600x400")
        
        # Create widgets
        self.create_widgets()
    
    def create_widgets(self):
        # Create a frame
        frame = ctk.CTkFrame(self)
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Label
        label = ctk.CTkLabel(frame, text="Welcome to CustomTkinter!", 
                            font=ctk.CTkFont(size=20, weight="bold"))
        label.pack(pady=12, padx=10)
        
        # Entry field
        self.entry = ctk.CTkEntry(frame, placeholder_text="Enter your name")
        self.entry.pack(pady=12, padx=10)
        
        # Button
        button = ctk.CTkButton(frame, text="Click Me", command=self.button_callback)
        button.pack(pady=12, padx=10)
        
        # Switch
        switch = ctk.CTkSwitch(frame, text="Dark Mode", command=self.toggle_dark_mode)
        switch.pack(pady=12, padx=10)
        
        # Slider
        self.slider = ctk.CTkSlider(frame, from_=0, to=100, command=self.slider_event)
        self.slider.pack(pady=12, padx=10)
        
        # Progress bar
        self.progressbar = ctk.CTkProgressBar(frame)
        self.progressbar.pack(pady=12, padx=10)
        self.progressbar.set(0)
        
        # Option menu
        optionmenu = ctk.CTkOptionMenu(frame, values=["Option 1", "Option 2", "Option 3"])
        optionmenu.pack(pady=12, padx=10)
        
        # Checkbox
        checkbox = ctk.CTkCheckBox(frame, text="Remember me")
        checkbox.pack(pady=12, padx=10)
    
    def button_callback(self):
        name = self.entry.get() or "User"
        messagebox.showinfo("Hello", f"Hello, {name}!")
        self.progressbar.set(0.5)  # Set progress to 50%
    
    def slider_event(self, value):
        print(f"Slider value: {int(value)}")
    
    def toggle_dark_mode(self):
        current_mode = ctk.get_appearance_mode()
        new_mode = "Light" if current_mode == "Dark" else "Dark"
        ctk.set_appearance_mode(new_mode)

if __name__ == "__main__":
    app = App()
    app.mainloop()