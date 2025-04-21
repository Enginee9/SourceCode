import tkinter as tk
from tkinter import messagebox
import pygame
from blackjack import BlackjackGame
from tutorial import BlackjackTutorial
from PokerGUI import PokerGUI
from TexasHoldemTutorial import TexasHoldemTutorial

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Devil's Gamble - Main Menu")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")  # Dark background for theme

        # Main frame for centering content
        self.main_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Title
        title_label = tk.Label(
            self.main_frame,
            text="DEVIL'S GAMBLE",
            font=("Arial", 36, "bold"),
            fg="#FF4444",  # Red for Devil theme
            bg="#1a1a1a"
        )
        title_label.pack(pady=(20, 40))

        # Subtitle
        subtitle_label = tk.Label(
            self.main_frame,
            text="Do you dare to play?",
            font=("Arial", 16, "italic"),
            fg="white",
            bg="#1a1a1a"
        )
        subtitle_label.pack(pady=(0, 30))

        # Button frame for alignment
        button_frame = tk.Frame(self.main_frame, bg="#1a1a1a")
        button_frame.pack()

        # Buttons for game selection
        button_style = {
            "font": ("Arial", 14),
            "bg": "#4a4a4a",
            "fg": "white",
            "activebackground": "#FF4444",
            "activeforeground": "white",
            "width": 20,
            "height": 2,
            "relief": "raised"
        }

        tk.Button(
            button_frame,
            text="Blackjack",
            command=self.start_blackjack,
            **button_style
        ).pack(pady=10)

        tk.Button(
            button_frame,
            text="Texas Hold'em",
            command=self.start_poker,
            **button_style
        ).pack(pady=10)

        tk.Button(
            button_frame,
            text="Blackjack Tutorial",
            command=self.start_blackjack_tutorial,
            **button_style
        ).pack(pady=10)

        tk.Button(
            button_frame,
            text="Texas Hold'em Tutorial",
            command=self.start_texas_tutorial,
            **button_style
        ).pack(pady=10)

        # Exit button
        tk.Button(
            button_frame,
            text="Exit",
            command=self.quit_game,
            font=("Arial", 14),
            bg="#4a4a4a",
            fg="white",
            activebackground="#FF4444",
            activeforeground="white",
            width=20,
            height=2,
            relief="raised"
        ).pack(pady=(30, 10))

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.quit_game)

    def start_blackjack(self):
        """Start the Blackjack game (Pygame-based)."""
        self.root.withdraw()  # Hide menu
        try:
            pygame.init()
            screen = pygame.display.set_mode((800, 600))
            game = BlackjackGame(screen)
            result = game.run()
            pygame.quit()
            if result == 'quit':
                self.root.destroy()
            else:
                self.root.deiconify()  # Show menu again
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Blackjack: {e}")
            pygame.quit()
            self.root.deiconify()

    def start_poker(self):
        """Start the Texas Hold'em game (Tkinter-based)."""
        self.root.withdraw()  # Hide menu
        try:
            poker_root = tk.Toplevel()  # Create new window for PokerGUI
            poker_root.geometry("1280x800")
            game = PokerGUI(poker_root)
            poker_root.protocol("WM_DELETE_WINDOW", lambda: self.on_poker_close(poker_root))
            # Note: PokerGUI runs its own mainloop via root.mainloop()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Texas Hold'em: {e}")
            self.root.deiconify()

    def start_blackjack_tutorial(self):
        """Start the Blackjack tutorial (Pygame-based)."""
        self.root.withdraw()
        try:
            pygame.init()
            screen = pygame.display.set_mode((800, 600))
            tutorial = BlackjackTutorial(screen)
            result = tutorial.run()
            pygame.quit()
            if result == 'quit':
                self.root.destroy()
            else:
                self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Blackjack Tutorial: {e}")
            pygame.quit()
            self.root.deiconify()

    def start_texas_tutorial(self):
        """Start the Texas Hold'em tutorial (Pygame-based)."""
        self.root.withdraw()
        try:
            pygame.init()
            screen = pygame.display.set_mode((1200, 800))
            tutorial = TexasHoldemTutorial(screen)
            result = tutorial.run()
            pygame.quit()
            if result == 'quit':
                self.root.destroy()
            else:
                self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Texas Hold'em Tutorial: {e}")
            pygame.quit()
            self.root.deiconify()

    def on_poker_close(self, poker_root):
        """Handle PokerGUI window close."""
        try:
            poker_root.destroy()
        except tk.TclError:
            pass
        self.root.deiconify()  # Show menu again

    def quit_game(self):
        """Handle quit request."""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
