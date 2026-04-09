import customtkinter as ctk
from tkinter import messagebox
import json
import subprocess
import sys
import sqlite3
import os

BASE_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
DATABASE_DIR = os.path.join(BASE_DIR, "login_mails")
DATABASE_PATH = os.path.join(DATABASE_DIR, "database.db")
PREFERENCES_PATH = os.path.join(PROJECT_ROOT, "preferences.json")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "config.json")
MAIN_SCRIPT = os.path.join(BASE_DIR, "main.py")

# create empty sqlite database
os.makedirs(DATABASE_DIR, exist_ok=True)
conn = sqlite3.connect(DATABASE_PATH)
conn.row_factory = sqlite3.Row
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
              Hospital TEXT,
              WalletAddress TEXT,
              BlockchainRegistered INTEGER DEFAULT 0
              )""")
    
    conn.commit()


def get_table_columns(table_name):
    c.execute(f"PRAGMA table_info({table_name})")
    return {row["name"] for row in c.fetchall()}


def ensure_login_schema():
    """Migrate the login table so each doctor can be linked to a blockchain wallet."""
    columns = get_table_columns("login")

    if "WalletAddress" not in columns:
        c.execute("ALTER TABLE login ADD COLUMN WalletAddress TEXT")

    if "BlockchainRegistered" not in columns:
        c.execute("ALTER TABLE login ADD COLUMN BlockchainRegistered INTEGER DEFAULT 0")

    conn.commit()


def get_registered_wallets(exclude_email=None):
    """Return wallet addresses already assigned to doctors in SQLite."""
    if exclude_email:
        c.execute(
            "SELECT WalletAddress FROM login WHERE WalletAddress IS NOT NULL AND WalletAddress != '' AND Email != ?",
            (exclude_email,),
        )
    else:
        c.execute("SELECT WalletAddress FROM login WHERE WalletAddress IS NOT NULL AND WalletAddress != ''")

    return [row["WalletAddress"] for row in c.fetchall()]


def ensure_blockchain_identity(name, email, hospital, preferred_wallet=None):
    """Assign a doctor wallet and ensure the doctor is registered on-chain."""
    try:
        from blockchain import provision_doctor_identity

        return provision_doctor_identity(
            doctor_name=name,
            doctor_email=email,
            doctor_hospital=hospital,
            preferred_wallet=preferred_wallet,
            used_wallets=get_registered_wallets(exclude_email=email),
        )
    except Exception as exc:
        return {
            "success": False,
            "error": f"Blockchain identity setup failed: {exc}",
            "wallet_address": preferred_wallet,
        }


ensure_login_schema()


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
        with open(PREFERENCES_PATH, "r", encoding="utf-8") as f:
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
            entry = ctk.CTkEntry(frame, placeholder_text=i, show="*" if "Password" in i or i == "password" else "")
            entry.pack(pady=(0, 20), padx = 15,fill="x")
            entries.append(entry)
    
    def login_database(self, entries):
        """this function match the login input from the user with the csv data to confirm login"""
        
        # get entries
        email = entries[0].get().strip()
        password = entries[1].get().strip()

        if not email or not password:
            messagebox.showerror("Error", "Please enter both email and password.")
            return
        
        # check if the email and password exist in the database
        c.execute("SELECT * FROM login WHERE Email = ? AND Password = ?", (email, password))
  
        

        #if exist return login successfull and open the app
        data = c.fetchone()

        if data:
            wallet_address = data["WalletAddress"]
            blockchain_registered = bool(data["BlockchainRegistered"])

            if not wallet_address or not blockchain_registered:
                identity_result = ensure_blockchain_identity(
                    name=data["Name"],
                    email=data["Email"],
                    hospital=data["Hospital"],
                    preferred_wallet=wallet_address,
                )
                if not identity_result["success"]:
                    messagebox.showerror("Blockchain Error", identity_result["error"])
                    return

                wallet_address = identity_result["wallet_address"]
                blockchain_registered = True
                c.execute(
                    "UPDATE login SET WalletAddress = ?, BlockchainRegistered = ? WHERE Email = ?",
                    (wallet_address, 1, email),
                )
                conn.commit()

            print("Login successful!")
            user = {
                "name": data["Name"],
                "email": data["Email"],
                "hospital": data["Hospital"],
                "wallet_address": wallet_address,
                "blockchain_registered": blockchain_registered,
            }
            with open(CONFIG_PATH, "w", encoding="utf-8")as f:
                json.dump(user,f,indent= 4)
            
            
            self.destroy()
            
            try:
                subprocess.Popen([sys.executable, MAIN_SCRIPT], cwd=BASE_DIR)
            except Exception as e:
                print(f"Error launching application: {e}")
            finally:
                sys.exit(0)
            
        else:
            messagebox.showerror("Error", "Email or password incorrect!")
                
    def register_database(self,entries):
        """this function enter the data entered by the user to the sqlite file"""
        
        # get values
        name=entries[0].get().strip()
        email = entries[1].get().strip()
        password = entries[2].get()
        conf_password = entries[3].get()
        hospital = entries[4].get().strip()

        if not all([name, email, password, conf_password, hospital]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        #insert values in the sqlite database
        if password == conf_password:
            c.execute("SELECT 1 FROM login WHERE Email = ?", (email,))
            if c.fetchone():
                messagebox.showerror("Error", "An account with this email already exists.")
                return

            identity_result = ensure_blockchain_identity(
                name=name,
                email=email,
                hospital=hospital,
            )
            if not identity_result["success"]:
                messagebox.showerror("Blockchain Error", identity_result["error"])
                return

            c.execute(
                "INSERT INTO login (Name,Email,Password,Hospital,WalletAddress,BlockchainRegistered) VALUES(?, ?, ?, ?, ?, ?)",
                (
                    name,
                    email,
                    password,
                    hospital,
                    identity_result["wallet_address"],
                    1,
                ),
            )

            conn.commit()
            messagebox.showinfo("Success", "Registration completed. You can log in now.")
            self.To_login()
        
        #check if the password is the same    
        else :
            messagebox.showerror("Error","The password does not match the confirmation")
        

if __name__ == "__main__":
    app = App()
    app.mainloop()
