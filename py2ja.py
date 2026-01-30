import ast
import sys

"""
簡易 Python -> 日本語擬似言語 変換器
対応する構文:
 - print(...) -> <expr> とひょうじする
 - x = y -> x を <expr> にする
 - for ... in range(N): -> <N> かいくりかえす
 - if <cond>: -> もし <cond> なら
 - else -> でなければ
 - def name(args): -> ていぎ name args
 - function call -> よびだす name args

出力は ja2py.py で解釈できる形式（空白区切りトークン、ブロックは `[` と `]`）を目指します。
"""


def const_token(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f'"{node.value}"'
        else:
            return str(node.value)
    return None


def expr_to_infix_tokens(node):
    # 単純化した AST -> 中置トークン列
    if isinstance(node, ast.BinOp):
        left = expr_to_infix_tokens(node.left)
        right = expr_to_infix_tokens(node.right)
        op = {
            ast.Add: '+', ast.Sub: '-', ast.Mult: '*', ast.Div: '/', ast.Mod: '%'
        }[type(node.op)]
        return left + [op] + right
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        t = expr_to_infix_tokens(node.operand)
        return ['0', '-',] + t
    if isinstance(node, ast.Compare):
        # 単一比較のみ対応
        left = expr_to_infix_tokens(node.left)
        comp = node.ops[0]
        right = expr_to_infix_tokens(node.comparators[0])
        op_map = {ast.Eq: '=', ast.NotEq: '!=', ast.Gt: '>', ast.Lt: '<', ast.GtE: '>=', ast.LtE: '<='}
        op_token = op_map[type(comp)]
        return left + [op_token] + right
    if isinstance(node, ast.Call):
        # 関数呼び出しを単一トークンにまとめる (主に print を先に扱う)
        if isinstance(node.func, ast.Name):
            name = node.func.id
            args = []
            for a in node.args:
                args += expr_to_infix_tokens(a) + [',']
            if args:
                args = args[:-1]
            return [f"{name}({ ' '.join(args) })"]
    if isinstance(node, ast.Name):
        return [node.id]
    c = const_token(node)
    if c is not None:
        return [c]
    return [ast.dump(node)]


def infix_to_rpn(tokens):
    # shunting-yard algorithm
    prec = {'+': 1, '-': 1, '*': 2, '/': 2, '%': 2,
            '=': 0, '!=':0, '>':0, '<':0, '>=':0, '<=':0}
    output = []
    stack = []
    for t in tokens:
        if t in prec or t == ',':
            if t == ',':
                # function arg separator: ignore for now
                continue
            while stack and stack[-1] != '(' and prec.get(stack[-1], 0) >= prec.get(t, 0):
                output.append(stack.pop())
            stack.append(t)
        elif t == '(':
            stack.append(t)
        elif t == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            if stack and stack[-1] == '(':
                stack.pop()
        else:
            output.append(t)
    while stack:
        output.append(stack.pop())
    return output


class Py2Ja(ast.NodeVisitor):
    def __init__(self):
        self.lines = []

    def emit(self, s):
        self.lines.append(s)

    def generic_visit(self, node):
        super().generic_visit(node)

    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Expr(self, node):
        # print(...) を とひょうじする に
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name) and node.value.func.id == 'print':
            arg = node.value.args[0] if node.value.args else ast.Constant(value='')
            infix = expr_to_infix_tokens(arg)
            rpn = infix_to_rpn(infix)
            self.emit(' '.join(rpn + ['とひょうじする']))
            return
        # その他の式: 関数呼び出しなど
        if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
            name = node.value.func.id
            args = []
            for a in node.value.args:
                infix = expr_to_infix_tokens(a)
                rpn = infix_to_rpn(infix)
                args.append(' '.join(rpn))
            self.emit(f"よびだす {name} {' '.join(args)}".strip())

    def visit_Assign(self, node):
        # 単純な名前代入のみ対応
        if len(node.targets) != 1:
            return
        target = node.targets[0]
        if isinstance(target, ast.Name):
            infix = expr_to_infix_tokens(node.value)
            rpn = infix_to_rpn(infix)
            self.emit(f"{target.id} を {' '.join(rpn)} にする")

    def visit_FunctionDef(self, node):
        args = [a.arg for a in node.args.args]
        self.emit(f"ていぎ {node.name} {' '.join(args)}")
        self.emit('[')
        for stmt in node.body:
            self.visit(stmt)
        self.emit(']')

    def visit_Call(self, node):
        # 式内の関数呼び出しを単独行にするとき
        if isinstance(node.func, ast.Name):
            name = node.func.id
            args = []
            for a in node.args:
                infix = expr_to_infix_tokens(a)
                rpn = infix_to_rpn(infix)
                args.append(' '.join(rpn))
            self.emit(f"よびだす {name} {' '.join(args)}".strip())

    def visit_If(self, node):
        infix = expr_to_infix_tokens(node.test)
        rpn = infix_to_rpn(infix)
        self.emit(f"もし {' '.join(rpn)} なら")
        self.emit('[')
        for stmt in node.body:
            self.visit(stmt)
        self.emit(']')
        if node.orelse:
            self.emit('でなければ')
            self.emit('[')
            for stmt in node.orelse:
                self.visit(stmt)
            self.emit(']')

    def visit_For(self, node):
        # range(N) のみ対応
        if isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name) and node.iter.func.id == 'range':
            args = node.iter.args
            if len(args) == 1:
                infix = expr_to_infix_tokens(args[0])
                rpn = infix_to_rpn(infix)
                self.emit(' '.join(rpn + ['かいくりかえす']))
                self.emit('[')
                for stmt in node.body:
                    self.visit(stmt)
                self.emit(']')


def convert(source):
    tree = ast.parse(source)
    p = Py2Ja()
    p.visit(tree)
    return '\n'.join(p.lines)


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
