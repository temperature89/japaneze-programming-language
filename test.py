# yui_to_python_transpiler_ui.py
# YUI言語 → Python トランスパイラ UI（tkinter版）

import tkinter as tk
from tkinter import ttk
import re
import io
import sys

# =====================
# YUI → Python トランスパイラ
# =====================
class YUITranspiler:
    def __init__(self):
        self.indent = 0
        self.lines = []

    def transpile(self, source: str) -> str:
        self.indent = 0
        self.lines = []
        for raw in source.splitlines():
            line = raw.strip()
            if not line or line.startswith('※'):
                continue
            self._line(line)
        return '\n'.join(self.lines)

    def emit(self, code: str):
        self.lines.append('    ' * self.indent + code)

    def _line(self, line: str):
        if line.endswith('。'):
            line = line[:-1]

        # 表示
        m = re.match(r'表示する (.+)', line)
        if m:
            expr = self._expr(m.group(1))
            self.emit(f"print({expr})")
            return

        # 入力
        m = re.match(r'(.+?) を 入力する', line)
        if m:
            self.emit(f"{m.group(1)} = input()")
            return

        # 変数宣言
        m = re.match(r'(数|文字|真) (.+?) は (.+)', line)
        if m:
            self.emit(f"{m.group(2)} = {self._expr(m.group(3))}")
            return

        # if
        m = re.match(r'もし (.+) ならば', line)
        if m:
            self.emit(f"if {self._expr(m.group(1))}:")
            self.indent += 1
            return

        # else
        if line == 'そうでなければ':
            self.indent -= 1
            self.emit('else:')
            self.indent += 1
            return

        # for
        m = re.match(r'(\d+) 回 繰り返す', line)
        if m:
            self.emit(f"for _ in range({m.group(1)}):")
            self.indent += 1
            return

        # while
        m = re.match(r'(.+?) の間 繰り返す', line)
        if m:
            self.emit(f"while {self._expr(m.group(1))}:")
            self.indent += 1
            return

        # 終わり
        if line == '終わり':
            self.indent -= 1
            return

        # 代入
        m = re.match(r'(.+?) は (.+)', line)
        if m:
            self.emit(f"{m.group(1)} = {self._expr(m.group(2))}")
            return

        raise SyntaxError(f"構文エラー: {line}")

    def _expr(self, expr: str) -> str:
        expr = expr.replace('真', 'True').replace('偽', 'False')
        expr = expr.replace(' 以上', ' >= ').replace(' 以下', ' <= ')
        expr = re.sub(r'「(.+?)」', r'"\1"', expr)
        return expr


# =====================
# tkinter UI
# =====================
class YUIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('YUI → Python トランスパイラ')
        self.geometry('1000x700')
        self.transpiler = YUITranspiler()
        self._build_ui()

    def _build_ui(self):
        top = ttk.Frame(self)
        top.pack(fill=tk.BOTH, expand=True)

        bottom = ttk.Frame(self, height=200)
        bottom.pack(fill=tk.X)

        # 左：YUI
        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(left, text='YUI言語').pack()
        self.yui_text = tk.Text(left, font=('Courier', 11))
        self.yui_text.pack(fill=tk.BOTH, expand=True)

        # 右：Python
        right = ttk.Frame(top)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(right, text='Pythonコード').pack()
        self.py_text = tk.Text(right, font=('Courier', 11), state=tk.DISABLED)
        self.py_text.pack(fill=tk.BOTH, expand=True)

        # 実行ボタン
        btn = ttk.Button(self, text='▶ トランスパイル & 実行', command=self.run)
        btn.pack(pady=5)

        # 下：出力
        ttk.Label(bottom, text='出力').pack(anchor=tk.W)
        self.out_text = tk.Text(bottom, height=10, font=('Courier', 11))
        self.out_text.pack(fill=tk.BOTH, expand=True)

        # 初期コード
        self.yui_text.insert(tk.END, """※ サンプル
数 年齢 は 20。

もし 年齢 >= 20 ならば
    表示する 「成人である」。
そうでなければ
    表示する 「未成年である」。
終わり。
""")

    def run(self):
        yui = self.yui_text.get('1.0', tk.END)
        try:
            py = self.transpiler.transpile(yui)
        except Exception as e:
            self._set_output(str(e))
            return
        self._set_python(py)
        self._execute_python(py)

    def _set_python(self, code: str):
        self.py_text.config(state=tk.NORMAL)
        self.py_text.delete('1.0', tk.END)
        self.py_text.insert(tk.END, code)
        self.py_text.config(state=tk.DISABLED)

    def _set_output(self, text: str):
        self.out_text.delete('1.0', tk.END)
        self.out_text.insert(tk.END, text)

    def _execute_python(self, code: str):
        buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buffer
        try:
            exec(code, {})
        except Exception as e:
            print('実行エラー:', e)
        finally:
            sys.stdout = old_stdout
        self._set_output(buffer.getvalue())


if __name__ == '__main__':
    app = YUIApp()
    app.mainloop()
