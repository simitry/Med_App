import customtkinter as ctk
from tkinter import messagebox
import json
import subprocess
import sys
import sqlite3


# create empty sqlite database
conn = sqlite3.connect("login_mails/database.db")
c = conn.cursor()

def check_table(table_name):
    c.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name=?;
    """, (table_name,))
    if not c.fetchone():
        return False
    return True
    
if not check_table("login"):
    c.execute("""CREATE TABLE login(
              ID INTEGER PRIMARY KEY AUTOINCREMENT,
              Name TEXT,
              Email TEXT,
              Password TEXT,
              Hospital TEXT
              )""")
    
    conn.commit()


class App(ctk.CTk):
    """login app class"""
    def __init__(self):
        super().__init__()
        self.title("Connect")
        
        #center the app in the screen
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (500 // 2)
        
        self.geometry(f"500x500+{x}+{y}")
        
        #read the preferences.json file
        with open ('preferences.json', "r") as f:
            data = json.load(f)
            ctk.set_appearance_mode(data["Appearance"])
            ctk.set_default_color_theme(data["ThemeColor"])

        #call the method to create the widgets
        self.login_widget()

    def login_widget(self):#main frame
        """create a login widget"""
        login_frame = ctk.CTkFrame(self)
        login_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        #label
        label = ctk.CTkLabel(login_frame,text="Log in",font = ctk.CTkFont(size = 20, weight = "bold"))
        label.pack(pady=(20,50)) 
        
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
        """this function switch to the register widget"""
        #clear the current frame and call the register method
        for widget in self.winfo_children():
            widget.destroy()
        self.register_widget()
    
    def To_login(self, event = None):
        """this function switch to the login widget"""
        #clear the current frame and call the login widget
        for widget in self.winfo_children():
            widget.destroy()
        self.login_widget()
    
    def register_widget(self):
        """create the register widget"""
        #register frame
        register_frame = ctk.CTkFrame(self)
        register_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        label = ctk.CTkLabel(register_frame,text="Register",font = ctk.CTkFont(size = 20, weight = "bold"))
        label.pack(pady=(20,50)) 
        
        entries = []
        placeholders_values = ["Full Name" , "Email" , "Password" , "Confirm Password" , "Hospital"]
        
        self.placeholders(register_frame,placeholders_values,entries)
        
        submit = ctk.CTkButton(register_frame, text="Register" , command = lambda : self.register_database(entries)) #command-------------------------------
        submit.pack(pady=(0,20))
        
        register_label = ctk.CTkLabel(register_frame, text="Already have an account? Log in now!",cursor ="hand2", text_color="#3498db",font=("Arial", 12, "bold"))
        register_label.pack(pady=(0,20))
        
        #on click event
        register_label.bind("<Button-1>", self.To_login)
        
    # create placeholders
    def placeholders(self,frame,placeholders_values,entries):
        """depending on the widget, this function create placeholders for user's input"""
        for i in placeholders_values:
            entry = ctk.CTkEntry(frame, placeholder_text= i)
            entry.pack(pady=(0, 20), padx = 15,fill="x")
            entries.append(entry)
    
    def login_database(self, entries):
        """this function match the login input from the user with the csv data to confirm login"""
        
        # get entries
        email = entries[0].get().strip()
        password = entries[1].get().strip()
        
        # check if the email and password exist in the database
        c.execute(f"SELECT * FROM login WHERE Email = '{email}' AND Password = '{password}'")
  
        

        #if exist return login successfull and open the app
        data = c.fetchall()

        if data:
            print("Login successful!")
            data = data[0]
            user = {
                "name": data[1],
            }
            with open("config.json", "w")as f:
                json.dump(user,f,indent= 4)
            
            
            self.destroy()
            
            try:
                subprocess.Popen([sys.executable, "main.py"])
            except Exception as e:
                print(f"Error launching application: {e}")
            finally:
                sys.exit(0)
            
        else:
            messagebox.showerror("Error", "Email or password incorrect!")
                
    def register_database(self,entries):
        """this function enter the data entered by the user to the sqlite file"""
        
        # get values
        name=entries[0].get()
        email = entries[1].get()
        password = entries[2].get()
        conf_password = entries[3].get()
        hospital = entries[4].get()

        #insert values in the sqlite database
        if password == conf_password:
            c.execute(f"INSERT INTO login (Name,Email,Password,Hospital) VALUES('{name}','{email}','{password}','{hospital}')")

            conn.commit()
        
        #check if the password is the same    
        else :
            messagebox.showinfo("Error","The password does not match the confirmation")
        

if __name__ == "__main__":
    app = App()
    app.mainloop()