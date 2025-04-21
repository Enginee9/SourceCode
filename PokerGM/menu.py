import tkinter as tk
from tkinter import messagebox
import pygame
from blackjack import BlackjackGame
from tutorial import BlackjackTutorial
from PokerGUI import PokerGUI
from TexasHoldemTutorial import TexasHoldemTutorial

class IntroScene:
    def __init__(self, screen):
        self.screen = screen
        # Use a thematic font if available; fallback to Arial
        self.font = pygame.font.SysFont("Arial", 28, bold=True)  # Bold for readability
        self.background_color = (20, 20, 20)  # Dark smoky background
        self.text_color = (255, 255, 255)  # White for general text
        self.man_color = (200, 200, 200)  # Light gray for Man's dialogue
        self.devil_color = (255, 50, 50)  # Red for Devil's dialogue
        self.whisper_color = (150, 150, 150)  # Gray for Whisper
        self.narration_color = (180, 180, 180)  # Slightly dim for narration
        # Flicker effect for background to simulate streetlamp
        self.flicker = [255, 200, 255, 180, 255]  # Alpha values for flicker
        self.flicker_index = 0
        self.flicker_timer = 0
        self.dialogue = [
            ("Man", "Damn it! One more round… Just one more and I could’ve won it all back!"),
            ("Whisper", "Seems like you could use some… luck?"),
            ("Narration", "(A man turns to see the Devil standing under a flickering streetlamp, his shadow stretching unnaturally long.)"),
            ("Man", "Who are you?"),
            ("Devil", "Someone who can give you what you desire… say, endless wealth?"),
            ("Narration", "(He pulls out an ancient deck of cards, its back engraved with eerie runes.)"),
            ("Devil", "Let’s play a game. Win, and I’ll give you more money than you could spend in a lifetime. Lose, and you’ll only pay… a small price."),
            ("Man", "What price?"),
            ("Devil", "Oh, nothing you’d miss. Just something you don’t… need.")
        ]
        self.current_dialogue_index = 0
        self.running = True
        self.skip = False

    def render_text(self, text, speaker, y_offset):
        """Render dialogue text with speaker label and appropriate color."""
        # Select text color based on speaker
        color = (
            self.man_color if speaker == "Man" else
            self.devil_color if speaker == "Devil" else
            self.whisper_color if speaker == "Whisper" else
            self.narration_color
        )
        if speaker and speaker != "Narration":
            speaker_text = self.font.render(f"{speaker}:", True, color)
            self.screen.blit(speaker_text, (50, y_offset))
            y_offset += 40
        # Wrap text to fit screen
        words = text.split()
        lines = []
        current_line = []
        line_width = 0
        max_width = 1100  # Max text width
        for word in words:
            word_surface = self.font.render(word, True, color)
            word_width = word_surface.get_width()
            if line_width + word_width <= max_width:
                current_line.append(word)
                line_width += word_width + self.font.size(" ")[0]
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                line_width = word_width + self.font.size(" ")[0]
        lines.append(" ".join(current_line))
        for i, line in enumerate(lines):
            line_surface = self.font.render(line, True, color)
            self.screen.blit(line_surface, (50, y_offset + i * 40))
        return y_offset + len(lines) * 40

    def run(self):
        """Run the intro scene loop."""
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    self.skip = True
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.current_dialogue_index += 1
                        if self.current_dialogue_index >= len(self.dialogue):
                            self.running = False
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                        self.skip = True

            # Update flicker effect
            self.flicker_timer += 1
            if self.flicker_timer >= 10:  # Change flicker every 10 frames
                self.flicker_index = (self.flicker_index + 1) % len(self.flicker)
                self.flicker_timer = 0

            # Draw scene
            # Apply flicker by adjusting background alpha
            self.screen.fill((20, 20, 20, self.flicker[self.flicker_index]))

            # Draw dialogue
            if self.current_dialogue_index < len(self.dialogue):
                speaker, text = self.dialogue[self.current_dialogue_index]
                self.render_text(text, speaker, 300)  # Start text lower on screen

            # Draw skip prompt
            skip_text = self.font.render("Press SPACE to continue, ESC to skip", True, (150, 150, 150))
            self.screen.blit(skip_text, (10, 760))

            pygame.display.flip()
            clock.tick(60)

        return 'skip' if self.skip else 'complete'

class MainMenu:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Devil's Gamble - Main Menu")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")

        # Main frame for centering content
        self.main_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Title
        title_label = tk.Label(
            self.main_frame,
            text="DEVIL'S GAMBLE",
            font=("Arial", 36, "bold"),
            fg="#FF4444",
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

    def start_intro(self):
        """Run the intro scene before showing the menu."""
        try:
            pygame.init()
            screen = pygame.display.set_mode((1200, 800))  # Match Blackjack resolution
            pygame.display.set_caption("Devil's Gamble - Intro")
            intro = IntroScene(screen)
            result = intro.run()
            pygame.quit()
            if result == 'skip' or result == 'complete':
                self.root.deiconify()  # Show main menu
            else:
                self.root.destroy()  # Quit if intro fails
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run intro scene: {e}")
            pygame.quit()
            self.root.deiconify()

    def start_blackjack(self):
        self.root.withdraw()
        try:
            pygame.init()
            screen = pygame.display.set_mode((1200, 800))
            game = BlackjackGame(screen)
            result = game.run()
            pygame.quit()
            if result == 'quit':
                self.root.destroy()
            else:
                self.root.deiconify()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Blackjack: {e}")
            pygame.quit()
            self.root.deiconify()

    def start_poker(self):
        self.root.withdraw()
        try:
            poker_root = tk.Toplevel()
            poker_root.geometry("1280x800")
            game = PokerGUI(poker_root)
            poker_root.protocol("WM_DELETE_WINDOW", lambda: self.on_poker_close(poker_root))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Texas Hold'em: {e}")
            self.root.deiconify()

    def start_blackjack_tutorial(self):
        self.root.withdraw()
        try:
            pygame.init()
            screen = pygame.display.set_mode((1200, 800))
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
        try:
            poker_root.destroy()
        except tk.TclError:
            pass
        self.root.deiconify()

    def quit_game(self):
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.root.destroy()

    def run(self):
        self.root.withdraw()  # Hide menu initially
        self.start_intro()  # Run intro scene first
        self.root.mainloop()

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
