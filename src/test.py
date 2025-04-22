import tkinter as tk
import math
import threading
import time

class GradientLoader:
    def __init__(self, parent, size=100, thickness=8, speed=2):
        self.canvas = tk.Canvas(parent, width=size, height=size, bg='white', highlightthickness=0)
        self.size = size
        self.thickness = thickness
        self.speed = speed
        self.angle = 0
        self.center = size // 2
        self.radius = (size // 2) - thickness
        
        # Create the arc
        self.arc = self.canvas.create_arc(
            thickness, thickness,
            size-thickness, size-thickness,
            start=0,
            extent=0,
            style=tk.ARC,
            outline='',
            width=thickness
        )
        
        # Animation colors (gradient from blue to purple)
        self.colors = [
            '#4285F4', '#5A6DF3', '#7256F2', 
            '#8A40F1', '#A229F0', '#BB13EF'
        ]
        self.animate()

    def animate(self):
        """Update the gradient loading animation"""
        self.angle = (self.angle + self.speed) % 360
        
        # Calculate gradient segments
        segments = len(self.colors)
        for i, color in enumerate(self.colors):
            start_angle = (self.angle + i * (360/segments)) % 360
            extent = 360/segments
            
            # Create temporary arc for each segment
            self.canvas.itemconfig(
                self.arc,
                start=start_angle,
                extent=extent,
                outline=color
            )
            self.canvas.update()
        
        self.canvas.after(20, self.animate)

    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

def long_operation(callback):
    """Simulate a background task"""
    time.sleep(3)  # Simulate work
    callback()

class LoadingWindow:
    def __init__(self, root):
        self.top = tk.Toplevel(root)
        self.top.title("Loading")
        self.top.geometry("300x200")
        self.top.resizable(False, False)
        
        # Make it modal
        self.top.grab_set()
        
        # Loading text
        tk.Label(self.top, text="Processing...", font=('Arial', 12)).pack(pady=20)
        
        # Gradient loader
        self.loader = GradientLoader(self.top, size=120, thickness=12)
        self.loader.pack()
        
        # Cancel button (optional)
        self.cancelled = False
        tk.Button(
            self.top, 
            text="Cancel", 
            command=self.cancel,
            width=10
        ).pack(pady=10)
    
    def cancel(self):
        self.cancelled = True
        self.top.destroy()

def start_task(root):
    """Show loading window and start background task"""
    loader = LoadingWindow(root)
    
    def task_completed():
        if not loader.cancelled:
            loader.top.destroy()
            status_label.config(text="Task completed!")
    
    # Start background task
    threading.Thread(
        target=long_operation,
        args=(task_completed,),
        daemon=True
    ).start()

# Main application
root = tk.Tk()
root.title("Gradient Loader Demo")
root.geometry("400x300")

# Status label
status_label = tk.Label(root, text="Ready to start task", font=('Arial', 12))
status_label.pack(pady=40)

# Start button
start_btn = tk.Button(
    root,
    text="Start Task",
    command=lambda: start_task(root),
    font=('Arial', 12),
    width=15
)
start_btn.pack()

root.mainloop()