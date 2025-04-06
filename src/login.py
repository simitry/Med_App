import customtkinter as ctk
import json
import os
import pandas as pd

if not os.path.exists("login_mails/login_database.csv"):      
    # create empty dataframe
    df = pd.DataFrame(columns=["Name", "Email", "Password","Hospital"]) 
            
    # create the csv file
    df.to_csv("login_mails/login_database.csv", index = False)
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Connect")
        self.geometry("500x500")
        
        #read the preferences.json file
        with open ('preferences.json', "r") as f:
            data = json.load(f)
            ctk.set_appearance_mode(data["Appearance"])
            ctk.set_default_color_theme(data["ThemeColor"])

        #call the method to create the widgets
        self.login_widget()
        
        #----------------
        #switch between login and register
        #----------------

    def login_widget(self):#main frame
        login_frame = ctk.CTkFrame(self)
        login_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        #label
        label = ctk.CTkLabel(login_frame,text="Log in",font = ctk.CTkFont(size = 20, weight = "bold"))
        label.pack(pady=(20,50)) 
        
        #----------------------------------
        #add login and account creation
        #----------------------------------
        
        #entries
        entries = []
        placeholders_values = ["email","password"]
                
        #import place holders
        self.placeholders(login_frame,placeholders_values,entries)
        
        # login/register button
        submit = ctk.CTkButton(login_frame, text="Log in", command = lambda : self.login_database(entries)) #command-------------------------------
        submit.pack(pady=(0,20))
        
        # label to switch between the login and register widget
        register_label = ctk.CTkLabel(login_frame, text="Don't have an account? Register now!",cursor ="hand2", text_color="#3498db",font=("Arial", 12, "bold"))
        register_label.pack(pady=(0,20))
        register_label.bind("<Button-1>", self.To_register)
        
    def To_register(self, event = None):
        #clear the current frame and call the register method
        for widget in self.winfo_children():
            widget.destroy()
        self.register_widget()
    
    def To_login(self, event = None):
        #clear the current frame and call the login widget
        for widget in self.winfo_children():
            widget.destroy()
        self.login_widget()
    
    def register_widget(self):
        #register frame
        register_frame = ctk.CTkFrame(self)
        register_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        label = ctk.CTkLabel(register_frame,text="Register",font = ctk.CTkFont(size = 20, weight = "bold"))
        label.pack(pady=(20,50)) 
        
        entries = []
        placeholders_values = ["Full Name" , "Email" , "Password" , "Confirm Password" , "Hospital"]
        
        self.placeholders(register_frame,placeholders_values,entries)
        
        submit = ctk.CTkButton(register_frame, text="Register") #command-----------------------
        submit.pack(pady=(0,20))
        
        register_label = ctk.CTkLabel(register_frame, text="Already have an account? Log in now!",cursor ="hand2", text_color="#3498db",font=("Arial", 12, "bold"))
        register_label.pack(pady=(0,20))
        
        #on click event
        register_label.bind("<Button-1>", self.To_login)
        
    # create placeholders
    def placeholders(self,frame,placeholders_values,entries):
        for i in placeholders_values:
            entry = ctk.CTkEntry(frame, placeholder_text= i)
            entry.pack(pady=(0, 20), padx = 15,fill="x")
            entries.append(entry)
    
    def login_database(self, entries):
        
        # read the csv file   
        df = pd.read_csv("login_mails/login_database.csv")
        user = entries[0].get()
        print(user)
        for names in df["Name"].values:
            if names == entries[0].get():
                print("gyaaaaaaaaaaaaat")
        
        
        
                    
                
# app = ctk.CTk()
# with open ('preferences.json', "r") as f:
#     data = json.load(f)
#     ctk.set_appearance_mode(data["Appearance"])
#     ctk.set_default_color_theme(data["ThemeColor"])
    
# app.geometry("500x500")
# app.title("test")


# app.mainloop()

if __name__ == "__main__":
    app = App()
    app.mainloop()