import tkinter as tk

from app.main_window import LyricsFormatter


def main() -> None:
    root = tk.Tk()
    LyricsFormatter(root)
    root.mainloop()


if __name__ == "__main__":
    main()
