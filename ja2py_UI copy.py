import tkinter as tk
from tkinter import ttk
import io
import contextlib
import importlib

import ja2py   # ← アップロードされたファイル

class TranspilerUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("日本語言語 ⇄ Python トランスパイラ")
        self.geometry("1000x700")
        self.create_widgets()

    def create_widgets(self):
        # ===== 上（左右） =====
        top = ttk.Frame(self)
        top.pack(fill=tk.BOTH, expand=True)

        # 左：Python
        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left, text="Pythonコード").pack(anchor=tk.W)
        self.py_text = tk.Text(left)
        self.py_text.pack(fill=tk.BOTH, expand=True)

        # 右：日本語言語
        right = ttk.Frame(top)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text="日本語言語").pack(anchor=tk.W)
        self.ja_text = tk.Text(right)
        self.ja_text.pack(fill=tk.BOTH, expand=True)

        # ===== ボタン =====
        btns = ttk.Frame(self)
        btns.pack(fill=tk.X)

        ttk.Button(btns, text="日本語 → Python", command=self.ja_to_py)\
            .pack(side=tk.LEFT, padx=5)

        ttk.Button(btns, text="Python 実行", command=self.run_python)\
            .pack(side=tk.LEFT, padx=5)

        # ===== 下：出力 =====
        ttk.Label(self, text="実行結果").pack(anchor=tk.W)
        self.out = tk.Text(self, height=12, bg="#111", fg="#0f0")
        self.out.pack(fill=tk.BOTH)

    # =========================
    # 日本語 → Python
    # =========================
    def ja_to_py(self):
        self.out.delete("1.0", tk.END)

        code = self.ja_text.get("1.0", tk.END)

        # ja2py をリロード（再実行対応）
        importlib.reload(ja2py)

        # program を差し替え
        ja2py.program = code

        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ja2py.main()
        except Exception as e:
            self.out.insert(tk.END, f"変換エラー:\n{e}")
            return

        py_code = buf.getvalue()
        self.py_text.delete("1.0", tk.END)
        self.py_text.insert(tk.END, py_code)

    # =========================
    # Python 実行
    # =========================
    def run_python(self):
        self.out.delete("1.0", tk.END)
        code = self.py_text.get("1.0", tk.END)

        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                exec(code, {})
        except Exception as e:
            self.out.insert(tk.END, f"実行エラー:\n{e}")
            return

        self.out.insert(tk.END, buf.getvalue())


if __name__ == "__main__":
    TranspilerUI().mainloop()