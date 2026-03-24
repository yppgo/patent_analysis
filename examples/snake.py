import random
import tkinter as tk


CELL_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
UPDATE_MS = 120

BG_COLOR = "#111111"
SNAKE_COLOR = "#22c55e"
FOOD_COLOR = "#ef4444"
TEXT_COLOR = "#f5f5f5"


class SnakeGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("贪吃蛇")
        self.root.resizable(False, False)

        width = GRID_WIDTH * CELL_SIZE
        height = GRID_HEIGHT * CELL_SIZE

        self.score_var = tk.StringVar(value="得分: 0")
        self.status = tk.Label(
            root,
            textvariable=self.score_var,
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Consolas", 12, "bold"),
            padx=8,
            pady=6,
        )
        self.status.pack(fill="x")

        self.canvas = tk.Canvas(
            root,
            width=width,
            height=height,
            bg=BG_COLOR,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.snake = []
        self.food = (0, 0)
        self.score = 0
        self.game_over = False
        self.loop_id = None

        root.bind("<Key>", self.on_key)
        self.restart()

    def restart(self) -> None:
        if self.loop_id is not None:
            self.root.after_cancel(self.loop_id)
            self.loop_id = None

        cx, cy = GRID_WIDTH // 2, GRID_HEIGHT // 2
        self.snake = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.game_over = False
        self.food = self.spawn_food()
        self.draw()
        self.tick()

    def on_key(self, event: tk.Event) -> None:
        key = event.keysym.lower()
        if self.game_over and key in ("space", "return", "kp_enter", "r"):
            self.restart()
            return

        mapping = {
            "up": (0, -1),
            "w": (0, -1),
            "down": (0, 1),
            "s": (0, 1),
            "left": (-1, 0),
            "a": (-1, 0),
            "right": (1, 0),
            "d": (1, 0),
        }
        if key not in mapping:
            return

        nx, ny = mapping[key]
        dx, dy = self.direction
        if (nx, ny) == (-dx, -dy):
            return
        self.next_direction = (nx, ny)

    def spawn_food(self) -> tuple[int, int]:
        occupied = set(self.snake)
        while True:
            food = (random.randrange(GRID_WIDTH), random.randrange(GRID_HEIGHT))
            if food not in occupied:
                return food

    def tick(self) -> None:
        if self.game_over:
            return

        self.direction = self.next_direction
        dx, dy = self.direction
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        x, y = new_head
        hit_wall = x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT
        hit_self = new_head in self.snake
        if hit_wall or hit_self:
            self.game_over = True
            self.draw()
            self.show_game_over()
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.score_var.set(f"得分: {self.score}")
            self.food = self.spawn_food()
        else:
            self.snake.pop()

        self.draw()
        self.loop_id = self.root.after(UPDATE_MS, self.tick)

    def draw(self) -> None:
        self.canvas.delete("all")

        fx, fy = self.food
        self.draw_cell(fx, fy, FOOD_COLOR)

        for i, (x, y) in enumerate(self.snake):
            color = "#4ade80" if i == 0 else SNAKE_COLOR
            self.draw_cell(x, y, color)

    def draw_cell(self, x: int, y: int, color: str) -> None:
        x0 = x * CELL_SIZE
        y0 = y * CELL_SIZE
        x1 = x0 + CELL_SIZE
        y1 = y0 + CELL_SIZE
        self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline=BG_COLOR)

    def show_game_over(self) -> None:
        w = GRID_WIDTH * CELL_SIZE
        h = GRID_HEIGHT * CELL_SIZE
        self.canvas.create_text(
            w // 2,
            h // 2 - 20,
            text="游戏结束",
            fill=TEXT_COLOR,
            font=("Microsoft YaHei", 28, "bold"),
        )
        self.canvas.create_text(
            w // 2,
            h // 2 + 18,
            text="按 空格 / Enter / R 重开",
            fill=TEXT_COLOR,
            font=("Microsoft YaHei", 14),
        )


def main() -> None:
    root = tk.Tk()
    SnakeGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
