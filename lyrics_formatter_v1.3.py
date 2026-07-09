import re
import sys
import json
import os
import tkinter as tk
import webbrowser
from tkinter import filedialog

from tkinter import (
    filedialog,
    messagebox
)

TIME_PATTERN = re.compile(
    r'\[(?:\d+\|)?\d{2}:\d{2}:\d{2}\]'
)

TIME_CAPTURE = re.compile(
    r'\[(?:\d+\|)?(\d{2}):(\d{2}):(\d{2})\]'
)

SETTINGS_FILE = "settings.json"

DEFAULT_THRESHOLD = "00:02:10"
DEFAULT_LINE_COUNT = "2"
DEFAULT_GEOMETRY = "1400x900"


class LyricsFormatter:

    def __init__(self, root):

        self.root = root
        self.root.title(
            "歌詞改行ツール v1.3"
        )

        (
            threshold,
            line_count,
            geometry
        ) = self.load_settings()

        self.root.geometry(
            geometry
        )

        self.threshold_var = tk.StringVar(
            value=threshold
        )

        self.line_count_var = tk.StringVar(
            value=line_count
        )

        self.areas = []

        self.build_ui()

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

    def get_app_dir(self):

        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)

        return os.path.dirname(
            os.path.abspath(__file__)
        )

    def load_settings(self):

        if os.path.exists(
            SETTINGS_FILE
        ):

            try:

                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                return (
                    data.get(
                        "threshold",
                        DEFAULT_THRESHOLD
                    ),
                    data.get(
                        "line_count",
                        DEFAULT_LINE_COUNT
                    ),
                    data.get(
                        "window_geometry",
                        DEFAULT_GEOMETRY
                    )
                )

            except Exception:
                pass

        return (
            DEFAULT_THRESHOLD,
            DEFAULT_LINE_COUNT,
            DEFAULT_GEOMETRY
        )

    def save_settings(self):

        data = {
            "threshold":
                self.threshold_var.get(),

            "line_count":
                self.line_count_var.get(),

            "window_geometry":
                self.root.geometry()
        }

        with open(
            SETTINGS_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )

    def reset_settings(self):

        self.threshold_var.set(
            DEFAULT_THRESHOLD
        )

        self.line_count_var.set(
            DEFAULT_LINE_COUNT
        )

        self.save_settings()

    def on_close(self):

        self.save_settings()

        self.root.destroy()

    def create_menu(self):

        menubar = tk.Menu(self.root)

        #
        # ファイル
        #

        file_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        file_menu.add_command(
            label="開く...",
            accelerator="Ctrl+O",
            command=self.open_file
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="名前を付けて保存...",
            accelerator="Ctrl+S",
            command=self.save_output
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="終了",
            accelerator="Alt+F4",
            command=self.on_close
        )

        menubar.add_cascade(
            label="ファイル",
            menu=file_menu
        )

        #
        # 編集
        #

        edit_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        edit_menu.add_command(
            label="元に戻す",
            accelerator="Ctrl+Z",
            command=self.undo
        )

        edit_menu.add_command(
            label="やり直す",
            accelerator="Ctrl+Y",
            command=self.redo
        )

        edit_menu.add_separator()

        edit_menu.add_command(
            label="クリア",
            command=self.clear_all
        )

        menubar.add_cascade(
            label="編集",
            menu=edit_menu
        )

        #
        # ツール
        #

        tool_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        tool_menu.add_command(
            label="自動整形",
            accelerator="Ctrl+D",
            command=self.auto_format
        )

        tool_menu.add_separator()

        tool_menu.add_command(
            label="手動空行挿入",
            accelerator="Ctrl+Enter",
            command=self.insert_blank_line
        )

        tool_menu.add_command(
            label="手動空行削除",
            command=self.remove_blank_line
        )

        tool_menu.add_command(
            label="全空行削除",
            command=self.remove_all_blank_lines
        )

        menubar.add_cascade(
            label="ツール",
            menu=tool_menu
        )

        #
        # ヘルプ
        #

        help_menu = tk.Menu(
            menubar,
            tearoff=0
        )

        help_menu.add_command(
            label="Read Me",
            command=self.open_readme
        )

        help_menu.add_separator()

        help_menu.add_command(
            label="バージョン情報",
            command=self.show_about
        )

        menubar.add_cascade(
            label="ヘルプ",
            menu=help_menu
        )

        self.root.config(
            menu=menubar
        )
    
    def build_ui(self):

        self.create_menu()
        
        self.root.grid_rowconfigure(
            1,
            weight=1
        )

        self.root.grid_rowconfigure(
            3,
            weight=1
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        #
        # 上部設定
        #

        top = tk.Frame(
            self.root
        )

        top.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=5,
            pady=5
        )

        tk.Label(
            top,
            text="時間差閾値"
        ).pack(
            side="left"
        )

        tk.Entry(
            top,
            textvariable=self.threshold_var,
            width=10
        ).pack(
            side="left",
            padx=5
        )

        tk.Label(
            top,
            text="(mm:ss:SS)"
        ).pack(
            side="left"
        )

        tk.Label(
            top,
            text="   改行間隔"
        ).pack(
            side="left",
            padx=(15, 0)
        )

        tk.OptionMenu(
            top,
            self.line_count_var,
            "2",
            "3",
            "4"
        ).pack(
            side="left"
        )

        tk.Label(
            top,
            text="行"
        ).pack(
            side="left"
        )

        tk.Button(
            top,
            text="デフォルトに戻す",
            command=self.reset_settings
        ).pack(
            side="left",
            padx=10
        )

        #
        # 入力エリア
        #

        input_area = tk.Frame(
            self.root
        )

        input_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=5
        )

        input_area.grid_rowconfigure(
            1,
            weight=1
        )

        input_area.grid_columnconfigure(
            0,
            weight=1
        )

        tk.Label(
            input_area,
            text="入力"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.input_text = self.create_text_area(
            input_area
        )

        self.input_text.outer_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        #
        # 中央ボタン
        #

        btn = tk.Frame(
            self.root
        )

        btn.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=5
        )

        # ← ボタン群
        tk.Button(btn, text="自動整形",
                command=self.auto_format).pack(side="left", padx=2)

        tk.Button(btn, text="手動空行挿入",
                command=self.insert_blank_line).pack(side="left", padx=2)

        tk.Button(btn, text="手動空行削除",
                command=self.remove_blank_line).pack(side="left", padx=2)

        tk.Button(btn, text="全空行削除",
                command=self.remove_all_blank_lines).pack(side="left", padx=2)

        # ★余白（これがポイント）
        tk.Frame(btn).pack(side="left", expand=True, fill="x")

        # →右寄せボタン
        tk.Button(
            btn,
            text="クリア",
            command=self.clear_all
        ).pack(side="right", padx=2)

        #
        # 出力エリア
        #

        output_area = tk.Frame(
            self.root
        )

        output_area.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=5
        )

        output_area.grid_rowconfigure(
            1,
            weight=1
        )

        output_area.grid_columnconfigure(
            0,
            weight=1
        )

        tk.Label(
            output_area,
            text="出力"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        self.output_text = self.create_text_area(
            output_area
        )

        self.output_text.outer_frame.grid(
            row=1,
            column=0,
            sticky="nsew"
        )

        #
        # 下部ボタン
        #

        bottom = tk.Frame(
            self.root
        )

        bottom.grid(
            row=4,
            column=0,
            sticky="ew",
            pady=5
        )

        tk.Button(
            bottom,
            text="コピー",
            command=self.copy_output
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            bottom,
            text="保存",
            command=self.save_output
        ).pack(
            side="left",
            padx=2
        )

        self.root.bind(
            "<Control-Return>",
            self.insert_blank_line
        )

        self.root.bind(
            "<Control-s>",
            self.save_output
        )
        
        self.root.bind(
            "<Control-z>",
            self.undo
        )

        self.root.bind(
            "<Control-y>",
            self.redo
        )
        
        self.root.bind(
            "<Control-d>",
            self.auto_format_shortcut
        )
        
        self.root.bind(
            "<Control-o>",
            self.open_file
        )

    def auto_format_shortcut(self, event=None):

        self.auto_format()

        return "break"

    def create_text_area(self, parent):

        outer = tk.Frame(parent)

        outer.grid_rowconfigure(
            0,
            weight=1
        )

        outer.grid_columnconfigure(
            1,
            weight=1
        )

        line_numbers = tk.Text(
            outer,
            width=6,
            state="disabled",
            bg="#e8e8e8",
            wrap="none",
            takefocus=0
        )

        text = tk.Text(
            outer,
            wrap="none",
            undo=True,
            bg="#fcfcfc"
        )

        y_scroll = tk.Scrollbar(
            outer,
            orient="vertical"
        )

        x_scroll = tk.Scrollbar(
            outer,
            orient="horizontal"
        )

        line_numbers.grid(
            row=0,
            column=0,
            sticky="ns"
        )

        text.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        y_scroll.grid(
            row=0,
            column=2,
            sticky="ns"
        )

        x_scroll.grid(
            row=1,
            column=1,
            sticky="ew"
        )

        text.configure(
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )

        y_scroll.configure(
            command=text.yview
        )

        x_scroll.configure(
            command=text.xview
        )

        text.tag_config(
            "time_tag",
            foreground="blue"
        )

        text.tag_config(
            "blank_line",
            background="#fff2a8"
        )

        text.bind(
            "<KeyRelease>",
            lambda e:
            self.refresh_visuals(
                text,
                line_numbers
            )
        )

        text.bind(
            "<ButtonRelease>",
            lambda e:
            self.refresh_visuals(
                text,
                line_numbers
            )
        )

        self.areas.append(
            (
                text,
                line_numbers
            )
        )

        text.outer_frame = outer

        return text
    
    def undo(self, event=None):

        widget = self.root.focus_get()

        if isinstance(widget, tk.Text):

            try:
                widget.edit_undo()

                if widget == self.input_text:
                    self.refresh_visuals(
                        self.input_text,
                        self.areas[0][1]
                    )
                elif widget == self.output_text:
                    self.refresh_visuals(
                        self.output_text,
                        self.areas[1][1]
                    )

            except tk.TclError:
                pass

        return "break"


    def redo(self, event=None):

        widget = self.root.focus_get()

        if isinstance(widget, tk.Text):

            try:
                widget.edit_redo()

                if widget == self.input_text:
                    self.refresh_visuals(
                        self.input_text,
                        self.areas[0][1]
                    )
                elif widget == self.output_text:
                    self.refresh_visuals(
                        self.output_text,
                        self.areas[1][1]
                    )

            except tk.TclError:
                pass

        return "break"

    def sync_numbers(
        self,
        text,
        line_numbers
    ):

        line_numbers.yview_moveto(
            text.yview()[0]
        )

    def refresh_visuals(
        self,
        text,
        line_numbers
    ):

        content = text.get(
            "1.0",
            "end-1c"
        )

        text.tag_remove(
            "time_tag",
            "1.0",
            "end"
        )

        text.tag_remove(
            "blank_line",
            "1.0",
            "end"
        )

        for match in TIME_PATTERN.finditer(
            content
        ):

            start = (
                f"1.0+{match.start()}c"
            )

            end = (
                f"1.0+{match.end()}c"
            )

            text.tag_add(
                "time_tag",
                start,
                end
            )

        lines = content.splitlines()

        line_numbers.config(
            state="normal"
        )

        line_numbers.delete(
            "1.0",
            "end"
        )

        nums = []

        for i, line in enumerate(
            lines,
            start=1
        ):

            nums.append(str(i))

            if line.strip() == "":
                text.tag_add(
                    "blank_line",
                    f"{i}.0",
                    f"{i}.end+1c"
                )

        line_numbers.insert(
            "1.0",
            "\n".join(nums)
        )

        line_numbers.config(
            state="disabled"
        )

    def time_to_cs(
        self,
        mm,
        ss,
        cs
    ):

        return (
            int(mm) * 6000 +
            int(ss) * 100 +
            int(cs)
        )

    def extract_times(
        self,
        line
    ):

        matches = TIME_CAPTURE.findall(
            line
        )

        if not matches:
            return None, None

        return (
            self.time_to_cs(
                *matches[0]
            ),
            self.time_to_cs(
                *matches[-1]
            )
        )

    def auto_format(self):

        try:

            mm, ss, cs = (
                self.threshold_var
                .get()
                .split(":")
            )

            threshold = (
                int(mm) * 6000 +
                int(ss) * 100 +
                int(cs)
            )

        except Exception:

            messagebox.showerror(
                "エラー",
                "閾値は mm:ss:SS"
            )

            return

        lines = [

            x.rstrip()

            for x in
            self.input_text.get(
                "1.0",
                "end"
            ).splitlines()

            if x.strip()
        ]

        result = []

        line_count = int(
            self.line_count_var.get()
        )

        pair = 0

        for i, line in enumerate(
            lines
        ):

            result.append(line)

            pair += 1

            blank = False

            if i < len(lines) - 1:

                _, last_time = (
                    self.extract_times(
                        line
                    )
                )

                next_first, _ = (
                    self.extract_times(
                        lines[i + 1]
                    )
                )

                if (
                    last_time is not None
                    and
                    next_first is not None
                ):

                    if (
                        next_first
                        -
                        last_time
                        >= threshold
                    ):

                        blank = True
                        pair = 0

            if pair >= line_count:

                blank = True
                pair = 0

            if (
                blank
                and
                i < len(lines) - 1
            ):

                result.append("")

        self.output_text.delete(
            "1.0",
            "end"
        )

        self.output_text.insert(
            "1.0",
            "\n".join(result)
        )

        self.refresh_visuals(
            self.output_text,
            self.areas[1][1]
        )

    def open_readme(self):

        path = os.path.join(
            self.get_app_dir(),
            "read me.txt"
        )

        if not os.path.exists(path):

            messagebox.showerror(
                "エラー",
                "read me.txt が見つかりません"
            )

            return

        os.startfile(path)
    
    def show_about(self):

        win = tk.Toplevel(
            self.root
        )
        
        win.transient(
            self.root
        )

        win.grab_set()
        win.focus_force()
        
        win.title(
            self.root.title()
        )

        win.geometry(
            "500x260"
        )
        
        win.update_idletasks()

        w = win.winfo_width()
        h = win.winfo_height()

        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()

        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2

        win.geometry(f"{w}x{h}+{x}+{y}")

        win.resizable(
            False,
            False
        )

        tk.Label(
            win,
            text=self.root.title(),
            font=(
                "",
                12,
                "bold"
            )
        ).pack(
            pady=(15, 10)
        )

        tk.Label(
            win,
            text="作者名：忍野イツキ"
        ).pack()

        tk.Label(
            win,
            text=""
        ).pack()
    
        tk.Label(
            win,
            text="X",
            font=(
                "",
                10,
                "bold"
            )
        ).pack()

        x_link = tk.Label(
            win,
            text="https://x.com/animehakase",
            fg="blue",
            cursor="hand2",
            font=(
                "",
                9,
                "underline"
            )
        )

        x_link.pack()

        x_link.bind(
            "<Button-1>",
            lambda e:
            webbrowser.open(
                "https://x.com/animehakase"
            )
        )

        tk.Label(
            win,
            text=""
        ).pack()

        tk.Label(
            win,
            text="YouTube",
            font=(
                "",
                10,
                "bold"
            )
        ).pack()

        yt_link = tk.Label(
            win,
            text="https://www.youtube.com/channel/UCEBuTXqgPftB6q36HtILlgA/",
            fg="blue",
            cursor="hand2",
            font=(
                "",
                9,
                "underline"
            )
        )

        yt_link.pack()

        yt_link.bind(
            "<Button-1>",
            lambda e:
            webbrowser.open(
                "https://www.youtube.com/channel/UCEBuTXqgPftB6q36HtILlgA/"
            )
        )

        tk.Button(
            win,
            text="閉じる",
            command=win.destroy
        ).pack(
            pady=15
        )
    
    def open_file(
        self,
        event=None
    ):

        path = filedialog.askopenfilename(

            title="テキストファイルを開く",

            filetypes=[

                ("Text File", "*.txt"),

                ("All Files", "*.*")
            ]
        )

        if not path:
            return

        with open(
            path,
            "r",
            encoding="utf-8"
        ) as f:

            text = f.read()

        self.input_text.delete(
            "1.0",
            "end"
        )

        self.input_text.insert(
            "1.0",
            text
        )

        self.refresh_visuals(
            self.input_text,
            self.areas[0][1]
        )
    
    def insert_blank_line(
        self,
        event=None
    ):

        text = self.output_text

        line_no = int(
            text.index(
                "insert"
            ).split(".")[0]
        )

        current = text.get(
            f"{line_no}.0",
            f"{line_no}.end"
        )

        if current.strip() == "":
            return

        next_line = text.get(
            f"{line_no+1}.0",
            f"{line_no+1}.end"
        )

        if next_line.strip() == "":
            return

        text.insert(
            f"{line_no+1}.0",
            "\n"
        )

        self.refresh_visuals(
            text,
            self.areas[1][1]
        )

    def remove_blank_line(self):

        text = self.output_text

        line_no = int(
            text.index(
                "insert"
            ).split(".")[0]
        )

        line = text.get(
            f"{line_no}.0",
            f"{line_no}.end"
        )

        if line.strip() == "":
            text.delete(
                f"{line_no}.0",
                f"{line_no+1}.0"
            )

        self.refresh_visuals(
            text,
            self.areas[1][1]
        )

    def remove_all_blank_lines(self):

        content = self.input_text.get(
            "1.0",
            "end"
        )

        lines = [
            x
            for x in
            content.splitlines()
            if x.strip()
        ]

        self.output_text.delete(
            "1.0",
            "end"
        )

        self.output_text.insert(
            "1.0",
            "\n".join(lines)
        )

        self.refresh_visuals(
            self.output_text,
            self.areas[1][1]
        )

    def copy_output(self):

        text = self.output_text.get(
            "1.0",
            "end-1c"
        )

        self.root.clipboard_clear()

        self.root.clipboard_append(
            text
        )

    def save_output(
        self,
        event=None
    ):

        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                (
                    "Text File",
                    "*.txt"
                )
            ]
        )

        if not path:
            return

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                self.output_text.get(
                    "1.0",
                    "end-1c"
                )
            )

    def clear_all(self):

        self.input_text.delete(
            "1.0",
            "end"
        )

        self.output_text.delete(
            "1.0",
            "end"
        )

        self.refresh_visuals(
            self.input_text,
            self.areas[0][1]
        )

        self.refresh_visuals(
            self.output_text,
            self.areas[1][1]
        )

if __name__ == "__main__":

    root = tk.Tk()

    app = LyricsFormatter(
        root
    )

    root.mainloop()