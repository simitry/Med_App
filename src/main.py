import customtkinter as ctk
from tkinter import filedialog
from test import scan_image
import json
import os

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Med-App")
        
        #get the screen width and height and center the app wonder in the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (800 // 2)
        y = (screen_height // 2) - (500 // 2)
        
        self.geometry(f"800x500+{x}+{y}")
        
        #load the theme and appearance from the file
        with open ('preferences.json') as f:
            data = json.load(f)
            ctk.set_appearance_mode(data['Appearance'])
            ctk.set_default_color_theme(data['ThemeColor'])
            
        # frame
        self.frame1 = ctk.CTkFrame(self)
        self.frame1.pack(side = 'left' ,pady=20, padx=(20,5), fill= "both",expand = True,ipadx=200,ipady=200)
        
        self.frame2 = ctk.CTkFrame(self)
        self.frame2.pack(side = 'right',pady=20, padx=(5,20), fill="both", expand=True)
        
        #label for button "brouse"
        label1 = ctk.CTkLabel(self.frame2, text ="X-Ray Image", font=("Arial", 12))
        label1.pack(pady=(10,0), padx=0)
        
        # load the user name
        with open ('config.json') as f:
            data = json.load(f)
            name = data['name']
        
        label2 = ctk.CTkLabel(self.frame1, text=f"Hello {name}!", font=("Arial", 12))
        label2.pack(pady=20, padx=0)
        
        # delete the file
        os.remove("config.json")
        
        # button
        browse = ctk.CTkButton(self.frame2, text='Browse', command = self.upload_file)
        browse.pack(pady=(0,20), padx=20, fill="both")
        
    def upload_file(self):
        # open a file dialog to select the image file
        file_path = filedialog.askopenfilename(title ="Select a file", filetypes=[("Images", "*.jpg")])
        if file_path:
            scan_output = scan_image(file_path)
            
            for disease in scan_output:
                print(f"{disease} : {scan_output[disease]:.2%}")
            
app = App()
app.mainloop()