import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Multiple Entries Example")
        self.geometry("400x500")
        
        # Create a frame to contain our entries
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Create multiple entries
        self.entries = []
        labels = ["Username", "Email", "Password", "Confirm Password", "Phone Number"]
        
        for label_text in labels:
            # Add label
            label = ctk.CTkLabel(self.frame, text=label_text)
            label.pack(pady=(10, 0))
            
            # Add entry field
            entry = ctk.CTkEntry(self.frame)
            entry.pack(pady=(0, 10), padx=10, fill="x")
            self.entries.append(entry)
        
        # Add a button to collect all entries
        submit_btn = ctk.CTkButton(self.frame, text="Submit", command=self.get_entries)
        submit_btn.pack(pady=20)

    def get_entries(self):
        for i, entry in enumerate(self.entries):
            print(f"Entry {i+1}: {entry.get()}")

app = App()
app.mainloop()