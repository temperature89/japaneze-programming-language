from io import StringIO
import sys

"""
ja2py_ai.py

日本語擬似言語 -> Python 変換器（中間表現を使用）
対応（簡易）:
 - <expr> とひょうじする -> print(<expr>)
 - X を <rpn...> にする -> X = <infix>
 - <rpn...> かいくりかえす -> for _ in range(<infix>):
 - もし <rpn...> なら / でなければ -> if / else
 - ていぎ name args [ ... ] -> def name(args):
 - よびだす name args -> name(args)

中間表現 (IR): Node クラス群で構築し、最後に Python コードを生成します。
"""

# --- 既存 ja2py.py と互換のためのユーティリティ ---
def integrate_str(tokens):
    if len(tokens) == 1:
        return tokens
    quote_chars = ['"', "'"]
    in_quote = False
    quote_start_index = None
    quote_index = {}
    integrated_tokens = []
    integrated_str = ''
    pass_index = set()
    n = 0
    for token in tokens:
        if token and token[0] in quote_chars:
            in_quote = True
            quote_start_index = n
        if in_quote and token and token[-1] in quote_chars:
            in_quote = False
            quote_index[quote_start_index] = n
        n += 1

    i = 0
    while i < len(tokens):
        if i in pass_index:
            i += 1
            continue
        if i in quote_index:
            integrated_str = ''
            for j in range(i, quote_index[i] + 1):
                integrated_str += tokens[j] + ' '
                pass_index.add(j)
            integrated_tokens.append(integrated_str.rstrip(' '))
            i = quote_index[i] + 1
        else:
            integrated_tokens.append(tokens[i])
            i += 1
    return integrated_tokens


def eval_exp(tokens):
    # 逆ポーランド記法 -> 中置式文字列
    stack = []
    for token in tokens:
        if token == '+':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} + {b})")
        elif token == '-':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} - {b})")
        elif token == '*':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} * {b})")
        elif token == '/':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} / {b})")
        elif token == '=':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} == {b})")
        elif token == '>':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} > {b})")
        elif token == '<':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} < {b})")
        elif token == '>=':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} >= {b})")
        elif token == '<=':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} <= {b})")
        elif token == '!=':
            b = stack.pop(); a = stack.pop(); stack.append(f"({a} != {b})")
        else:
            stack.append(token)
    return stack[-1] if stack else ''


def eval_tokens(tokens):
    if not tokens:
        return ''
    if len(tokens) == 1:
        return tokens[0]
    return eval_exp(tokens)


# --- IR ノード ---
class Node:
    def to_python(self, indent=0):
        return []


class Block(Node):
    def __init__(self):
        self.stmts = []

    def to_python(self, indent=0):
        lines = []
        for s in self.stmts:
            lines += s.to_python(indent)
        return lines


class Assign(Node):
    def __init__(self, name, expr_tokens):
        self.name = name
        self.expr = expr_tokens

    def to_python(self, indent=0):
        expr = eval_tokens(self.expr)
        return ["    " * indent + f"{self.name} = {expr}"]


class Print(Node):
    def __init__(self, expr_tokens):
        self.expr = expr_tokens

    def to_python(self, indent=0):
        expr = eval_tokens(self.expr)
        return ["    " * indent + f"print({expr})"]


class ForLoop(Node):
    def __init__(self, times_tokens, body):
        self.times = times_tokens
        self.body = body

    def to_python(self, indent=0):
        expr = eval_tokens(self.times)
        lines = ["    " * indent + f"for _ in range({expr}):"]
        lines += self.body.to_python(indent + 1)
        return lines


class IfNode(Node):
    def __init__(self, cond_tokens, body, orelse=None):
        self.cond = cond_tokens
        self.body = body
        self.orelse = orelse

    def to_python(self, indent=0):
        cond = eval_tokens(self.cond)
        lines = ["    " * indent + f"if {cond}:"]
        lines += self.body.to_python(indent + 1)
        if self.orelse:
            lines += ["    " * indent + "else:"]
            lines += self.orelse.to_python(indent + 1)
        return lines


class DefNode(Node):
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

    def to_python(self, indent=0):
        arglist = ', '.join(self.args)
        lines = ["    " * indent + f"def {self.name}({arglist}):"]
        lines += self.body.to_python(indent + 1)
        return lines


class Call(Node):
    def __init__(self, name, raw_args):
        self.name = name
        self.raw_args = raw_args

    def to_python(self, indent=0):
        # raw_args: list of token-strings that will be joined with ', '
        args = []
        if self.raw_args:
            # join contiguous tokens as single args as ja2py.py did
            args = [a for a in self.raw_args]
        return ["    " * indent + f"{self.name}({', '.join(args)})"]


# --- パーサ ---
def parse_lines(lines):
    root = Block()
    stack = [root]
    pending_parent = None  # node waiting for next '[' to become its body
    last_if = None
    expect_else = False

    for raw in lines:
        line = raw.strip()
        if line == '':
            continue
        if line == '[':
            # attach a new block to pending_parent or to last_if. default: push empty block
            new_block = Block()
            if expect_else and last_if is not None:
                last_if.orelse = new_block
                expect_else = False
            elif pending_parent is not None:
                # assign as body
                if isinstance(pending_parent, (IfNode, ForLoop, DefNode)):
                    pending_parent.body = new_block
                pending_parent = None
            else:
                # push as anonymous nested block
                pass
            stack.append(new_block)
            continue
        if line == ']':
            if len(stack) > 1:
                stack.pop()
            continue

        tokens = integrate_str(line.split(' '))
        cur = stack[-1]

        # print
        if tokens[-1] == 'とひょうじする':
            expr = tokens[0:len(tokens)-1]
            node = Print(expr)
            cur.stmts.append(node)
            continue

        # assign
        if tokens[-1] == 'にする':
            # X を <expr> にする
            if len(tokens) >= 4 and tokens[1] == 'を':
                name = tokens[0]
                expr = tokens[2:len(tokens)-1]
                node = Assign(name, expr)
                cur.stmts.append(node)
            continue

        # for loop
        if tokens[-1] == 'かいくりかえす':
            expr = tokens[0:len(tokens)-1]
            node = ForLoop(expr, Block())
            cur.stmts.append(node)
            pending_parent = node
            continue

        # if
        if tokens[0] == 'もし' and tokens[-1] == 'なら':
            cond = tokens[1:len(tokens)-1]
            node = IfNode(cond, Block())
            cur.stmts.append(node)
            last_if = node
            pending_parent = node
            continue

        # else
        if tokens[0] == 'でなければ':
            # next '[' will attach to last_if. set flag
            expect_else = True
            continue

        # def
        if tokens[0] == 'ていぎ':
            name = tokens[1] if len(tokens) > 1 else 'f'
            args = tokens[2:] if len(tokens) > 2 else []
            node = DefNode(name, args, Block())
            cur.stmts.append(node)
            pending_parent = node
            continue

        # call
        if tokens[0] == 'よびだす':
            if len(tokens) >= 2:
                name = tokens[1]
                args = tokens[2:]
                node = Call(name, args)
                cur.stmts.append(node)
            continue

        # fallthrough: unknown -> ignore
    return root


def convert(program_text):
    stream = StringIO(program_text)
    lines = [l.rstrip('\n').strip() for l in stream if l.strip() != '']
    ir = parse_lines(lines)
    py_lines = ir.to_python()
    return '\n'.join(py_lines)


def main():
    if len(sys.argv) >= 2:
        path = sys.argv[1]
        with open(path, 'r', encoding='utf-8') as f:
            src = f.read()
    else:
        src = sys.stdin.read()
    out = convert(src)
    print(out)


if __name__ == '__main__':
    main()
