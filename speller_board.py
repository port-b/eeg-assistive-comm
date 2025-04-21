import tkinter as tk
import threading
from tkinter import messagebox
import time

# Define your speller grid
GRID = [
    ['A', 'B', 'C', 'D', 'E', 'F'],
    ['G', 'H', 'I', 'J', 'K', 'L'],
    ['M', 'N', 'O', 'P', 'Q', 'R'],
    ['S', 'T', 'U', 'V', 'W', 'X'],
    ['Y', 'Z', '0', '1', '2', '3'],
    ['4', '5', '6', '7', '8', '9'],
    ['SPACE', 'BKSP', 'CMD1', 'CMD2', 'CMD3', 'ENTER']
]


class SpellerBoardUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EEG-Based Speller Board")

        self.buttons = []
        for r, row in enumerate(GRID):
            row_buttons = []
            for c, char in enumerate(row):
                btn = tk.Button(root, text=char, width=10, height=3)
                btn.grid(row=r, column=c, padx=2, pady=2)
                row_buttons.append(btn)
            self.buttons.append(row_buttons)

        self.selected_row = None
        self.selected_col = None
        self.current_highlight = -1  # <-- Fix: Start at -1 so first highlight is 0
        self.highlight_mode = 'row'  # alternate between 'row' and 'col'
        self.running = True
        self.output_text = ""

        self.output_label = tk.Label(root, text="Output: ", font=("Arial", 16))
        self.output_label.grid(row=len(GRID), column=0, columnspan=6, pady=10)

        threading.Thread(target=self.highlight_loop, daemon=True).start()

    def highlight_loop(self):
        while self.running:
            self.clear_highlights()
            if self.highlight_mode == 'row':
                for col in range(len(GRID[0])):
                    self.buttons[self.current_highlight][col].config(
                        bg='yellow')
            else:
                # Keep selected row highlighted
                for col in range(len(GRID[0])):
                    self.buttons[self.selected_row][col].config(
                        bg='lightgreen')
                # Flash column in that row
                self.buttons[self.selected_row][self.current_highlight].config(
                    bg='cyan')

            time.sleep(1)  # Interval between highlights

            self.current_highlight = (self.current_highlight + 1) % (
                len(GRID) if self.highlight_mode == 'row' else len(GRID[0])
            )

    def on_blink_detected(self):
        if self.highlight_mode == 'row':
            self.selected_row = self.current_highlight
            self.highlight_mode = 'col'
        else:
            self.selected_col = self.current_highlight
            self.select_character()
            self.highlight_mode = 'row'
        self.current_highlight = -1  # <-- Fix: Reset to -1 before new round

    def select_character(self):
        char = GRID[self.selected_row][self.selected_col]
        if char == 'SPACE':
            self.output_text += ' '
        elif char == 'BKSP':
            self.output_text = self.output_text[:-1]
        elif char == 'ENTER':
            messagebox.showinfo("Entered Text", self.output_text)
            self.output_text = ''
        else:
            self.output_text += char
        self.output_label.config(text=f"Output: {self.output_text}")

    def clear_highlights(self):
        for r, row in enumerate(self.buttons):
            for c, btn in enumerate(row):
                # Keep row highlighted when in 'col' mode
                if self.highlight_mode == 'col' and r == self.selected_row:
                    btn.config(bg='lightgreen')
                else:
                    btn.config(bg='SystemButtonFace')
