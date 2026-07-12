import ctypes
import re
import sys
import json
import os
import tkinter as tk
import webbrowser
import urllib.request
import urllib.error
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

GITHUB_API = ("https://api.github.com/repos/OshinoItsuki/lyrics_formatter/releases/latest")
SETTINGS_FILE = "settings.json"
APP_NAME = "歌詞改行ツール"
APP_VERSION = "1.9"

#
# デフォルト設定
#

DEFAULT_THRESHOLD = "00:03:10"
DEFAULT_LINE_COUNT = "2"
DEFAULT_CHECK_UPDATE_ON_START = True

#
# 初回起動時のサイズ
# （位置は起動時に中央へ配置）
#

DEFAULT_WINDOW_SIZE = "900x700"
DEFAULT_INSPECTOR_SIZE = "220x400"

#
# 検査設定
#

DEFAULT_IGNORE_FIRST_TAG_ERROR = True
DEFAULT_SORT_BY_FIRST_TAG = True


class LyricsFormatter:

    def __init__(self, root):

        self.root = root
        self.root.title(
            f"{APP_NAME} v{APP_VERSION}"
        )

        (
            threshold,
            line_count,
            geometry,
            inspector_geometry,
            ignore_first_tag_error,
            sort_by_first_tag,
            check_update_on_start
        ) = self.load_settings()

        self.sort_by_first_tag = tk.BooleanVar(
            value=sort_by_first_tag
        )

        #
        # メインウインドウ
        #

        self.root.geometry(
            geometry
        )
        
        self.inspector_geometry = (
            inspector_geometry
        )

        self.threshold_var = tk.StringVar(
            value=threshold
        )

        self.line_count_var = tk.StringVar(
            value=line_count
        )

        self.ignore_first_tag_error = tk.BooleanVar(
            value=ignore_first_tag_error
        )

        self.check_update_on_start = tk.BooleanVar(
            value=check_update_on_start
        )

        self.areas = []
        
        #
        # タイムタグ検査結果
        #

        self.inspect_errors = []

        #
        # タイムタグ監視
        #

        self.clipboard_monitor = None

        self.monitor_popup = None

        self.clipboard_monitor_enabled = False

        self.clipboard_sequence = 0
        
        self.inspector = TimeTagInspector(self)
        
        self.settings_dialog = SettingsDialog(self)
        
        self.build_ui()

        #
        # ウインドウサイズ確定
        #

        self.root.update_idletasks()

        #
        # 保存位置へ移動
        #

        self.root.geometry(
            geometry
        )

        #
        # 初回だけ中央表示
        #

        if "+" not in geometry:

            self.center_screen(
                self.root
            )

        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.on_close
        )

        #
        # 起動時更新チェック
        #

        if self.check_update_on_start.get():

            self.root.after(

                1000,

                lambda:
                    self.check_for_updates(
                        silent=True
                    )

            )

        #
        # アイコン設定
        #

        try:

            hwnd = self.root.winfo_id()

            ICON_SMALL = 0
            ICON_BIG = 1
            WM_SETICON = 0x0080

            hicon = ctypes.windll.user32.LoadIconW(
                ctypes.windll.kernel32.GetModuleHandleW(None),
                1
            )

            ctypes.windll.user32.SendMessageW(
                hwnd,
                WM_SETICON,
                ICON_SMALL,
                hicon
            )

            ctypes.windll.user32.SendMessageW(
                hwnd,
                WM_SETICON,
                ICON_BIG,
                hicon
            )

        except Exception:
            pass

        try:

            icon_path = os.path.join(
                self.get_app_dir(),
                "icon.ico"
            )

            self.root.iconbitmap(
                icon_path
            )

        except Exception:
            pass
        self.root.iconbitmap("icon.ico")
        
    def get_app_dir(self):

        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)

        return os.path.dirname(
            os.path.abspath(__file__)
        )

    def create_default_settings(self):

        data = {

            "threshold":
                DEFAULT_THRESHOLD,

            "line_count":
                DEFAULT_LINE_COUNT,

            "window_geometry":
                DEFAULT_WINDOW_SIZE,

            "inspector_geometry":
                DEFAULT_INSPECTOR_SIZE,

            "ignore_first_tag_error":
                DEFAULT_IGNORE_FIRST_TAG_ERROR,

            "sort_by_first_tag":
                DEFAULT_SORT_BY_FIRST_TAG,
            
             "check_update_on_start":
                DEFAULT_CHECK_UPDATE_ON_START
                       

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

    def load_settings(self):

        #
        # 無ければ作る
        #

        if not os.path.exists(
            SETTINGS_FILE
        ):

            self.create_default_settings()

        #
        # 読み込み
        #

        try:

            with open(
                SETTINGS_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

        except Exception:

            #
            # 壊れていたら作り直す
            #

            self.create_default_settings()

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
                DEFAULT_WINDOW_SIZE
            ),

            data.get(
                "inspector_geometry",
                DEFAULT_INSPECTOR_SIZE
            ),

            data.get(
                "ignore_first_tag_error",
                DEFAULT_IGNORE_FIRST_TAG_ERROR
            ),

            data.get(
                "sort_by_first_tag",
                DEFAULT_SORT_BY_FIRST_TAG
            ),

            data.get(
                "check_update_on_start",
                DEFAULT_CHECK_UPDATE_ON_START
            )

        )

    def save_settings(self):

        data = {
            "threshold":
                self.threshold_var.get(),

            "line_count":
                self.line_count_var.get(),

            "window_geometry":
                self.root.geometry(),
            "inspector_geometry":
                getattr(
                    self,
                    "inspector_geometry",
                    DEFAULT_INSPECTOR_SIZE
                ),
            "ignore_first_tag_error":
                self.ignore_first_tag_error.get(
                ),
            "sort_by_first_tag":
                self.sort_by_first_tag.get(
                ),
            "check_update_on_start":
                getattr(
                    self,
                    "check_update_on_start",
                    DEFAULT_CHECK_UPDATE_ON_START
                )
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

    def check_for_updates(
        self,
        silent=True
    ):

        latest = self.get_latest_release()

        #
        # 通信失敗
        #

        if latest is None:

            if not silent:

                messagebox.showwarning(
                    "更新確認",
                    "更新を確認できませんでした。\n"
                    "インターネット接続を確認してください。"
                )

            return

        #
        # 現在のバージョン
        #

        current = APP_VERSION

        latest_version = latest["version"].lstrip("v")

        #
        # 最新
        #

        if current == latest_version:

            if not silent:

                messagebox.showinfo(
                    "更新確認",
                    f"最新版です。\n\n現在：v{current}"
                )

            return

        #
        # 新しいバージョン
        #

        answer = messagebox.askyesno(

            "更新があります",

            f"新しいバージョンがあります。\n\n"

            f"現在：v{current}\n"

            f"最新：{latest['version']}\n"

            f"公開日：{latest['date']}\n\n"

            "最新版をダウンロードしますか?"

        )

        if answer:

            #
            # ダウンロードURLが取得できた
            #

            if latest["download"]:

                webbrowser.open(
                    latest["download"]
                )

            #
            # 念のためフォールバック
            #

            else:

                webbrowser.open(
                    latest["url"]
                )

    def on_close(self):

        self.save_settings()

        self.root.destroy()

    def get_latest_release(self):

        try:

            req = urllib.request.Request(
                GITHUB_API,
                headers={
                    "User-Agent": "LyricsFormatter"
                }
            )

            with urllib.request.urlopen(
                req,
                timeout=5
            ) as response:

                data = json.loads(
                    response.read().decode(
                        "utf-8"
                    )
                )

            assets = data.get(
                "assets",
                []
            )

            download_url = None

            if assets:

                download_url = assets[0].get(
                    "browser_download_url"
                )

            return {

                "version":
                    data["tag_name"],

                "date":
                    data["published_at"][:10],

                "url":
                    data["html_url"],

                "download":
                    download_url

            }

        except Exception:

            return None

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
            label="設定",
            command=self.settings_dialog.show
        )

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

        tool_menu.add_command(
            label="タイムタグ検査",
            command=self.inspector.show
        )
        
        tool_menu.add_command(
            label="タイムタグ監視",
            command=self.start_clipboard_monitor
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


        help_menu.add_command(

            label="更新を確認",

            command=lambda:
                self.check_for_updates(
                    silent=False
                )
        )

        help_menu.add_separator()
        
        help_menu.add_command(
            label="About",
            command=self.show_about
        )

        menubar.add_cascade(
            label="Help",
            menu=help_menu
        )

        self.root.config(
            menu=menubar
        )
    
    def build_ui(self):

        self.create_menu()
        
        self.root.grid_rowconfigure(
            0,
            weight=1
        )

        self.root.grid_rowconfigure(
            2,
            weight=1
        )

        self.root.grid_columnconfigure(
            0,
            weight=1
        )

        #
        # 入力エリア
        #

        input_area = tk.Frame(
            self.root
        )

        input_area.grid(
            row=0,
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

        button_area = tk.Frame(
            self.root
        )

        button_area.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=5,
            padx=5
        )

        #
        # 1段目
        #

        top_buttons = tk.Frame(
            button_area
        )

        top_buttons.pack(
            fill="x"
        )

        tk.Button(
            top_buttons,
            text="自動整形",
            command=self.auto_format
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            top_buttons,
            text="手動空行挿入",
            command=self.insert_blank_line
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            top_buttons,
            text="手動空行削除",
            command=self.remove_blank_line
        ).pack(
            side="left",
            padx=2
        )

        tk.Button(
            top_buttons,
            text="全空行削除",
            command=self.remove_all_blank_lines
        ).pack(
            side="left",
            padx=2
        )

        #
        # 右寄せ用余白
        #

        tk.Frame(
            top_buttons
        ).pack(
            side="left",
            expand=True,
            fill="x"
        )

        tk.Button(
            top_buttons,
            text="クリア",
            command=self.clear_all
        ).pack(
            side="right",
            padx=2
        )

        #
        # 区切り線
        #

        tk.Frame(
            button_area,
            height=1,
            bg="#bfbfbf"
        ).pack(
            fill="x",
            pady=6
        )

        #
        # 2段目
        #

        bottom_buttons = tk.Frame(
            button_area
        )

        bottom_buttons.pack(
            fill="x",
            anchor="w"
        )

        tk.Button(
            bottom_buttons,
            text="タイムタグ監視",
            command=self.start_clipboard_monitor,
            width=10
        ).pack(
            side="right",
            padx=2
        )

        tk.Button(
            bottom_buttons,
            text="タイムタグ検査",
            command=self.inspector.show,
            width=10
        ).pack(
            side="right",
            padx=2
        )
        #
        # 出力エリア
        #

        output_area = tk.Frame(
            self.root
        )

        output_area.grid(
            row=2,
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

        self.root.bind(
            "<FocusIn>",
            self.on_main_focus
        )

    def center_window(
        self,
        window
    ):

        window.update_idletasks()

        w = window.winfo_width()
        h = window.winfo_height()

        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()

        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        x = parent_x + (
            parent_w - w
        ) // 2

        y = parent_y + (
            parent_h - h
        ) // 2

        window.geometry(
            f"{w}x{h}+{x}+{y}"
        )

    def center_screen(
        self,
        window
    ):

        window.update_idletasks()

        w = window.winfo_width()
        h = window.winfo_height()

        sw = window.winfo_screenwidth()
        sh = window.winfo_screenheight()

        x = (sw - w) // 2
        y = (sh - h) // 2

        window.geometry(
            f"{w}x{h}+{x}+{y}"
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
            takefocus=0,
            font=("Yu Gothic UI", 10)
        )

        text = tk.Text(
            outer,
            wrap="none",
            undo=True,
            bg="#fcfcfc",
            font=("Yu Gothic UI", 10)
        )

        line_numbers.bind(
            "<Button-1>",
            lambda e, t=text, n=line_numbers:
                self.line_number_press(e, t, n)
        )

        line_numbers.bind(
            "<B1-Motion>",
            lambda e, t=text, n=line_numbers:
                self.line_number_drag(e, t, n)
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
            yscrollcommand=lambda first, last: (
                y_scroll.set(first, last),
                self.sync_numbers(
                    text,
                    line_numbers
                )
            ),
            xscrollcommand=x_scroll.set
        )
        
        text.bind(
            "<MouseWheel>",
            lambda e:
            self.sync_numbers(
                text,
                line_numbers
            ),
            add="+"
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
        
        text.tag_config(
            "inspect_tag",
            background="#ffd0d0"
        )
        
        text.tag_config(
            "inspect_time",
            foreground="red",
            font=("", 9, "bold")
        )
        
        text.tag_config(
            "inspect_line",
            background="#FFE4B5"
        )

        text.tag_config(
            "time_tag_error",
            foreground="#CC0000",
            font=("",9,"bold")
        )
        text.config(
            selectbackground="#3399FF",
            selectforeground="white",
            inactiveselectbackground="#3399FF"
        )        


        #
        # タグ表示優先順位
        #

        text.tag_raise(
            "blank_line"
        )

        text.tag_raise(
            "inspect_line"
        )

        text.tag_raise(
            "time_tag"
        )

        text.tag_raise(
            "time_tag_error"
        )

        #
        # 選択を最前面
        #

        text.tag_raise(
            tk.SEL
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
            (text,line_numbers)
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

    def refresh_time_tags(
        self,
        text,
        content
    ):

        text.tag_remove(
            "time_tag",
            "1.0",
            "end"
        )

        for match in TIME_PATTERN.finditer(
            content
        ):

            text.tag_add(
                "time_tag",
                f"1.0+{match.start()}c",
                f"1.0+{match.end()}c"
            )

    def refresh_blank_lines(
        self,
        text,
        lines
    ):

        text.tag_remove(
            "blank_line",
            "1.0",
            "end"
        )

        for i, line in enumerate(
            lines,
            start=1
        ):

            if not line.strip():

                text.tag_add(
                    "blank_line",
                    f"{i}.0",
                    f"{i}.end+1c"
                )

    def refresh_inspector(
        self,
        text,
        selected_lines
    ):

        text.tag_remove(
            "inspect_line",
            "1.0",
            "end"
        )

        text.tag_remove(
            "time_tag_error",
            "1.0",
            "end"
        )

        for error in self.inspect_errors:

            line = error["line"]

            #
            # 選択中はハイライトしない
            #

            if line in selected_lines:
                continue

            text.tag_add(
                "inspect_line",
                f"{line}.0",
                f"{line}.end+1c"
            )

            text.tag_add(
                "time_tag_error",
                f"{line}.0+{error['start']}c",
                f"{line}.0+{error['end']}c"
            )        

    def refresh_line_numbers(
        self,
        line_numbers,
        lines
    ):

        line_numbers.config(
            state="normal"
        )

        line_numbers.delete(
            "1.0",
            "end"
        )

        nums = []

        for i in range(
            1,
            len(lines)+1
        ):

            nums.append(
                str(i)
            )

        line_numbers.insert(
            "1.0",
            "\n".join(nums)
        )

        line_numbers.tag_delete(
            "inspect_line"
        )

        line_numbers.tag_config(
            "inspect_line",
            background="#FFE4B5"
        )

        for error in self.inspect_errors:

            line_numbers.tag_add(
                "inspect_line",
                f"{error['line']}.0",
                f"{error['line']}.end"
            )

        line_numbers.config(
            state="disabled"
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

        lines = content.splitlines()

        #
        # タイムタグ
        #

        self.refresh_time_tags(
            text,
            content
        )

        #
        # 空行
        #

        self.refresh_blank_lines(
            text,
            lines
        )

        #
        # 選択中の行取得
        #

        selected_lines = set()

        if text.tag_ranges(
            tk.SEL
        ):

            start = text.index(
                tk.SEL_FIRST
            )

            end = text.index(
                tk.SEL_LAST
            )

            first = int(
                start.split(".")[0]
            )

            last = int(
                end.split(".")[0]
            )

            for n in range(
                first,
                last + 1
            ):

                selected_lines.add(
                    n
                )

        #
        # 検査結果
        #

        self.refresh_inspector(
            text,
            selected_lines
        )

        #
        # 行番号
        #

        self.refresh_line_numbers(
            line_numbers,
            lines
        )

        #
        # タグ優先順位
        #

        text.tag_raise(
            "blank_line"
        )

        text.tag_raise(
            "inspect_line"
        )

        text.tag_raise(
            "time_tag"
        )

        text.tag_raise(
            "time_tag_error"
        )

        #
        # 選択を最前面
        #

        text.tag_raise(
            tk.SEL
        )

        #
        # 行番号同期
        #

        self.sync_numbers(
            text,
            line_numbers
        )
        
    def line_number_press(
        self,
        event,
        text,
        line_numbers
    ):

        #
        # クリックした行番号
        #

        index = line_numbers.index(
            f"@0,{event.y}"
        )

        self.line_select_start = int(
            index.split(".")[0]
        )

        self.select_line_range(
            text,
            self.line_select_start,
            self.line_select_start
        )

        return "break"

    def line_number_drag(
        self,
        event,
        text,
        line_numbers
    ):

        index = line_numbers.index(
            f"@0,{event.y}"
        )

        current = int(
            index.split(".")[0]
        )

        self.select_line_range(
            text,
            self.line_select_start,
            current
        )

        return "break"

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

    def sort_lines_by_first_tag(self,lines):

            sortable = []

            no_tag = []

            for index, line in enumerate(lines):

                #
                # タイムタグ取得
                #

                times = self.extract_times(
                    line
                )

                #
                # タイムタグ無し
                #

                if not times:

                    no_tag.append(line)

                    continue

                #
                # 最初のタイムタグ
                #

                sortable.append(

                    (
                        times[0],
                        index,
                        line
                    )

                )

            #
            # 時間順
            #

            sortable.sort()

            result = [

                line

                for _, _, line

                in sortable

            ]

            #
            # タイムタグ無しは最後
            #

            result.extend(
                no_tag
            )

            return result

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

        #
        # 入力取得（空行は除外）
        #

        lines = [

            x.rstrip()

            for x in
            self.input_text.get(
                "1.0",
                "end"
            ).splitlines()

            if x.strip()
        ]

        #
        # 時間順に並べ替え
        #

        if self.sort_by_first_tag.get():

            lines = self.sort_lines_by_first_tag(
                lines
            )

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

                current_times = self.extract_times(
                    line
                )

                next_times = self.extract_times(
                    lines[i + 1]
                )

                if (
                    current_times
                    and
                    next_times
                ):

                    last_time = current_times[1]
                    next_first = next_times[0]

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

        self.copy_output()

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
            text="作者名：忍野イツキ from 忍野カラオケ動画製作所"
        ).pack()

        tk.Label(
            win,
            text=""
        ).pack()
    
        tk.Label(
            win,
            text="X(Twitter)",
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
        
    def on_main_focus(
        self,
        event=None
    ):

        if (
            self.inspector.window
            and
            self.inspector.window.winfo_exists()
        ):

            self.inspector.window.lift()
            
    def start_clipboard_monitor(self):

        #
        # 二重起動防止
        #

        if (
            self.monitor_popup
            and
            self.monitor_popup.winfo_exists()
        ):
            return

        self.monitor_popup = tk.Toplevel(
            self.root
        )

        self.monitor_popup.title(
            "タイムタグ監視"
        )

        self.monitor_popup.resizable(
            False,
            False
        )

        self.monitor_popup.transient(
            self.root
        )

        self.monitor_popup.grab_set()

        self.monitor_popup.focus_force()

        tk.Label(

            self.monitor_popup,

            text=(
                "RhythmicaLyricsのテキスト編集モードで\n\n"
                "歌詞を全選択コピーしてください"
            ),

            font=("",11)

        ).pack(
            padx=30,
            pady=(20,15)
        )

        self.monitor_status = tk.Label(

            self.monitor_popup,

            text="待機中..."

        )

        self.monitor_status.pack(
            pady=(0,20)
        )

        tk.Button(

            self.monitor_popup,

            text="キャンセル",

            command=self.stop_clipboard_monitor

        ).pack(
            pady=(0,20)
        )

        self.monitor_popup.protocol(

            "WM_DELETE_WINDOW",

            self.stop_clipboard_monitor

        )

        self.center_window(
            self.monitor_popup
        )

        #
        # 現在のクリップボード更新番号を記録
        #

        self.clipboard_sequence = (
            ctypes.windll.user32.GetClipboardSequenceNumber()
        )

        self.monitor_status.config(
            text="待機中..."
        )

        self.clipboard_monitor_enabled = True

        self.check_clipboard()
        
        
    def stop_clipboard_monitor(self):

        self.clipboard_monitor_enabled = False

        if (
            self.monitor_popup
            and
            self.monitor_popup.winfo_exists()
        ):

            self.monitor_popup.destroy()

        if self.clipboard_monitor:

            self.root.after_cancel(
                self.clipboard_monitor
            )

        self.monitor_popup = None

        self.clipboard_monitor = None

    def schedule_clipboard_check(self):

        self.clipboard_monitor = self.root.after(
            200,
            self.check_clipboard
        )    

    def check_clipboard(self):
        #
        # 監視中のみ動作
        #

        if not self.clipboard_monitor_enabled:
            return

        #
        # 監視ウインドウが閉じられた
        #

        if (
            self.monitor_popup is None
            or
            not self.monitor_popup.winfo_exists()
        ):
            return
        
        #
        # クリップボード更新番号確認
        #

        current_sequence = (
            ctypes.windll.user32.GetClipboardSequenceNumber()
        )

        #
        # 更新されていない
        #

        if current_sequence == self.clipboard_sequence:
            self.schedule_clipboard_check()
            return

        #
        # 更新番号更新
        #

        self.clipboard_sequence = current_sequence

        #
        # テキスト取得
        #

        try:

            text = self.root.clipboard_get()

        except Exception:
            self.schedule_clipboard_check()
            return

        #
        # タイムタグが無ければ監視継続
        #

        if not TIME_PATTERN.search(text):
            self.schedule_clipboard_check()
            return

    #
    # タイムタグがある
    #

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

        #
        # 自動整形
        #

        self.auto_format()

        #
        # 監視終了
        #

        self.stop_clipboard_monitor()

        return

    def select_line_range(
        self,
        text,
        start_line,
        end_line
    ):

        #
        # 順番補正
        #

        if start_line > end_line:

            start_line, end_line = (
                end_line,
                start_line
            )

        #
        # 選択解除
        #

        text.tag_remove(
            tk.SEL,
            "1.0",
            "end"
        )

        #
        # 行選択
        #

        text.tag_add(
            tk.SEL,
            f"{start_line}.0",
            f"{end_line + 1}.0"
        )

        #
        # カーソル
        #

        text.mark_set(
            tk.INSERT,
            f"{start_line}.0"
        )

        text.see(
            f"{start_line}.0"
        )

        text.focus_set()

class TimeTagInspector:

    def __init__(
        self,
        app
    ):

        self.app = app
        self.root = app.root

        self.window = None

        self.status_label = None
        self.listbox = None

        self.prev_button = None
        self.next_button = None
        self.recheck_button = None

        #
        # 検査結果
        #

        self.errors = []

        self.current_index = -1

    def show(self):

        #
        # 既に開いているなら再検査
        #

        if (
            self.window
            and
            self.window.winfo_exists()
        ):

            self.window.lift()
            self.window.focus_force()

            self.inspect()

            return

        self.window = tk.Toplevel(
            self.root
        )

        self.window.title(
            "検査"
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close
        )
        
        self.create_widgets()

        #
        # 前回位置で開く
        #

        geometry = self.app.inspector_geometry

        #
        # 初回（サイズだけ保存されている）
        #

        if "+" not in geometry:

            self.window.geometry(
                geometry
            )

            self.app.center_window(
                self.window
            )

        else:

            self.window.geometry(
                geometry
            )

        self.inspect()

    def create_widgets(self):

        self.status_label = tk.Label(
            self.window,
            text="異常件数：0件",
            anchor="w"
        )

        self.status_label.pack(
            fill="x",
            padx=10,
            pady=(10, 5)
        )

        frame = tk.Frame(
            self.window
        )

        frame.pack(
            fill="both",
            expand=True,
            padx=10
        )

        scrollbar = tk.Scrollbar(
            frame
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.listbox = tk.Listbox(
            frame,
            activestyle="none"
        )

        self.listbox.pack(
            side="left",
            fill="both",
            expand=True
        )

        self.listbox.config(
            yscrollcommand=scrollbar.set
        )

        scrollbar.config(
            command=self.listbox.yview
        )

        self.listbox.bind(
            "<<ListboxSelect>>",
            self.on_listbox_select
        )

        self.listbox.bind(
            "<Double-Button-1>",
            self.on_listbox_double_click
        )

        self.listbox.bind(
            "<Return>",
            self.on_listbox_enter
        )

        button_frame = tk.Frame(
            self.window
        )

        button_frame.pack(
            fill="x",
            padx=10,
            pady=10
        )

        self.prev_button = tk.Button(
            button_frame,
            text="◀ 前へ",
            state="disabled",
            command=self.move_prev
        )

        self.prev_button.pack(
            side="left",
            expand=True,
            fill="x",
            padx=2
        )

        self.next_button = tk.Button(
            button_frame,
            text="次へ ▶",
            state="disabled",
            command=self.move_next
        )

        self.next_button.pack(
            side="left",
            expand=True,
            fill="x",
            padx=2
        )

        bottom = tk.Frame(
            self.window
        )

        bottom.pack(
            fill="x",
            padx=10,
            pady=(0, 10)
        )

        self.recheck_button = tk.Button(
            bottom,
            text="検査",
            state="disabled",
            command=self.inspect
        )

        self.recheck_button.pack(
            side="left",
            expand=True,
            fill="x",
            padx=2
        )

        tk.Button(
            bottom,
            text="閉じる",
            command=self.close
        ).pack(
            side="left",
            expand=True,
            fill="x",
            padx=2
        )

    def time_to_cs(
        self,
        mm,
        ss,
        cs
    ):

        return (
            int(mm) * 6000
            +
            int(ss) * 100
            +
            int(cs)
        )

    def extract_times(
        self,
        line
    ):

        result = []

        for match in TIME_CAPTURE.finditer(line):

            result.append(

                (
                    self.time_to_cs(
                        match.group(1),
                        match.group(2),
                        match.group(3)
                    ),
                    match.start(),
                    match.end()
                )

            )

        return result
        
    def inspect(self):

        self.errors.clear()

        self.listbox.delete(
            0,
            tk.END
        )

        text = self.app.output_text.get(
            "1.0",
            "end-1c"
        )

        previous = None

        for line_no, line in enumerate(
            text.splitlines(),
            start=1
        ):

            times = self.extract_times(line)

            tag_index = 0

            for time_cs, start, end in times:

                tag_index += 1
                
                if (
                    previous is not None
                    and
                    time_cs <= previous
                ):

                    error = {
                        "line": line_no,
                        "time": time_cs,
                        "start": start,
                        "end": end
                    }

                    #
                    # 各行の最初のタイムタグの違反は表示しない
                    #

                    if (
                        self.app.ignore_first_tag_error.get()
                        and
                        tag_index == 1
                    ):
                        previous = time_cs
                        continue

                    self.errors.append(
                        error
                    )

                    self.listbox.insert(
                        tk.END,
                        f"{line_no}行目"
                    )

                previous = time_cs

        #
        # 件数表示
        #

        if self.errors:

            self.status_label.config(
                text=f"⚠ 異常件数：{len(self.errors)}件",
                fg="red"
            )

        else:

            self.status_label.config(
                text="✔ 異常は見つかりませんでした",
                fg="green"
            )

        #
        # ボタン
        #

        state = (
            "normal"
            if self.errors
            else "disabled"

        )

        self.prev_button.config(
            state=state
        )

        self.next_button.config(
            state=state
        )

        self.recheck_button.config(
            state="normal"
        )

        #
        # ハイライト更新
        #

        self.app.inspect_errors = self.errors.copy()
        self.app.refresh_visuals(
            self.app.output_text,
            self.app.areas[1][1]
        )

        #
        # 初回選択
        #

        if self.errors:

            self.current_index = 0
            self.listbox.selection_clear(
                0,
                tk.END
            )
            
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self.listbox.see(0)
            self.jump_to_current()
        else:
            self.current_index = -1

    def move_next(self):

        if not self.errors:
            return

        self.current_index += 1

        if self.current_index >= len(self.errors):
            self.current_index = 0

        self.jump_to_current()


    def move_prev(self):

        if not self.errors:
            return

        self.current_index -= 1

        if self.current_index < 0:
            self.current_index = len(self.errors) - 1

        self.jump_to_current()


    def jump_to_current(self):

        if not self.errors:
            return

        error = self.errors[self.current_index]

        text = self.app.output_text

        index = (
            f"{error['line']}.0+{error['start']}c"
        )

        #
        # カーソル
        #

        text.mark_set(
            "insert",
            index
        )

        #
        # 縦スクロール
        #

        text.see(index)

        #
        # 横スクロール
        #

        try:

            #
            # 現在の幅（文字数）
            #

            visible_chars = max(
                20,
                text.winfo_width() // 9
            )

            #
            # 左端を少し前にずらす
            #

            left_char = max(
                0,
                error["start"] - visible_chars // 2
            )

            text.xview_moveto(
                left_char / 500
            )

        except Exception:
            pass

        text.focus_set()

        #
        # Listbox同期
        #

        self.listbox.selection_clear(
            0,
            tk.END
        )

        self.listbox.selection_set(
            self.current_index
        )

        self.listbox.activate(
            self.current_index
        )

        self.listbox.see(
            self.current_index
        )


    def on_listbox_select(
        self,
        event=None
    ):

        selection = self.listbox.curselection()
        if not selection:
            return
        self.current_index = selection[0]


    def on_listbox_double_click(
        self,
        event=None
    ):

        selection = self.listbox.curselection()
        if not selection:
            return
        self.current_index = selection[0]
        self.jump_to_current()


    def on_listbox_enter(
        self,
        event=None
    ):

        self.on_listbox_double_click()
        return "break"

    def close(self):

        if (
            self.window
            and
            self.window.winfo_exists()
        ):

            self.app.inspector_geometry = (
                self.window.geometry()
            )

            #
            # settings.json 更新
            #

            self.app.save_settings()

            self.window.destroy()

            self.window = None

            self.root.after_idle(
                self.clear_highlight
            )

    def clear_highlight(self):

        #
        # ハイライト解除
        #

        self.app.inspect_errors.clear()

        self.app.refresh_visuals(
            self.app.output_text,
            self.app.areas[1][1]
        )          

class SettingsDialog:

    def __init__(
        self,
        app
    ):

        self.app = app

        self.root = app.root

        self.window = None

    def show(self):

        #
        # 既に開いている
        #

        if (
            self.window
            and
            self.window.winfo_exists()
        ):

            self.window.lift()
            self.window.focus_force()

            return

        self.window = tk.Toplevel(
            self.root
        )

        self.window.title(
            "設定"
        )

        self.window.resizable(
            False,
            False
        )

        self.window.transient(
            self.root
        )

        self.window.grab_set()

        #
        # 変数
        #

        self.threshold_var = tk.StringVar(
            value=self.app.threshold_var.get()
        )

        self.line_count_var = tk.StringVar(
            value=self.app.line_count_var.get()
        )

        self.ignore_first_tag_error = tk.BooleanVar(
            value=self.app.ignore_first_tag_error.get()
        )

        self.sort_by_first_tag = tk.BooleanVar(
            value=self.app.sort_by_first_tag.get()
        )

        #
        # メインフレーム
        #

        main = tk.Frame(
            self.window,
            padx=15,
            pady=15
        )

        main.pack(
            fill="both",
            expand=True
        )

        #
        # メインウインドウ設定
        #

        main_group = tk.LabelFrame(
            main,
            text="メインウインドウ設定",
            padx=10,
            pady=10
        )

        main_group.pack(
            fill="x",
            pady=(0,10)
        )

        tk.Label(
            main_group,
            text="時間差閾値"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0,10)
        )

        tk.Entry(
            main_group,
            textvariable=self.threshold_var,
            width=10
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(10,0),
            pady=(0,10)
        )

        tk.Label(
            main_group,
            text="改行間隔"
        ).grid(
            row=1,
            column=0,
            sticky="nw"
        )

        radio_frame = tk.Frame(
            main_group
        )

        radio_frame.grid(
            row=1,
            column=1,
            sticky="w",
            padx=(10,0)
        )

        for value in (
            "2",
            "3",
            "4"
        ):

            tk.Radiobutton(
                radio_frame,
                text=f"{value}行",
                value=value,
                variable=self.line_count_var
            ).pack(
                anchor="w"
            )

        tk.Checkbutton(
            main_group,
            text="最初のタイムタグ順に並べ替える",
            variable=self.sort_by_first_tag
        ).grid(
            row=2,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(8,0)
        )

        tk.Checkbutton(
            main_group,
            text="起動時に更新を確認する",
            variable=self.app.check_update_on_start
        ).grid(
            row=3,
            column=0,
            columnspan=2,
            sticky="w",
            pady=(4,0)
        )

        #
        # タイムタグ検査設定
        #

        inspect_group = tk.LabelFrame(
            main,
            text="タイムタグ検査設定",
            padx=10,
            pady=10
        )

        inspect_group.pack(
            fill="x",
            pady=(0,10)
        )

        tk.Checkbutton(
            inspect_group,
            text="各行の最初のタイムタグの違反は無視する",
            variable=self.ignore_first_tag_error
        ).pack(
            anchor="w"
        )

        #
        # ボタン
        #

        button_frame = tk.Frame(
            main
        )

        button_frame.pack(
            pady=(5,0)
        )

        tk.Button(
            button_frame,
            text="OK",
            width=10,
            command=self.apply
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="キャンセル",
            width=10,
            command=self.window.destroy
        ).pack(
            side="left",
            padx=5
        )

        self.window.update_idletasks()

        self.app.center_window(
            self.window
        )

    def apply(self):

        #
        # 値を反映
        #

        self.app.threshold_var.set(
            self.threshold_var.get()
        )

        self.app.line_count_var.set(
            self.line_count_var.get()
        )

        self.app.ignore_first_tag_error.set(
            self.ignore_first_tag_error.get()
        )

        self.app.sort_by_first_tag.set(
            self.sort_by_first_tag.get()
        )
        
        #
        # JSONへ保存
        #

        self.app.save_settings()

        #
        # 閉じる
        #

        self.window.destroy()

if __name__ == "__main__":

    root = tk.Tk()

    app = LyricsFormatter(
        root
    )

    root.mainloop()
    