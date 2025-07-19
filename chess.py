import tkinter as tk
from tkinter import Toplevel, Label, Button, PhotoImage
import platform
import winsound
import copy

BOARD_SIZE = 8
CELL_SIZE = 80
KING_COST = 10
BOAT_COST = 20
KILL_REWARD = 100
LOSS_PENALTY = 100
STARTING_POINTS = 1000

class Piece:
    def __init__(self, name, position):
        self.name = name
        self.position = position

class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Chess Game - King & Boat vs System King")
        self.root.configure(bg="#e3f2fd")

        # Load images
        self.uk_img = PhotoImage(file="user_king.png")
        self.sk_img = PhotoImage(file="system_king.png")
        self.ub_img = PhotoImage(file="boat.png")

        self.main_frame = tk.Frame(root, bg="#e3f2fd")
        self.main_frame.pack(padx=20, pady=20)

        self.canvas = tk.Canvas(self.main_frame, width=BOARD_SIZE * CELL_SIZE, height=BOARD_SIZE * CELL_SIZE, bg="white", highlightthickness=1, highlightbackground="#999")
        self.canvas.grid(row=0, column=0, rowspan=20, padx=(0, 20))

        self.right_frame = tk.Frame(self.main_frame, bg="#e3f2fd")
        self.right_frame.grid(row=0, column=1, sticky="nw")

        self.status_label = tk.Label(self.right_frame, text="", font=("Arial", 16, "bold"), fg="#1e3a8a", bg="#e3f2fd", anchor="w")
        self.status_label.pack(anchor="w", pady=(0, 10))

        self.turn_label = tk.Label(self.right_frame, text="Your Turn", font=("Arial", 14, "italic"), fg="#1e40af", bg="#e3f2fd", anchor="w")
        self.turn_label.pack(anchor="w", pady=5)

        self.history_title = tk.Label(self.right_frame, text="Move History", font=("Arial", 14, "underline"), fg="#1f2937", bg="#e3f2fd")
        self.history_title.pack(anchor="w")

        self.history_label = tk.Label(self.right_frame, text="", font=("Courier", 12), justify="left", bg="#f0f9ff", bd=2, relief="groove", width=35, height=10, anchor="nw")
        self.history_label.pack(anchor="w", pady=(0, 15))

        self.buttons_frame = tk.Frame(self.right_frame, bg="#e3f2fd")
        self.buttons_frame.pack(anchor="w")

        self.undo_button = tk.Button(self.buttons_frame, text="Undo Move", font=("Arial", 12), command=self.undo_move, bg="#facc15", fg="black", width=15)
        self.undo_button.pack(side="left", padx=(0, 10))

        self.restart_button = tk.Button(self.buttons_frame, text="Restart Game", font=("Arial", 12), command=self.restart_game, bg="#38bdf8", fg="white", width=15)
        self.restart_button.pack(side="left")

        self.canvas.bind("<Button-1>", self.on_click)
        self.restart_game()

    def undo_move(self):
        if self.move_snapshots:
            state = self.move_snapshots.pop()
            self.uk = state["uk"]
            self.ub = state["ub"]
            self.sk = state["sk"]
            self.points = state["points"]
            self.move_history = state["history"]
            self.update_status()
            self.draw_board()
            self.draw_pieces()

    def on_click(self, event):
        col, row = event.x // CELL_SIZE, event.y // CELL_SIZE
        pos = (row, col)
        if self.selected_piece:
            if self.valid_move(self.selected_piece, pos):
                self.save_snapshot()
                self.move_piece(self.selected_piece, pos)
            self.selected_piece = None
        else:
            if self.uk.position == pos:
                self.selected_piece = self.uk
            elif self.ub.position == pos:
                self.selected_piece = self.ub
        self.draw_board()
        self.draw_pieces()

    def restart_game(self):
        self.points = STARTING_POINTS
        self.selected_piece = None
        self.move_history = []
        self.move_snapshots = []
        self.uk = Piece("uk", (7, 4))
        self.ub = Piece("ub", (7, 0))
        self.sk = Piece("sk", (0, 4))
        self.update_status()
        self.draw_board()
        self.draw_pieces()

    def update_status(self):
        self.status_label.config(
            text=f"Points: {self.points} | User King: {self.uk.position} | System King: {self.sk.position}"
        )
        self.history_label.config(text="\n".join(self.move_history[-10:]))

    def draw_board(self):
        self.canvas.delete("square")
        for i in range(BOARD_SIZE):
            for j in range(BOARD_SIZE):
                color = "#dbe9f4" if (i + j) % 2 == 0 else "#9bbad8"
                self.canvas.create_rectangle(j * CELL_SIZE, i * CELL_SIZE,
                                             (j + 1) * CELL_SIZE, (i + 1) * CELL_SIZE,
                                             fill=color, tags="square")
        self.highlight_killable_zones()

    def draw_pieces(self):
        self.canvas.delete("piece")
        for piece, img in zip([self.uk, self.ub, self.sk], [self.uk_img, self.ub_img, self.sk_img]):
            if piece.position != (-1, -1):
                r, c = piece.position
                self.canvas.create_image(c * CELL_SIZE + 40, r * CELL_SIZE + 40, image=img, tags="piece")

        if self.selected_piece and self.selected_piece.position != (-1, -1):
            r, c = self.selected_piece.position
            self.canvas.create_rectangle(c * CELL_SIZE + 5, r * CELL_SIZE + 5,
                                         (c + 1) * CELL_SIZE - 5, (r + 1) * CELL_SIZE - 5,
                                         outline="gold", width=3, tags="piece")

    def highlight_killable_zones(self):
        if self.uk.position != (-1, -1):
            r, c = self.uk.position
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0: continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        self.canvas.create_rectangle(nc * CELL_SIZE, nr * CELL_SIZE,
                                                     (nc + 1) * CELL_SIZE, (nr + 1) * CELL_SIZE,
                                                     outline="red", width=2)

    def valid_move(self, piece, target):
        r1, c1 = piece.position
        r2, c2 = target
        if target in [self.uk.position, self.ub.position]:
            return False
        if piece.name == "uk":
            return abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1 and (r1 != r2 or c1 != c2)
        elif piece.name == "ub":
            if r1 == r2:
                step = 1 if c2 > c1 else -1
                for c in range(c1 + step, c2, step):
                    if (r1, c) in [self.uk.position, self.sk.position]:
                        return False
                return True
            elif c1 == c2:
                step = 1 if r2 > r1 else -1
                for r in range(r1 + step, r2, step):
                    if (r, c1) in [self.uk.position, self.sk.position]:
                        return False
                return True
        return False

    def save_snapshot(self):
        snapshot = {
            "uk": copy.deepcopy(self.uk),
            "ub": copy.deepcopy(self.ub),
            "sk": copy.deepcopy(self.sk),
            "points": self.points,
            "history": list(self.move_history)
        }
        self.move_snapshots.append(snapshot)

    def move_piece(self, piece, target):
        start = piece.position
        if piece.name == "uk":
            self.points -= KING_COST
        elif piece.name == "ub":
            self.points -= BOAT_COST

        if target == self.sk.position:
            self.points += KILL_REWARD
            self.sk.position = (-1, -1)
            self.move_history.append(f"{piece.name.upper()} captured SK at {target}")
            self.update_status()
            self.draw_board()
            self.draw_pieces()
            self.show_end_screen("Victory! You killed the system king.")
            return

        piece.position = target
        self.move_history.append(f"{piece.name.upper()} moved from {start} to {target}")
        self.draw_board()
        self.draw_pieces()
        self.update_status()
        self.turn_label.config(text="System Turn")
        if self.sk.position != (-1, -1):
            self.root.after(500, self.system_move)

    def system_move(self):
        def evaluate_state(sk_pos):
            if sk_pos == self.uk.position:
                return 1000
            if sk_pos == self.ub.position:
                return -500
            distance_uk = abs(sk_pos[0] - self.uk.position[0]) + abs(sk_pos[1] - self.uk.position[1])
            distance_ub = abs(sk_pos[0] - self.ub.position[0]) + abs(sk_pos[1] - self.ub.position[1])
            return - (distance_uk + 0.5 * distance_ub)

        def minimax(position, depth, alpha, beta, maximizing):
            if depth == 0 or position == self.uk.position:
                return evaluate_state(position)
            directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            if maximizing:
                max_eval = -float('inf')
                for dr, dc in directions:
                    nr, nc = position[0] + dr, position[1] + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) != self.ub.position:
                        eval = minimax((nr, nc), depth - 1, alpha, beta, False)
                        max_eval = max(max_eval, eval)
                        alpha = max(alpha, eval)
                        if beta <= alpha:
                            break
                return max_eval
            else:
                min_eval = float('inf')
                for dr, dc in directions:
                    nr, nc = position[0] + dr, position[1] + dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) != self.ub.position:
                        eval = minimax((nr, nc), depth - 1, alpha, beta, True)
                        min_eval = min(min_eval, eval)
                        beta = min(beta, eval)
                        if beta <= alpha:
                            break
                return min_eval

        directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for dr, dc in directions:
            nr, nc = self.sk.position[0] + dr, self.sk.position[1] + dc
            if (nr, nc) == self.uk.position:
                self.sk.position = (nr, nc)
                self.move_history.append(f"SK moved to {self.sk.position} and killed UK")
                self.points -= LOSS_PENALTY
                self.uk.position = (-1, -1)
                self.update_status()
                self.draw_board()
                self.draw_pieces()
                self.turn_label.config(text="System Turn")
                self.show_end_screen("Game Over! System king killed your king.")
                return

        best_score = -float('inf')
        best_move = self.sk.position

        for dr, dc in directions:
            nr, nc = self.sk.position[0] + dr, self.sk.position[1] + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) != self.ub.position:
                score = minimax((nr, nc), 3, -float('inf'), float('inf'), True)
                if score > best_score:
                    best_score = score
                    best_move = (nr, nc)

        self.sk.position = best_move
        self.move_history.append(f"SK moved to {self.sk.position}")
        self.update_status()
        self.draw_board()
        self.draw_pieces()
        self.turn_label.config(text="Your Turn")

    def show_end_screen(self, message):
        end_win = Toplevel(self.root)
        end_win.title("Game Result")
        end_win.geometry("320x200")
        end_win.configure(bg="#fefefe")
        Label(end_win, text=message, font=("Arial", 16, "bold"), bg="#fefefe", fg="#222").pack(pady=20)
        Button(end_win, text="Restart Game", font=("Arial", 12), bg="#10b981", fg="white", padx=10, pady=5, command=lambda: [end_win.destroy(), self.restart_game()]).pack(pady=5)
        Button(end_win, text="Exit", font=("Arial", 12), bg="#ef4444", fg="white", padx=10, pady=5, command=self.root.quit).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    game = Game(root)
    root.mainloop()