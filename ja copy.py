from io import StringIO
program = """"""
program = """
X を 1 にする
Y を 0 にする
もし X = 1 かつ Y = 1 なら
[
    "True" とひょうじする
]
でなければ
[
    "False" とひょうじする
]
おわる
"""

# 演算子の優先度
precedence = {
    "ではない": 3,
    "*": 2,
    "/": 2,
    "+": 1,
    "-": 1,
    ">": 0,
    "<": 0,
    "=": 0,
    "!=": 0,
    "かつ": -1,
    "または": -2,
}

def make_env():
    global env
    g_env = dict()
    env = [g_env]
    # print(f"==> env={env}")

def lookup_env(key):
    if len(env) > 1:
        local_env = env[-1]  # last element
        if key in local_env:
            return local_env[key]
    return env[0][key]

def update_env(key, value):
    env[-1][key] = value
    # print(f"==> env={env}")

def push_local():
    env.append(dict())
    # print(f"==> env={env}")

def pop_local():
    env.pop()
    # print(f"==> env={env}")

def infix_to_postfix(tokens):
    output = []
    ops = []

    for token in tokens:
        # オペランド
        if token.isalpha() or token.isdecimal() or token.startswith('"'):
            output.append(token)

        # 演算子
        else:
            while (
                ops
                and ops[-1] in precedence
                and precedence[ops[-1]] >= precedence[token]
            ):
                output.append(ops.pop())
            ops.append(token)

    while ops:
        output.append(ops.pop())

    return output

# 変数か数字か文字列かを判断する関数
def eval_id_or_literal(token):
    quote_chars = ["\"", "\'"]
    # 真偽値リテラル
    if token == "true":
        return True
    elif token == "false":
        return False
    
    # 文字列リテラル
    for quote_char in quote_chars:
        if token[0] == token[len(token) - 1] == quote_char: #クォートで囲まれているか(文字列かどうか)を判定
            return (token.rstrip(quote_char)).lstrip(quote_char) #クォート文字を外す
    
    # 数値リテラル（整数か判定）
    if token.isdecimal():
        return int(token)
    
    # 変数参照（ここを修正）
    # if token in env:    <-- 旧コード（誤り）
    #     return lookup_env(token)
    if token.isalpha():
        return lookup_env(token)
    raise NameError(f"{token}がていぎされていません")

# トークンで分断された文字列を統合する関数
def integrate_str(tokens):
    if len(tokens) == 1:
        return tokens
    quote_chars = ["\"", "\'"]
    in_quote = None
    quote_start_index = None
    quote_index = {}
    integrated_tokens = []
    integrated_str = ""
    pass_index = []
    n = 0
    for token in tokens:
        if token[0] in quote_chars:
            in_quote = True
            quote_start_index = n
        if in_quote:
            if token[len(token) - 1] in quote_chars:
                in_quote = False
                quote_index[quote_start_index] = n
        n += 1
        
    for i in range(len(tokens)):
        if i in pass_index:
            continue
        elif i in quote_index:
            n = i
            while n < quote_index[i] + 1:
                integrated_str += (tokens[n] + " ")
                pass_index.append(n)
                n += 1
            integrated_str = integrated_str.rstrip(" ")
            integrated_tokens.append(integrated_str)
        else:
            integrated_tokens.append(tokens[i])
    return integrated_tokens

INF = 1000
def find_body_end(PC):
    # assumes lines[PC] == "["
    for _ in range(INF):
        PC += 1
        if PC >= len(lines):
            raise Exception("たいおうする [ がみつかりません")
        tokens = lines[PC].split(" ")
        if tokens[0] == "]":
            return PC
        if tokens[0] == "[":
            PC = find_body_end(PC)
    raise Exception("ここにとうたつするはずがありません")

# tokenが数字の時、stackに入れて次のインデックスに行く
# tokenが演算子の時、1つインデックスを戻してそのインデックスとその次のインデックスの数値に計算を適用
def eval_exp(tokens):
    stack = [0] * 100
    sp = -1
    for token in tokens:
        # 演算
        if token == "+":
            sp = sp - 1
            stack[sp] = stack[sp] + stack[sp + 1]
        elif token == "*":
            sp = sp - 1
            stack[sp] = stack[sp] * stack[sp + 1]
        elif token == "-":
            sp = sp - 1
            stack[sp] = stack[sp] - stack[sp + 1]
        elif token == "/":
            sp = sp - 1
            stack[sp] = stack[sp] / stack[sp + 1]
        
        # 比較演算子
        elif token == "=":
            sp = sp - 1
            stack[sp] = stack[sp] == stack[sp + 1]
        elif token == ">":
            sp = sp - 1
            stack[sp] = stack[sp] > stack[sp + 1] 
        elif token == "<":
            sp = sp - 1
            stack[sp] = stack[sp] < stack[sp + 1]   
        elif token == ">=":
            sp = sp - 1
            stack[sp] = stack[sp] >= stack[sp + 1]
        elif token == "<=":
            sp = sp - 1
            stack[sp] = stack[sp] <= stack[sp + 1]
        elif token == "!=":
            sp = sp - 1
            stack[sp] = stack[sp] != stack[sp + 1]
            
        # 論理演算子
        elif token == "かつ":
            sp = sp - 1
            stack[sp] = stack[sp] and stack[sp + 1]
            
        elif token == "または":
            sp = sp - 1
            stack[sp] = stack[sp] or stack[sp + 1]
            
        elif token == "ではない":
            # Unary not: invert the top-of-stack value without changing sp
            stack[sp] = not stack[sp]
        
        # 変数参照
        else:
            sp = sp + 1
            stack[sp] = eval_id_or_literal(token)
            
    return stack[sp]

# 受け取ったトークンを評価し計算が必要であればする関数
def eval_tokens(tokens):
    if len(tokens) == 1:
        return eval_id_or_literal(tokens[0])

    postfix = infix_to_postfix(tokens)
    return eval_exp(postfix)

def execute():
    for _ in range(INF):
        if PC < 0 or PC >= len(lines):
            break
        line = lines[PC]
        cont = exec_inst(line)
        if cont is False:
            break

def last_token(tokens):
    return tokens[len(tokens)-1]

# ブロック要素のトークンを実行する関数
def exec_block():
    global PC
    line = lines[PC]
    tokens = line.split(" ")
    PC += 1
    if not tokens:
        return True
    if tokens[0] != "[":
        raise Exception("ブロックは [ ではじまるひつようがあります")
    for _ in range(INF):
        line = lines[PC]
        tokens = line.split(" ")
        if tokens and tokens[0] == "]":
            PC += 1
            break
        cont = exec_inst(line)
        if cont is False:
            return False
    return True

# 行ごとのトークンを読み取って実行する関数
# 反復はPCを保存して行う 
def exec_inst(line):
    global PC, saved_boolen
    tokens = line.split(" ")
    tokens = integrate_str(tokens)
    
    if tokens[0] == "おわる":
        return False
    
    if tokens[0] == "":  # 空行またはトークンなし
        PC += 1
    
    elif last_token(tokens) == "とひょうじする":
        result = eval_tokens(tokens[0 : len(tokens) - 1])
        if result is True:
            print("true")
        elif result is False:
            print("false")
        else:
            print(result)
        PC += 1
        
    elif last_token(tokens) == "にする":
        value = eval_tokens(tokens[2 : len(tokens) - 1])
        update_env(tokens[0], value)
        PC += 1
        
    elif last_token(tokens) == "かいくりかえす":
        PC += 1
        saved_PC = PC
        for _ in range(eval_tokens(tokens[0 : len(tokens) - 1])):
            PC = saved_PC
            cont = exec_block()
            # contにはプログラムを続けるかどうかのブール値が入る
            if cont is False:
                return False

    elif tokens[0] == "もし":
        PC += 1
        saved_PC = PC
        if eval_tokens(tokens[1 : len(tokens) - 1]) == True:
            saved_boolen = True
            cont = exec_block()
            # contにはプログラムを続けるかどうかのブール値が入る
            if cont is False:
                return False
        else:
            saved_boolen = False
            skip_block()
        
    elif tokens[0] == "でなければ":
        PC += 1
        saved_PC = PC
        if saved_boolen == False:
            cont = exec_block()
            if cont is False:
                return False
        
        elif saved_boolen == True:
            saved_boolen = None
            skip_block()
        
        else:
            raise SyntaxError
    
    elif tokens[0] == "ていぎ":
        update_env(tokens[1], ('proc', PC, tokens[2:]))
        PC = find_body_end(PC + 1)
        PC += 1
        
    elif tokens[0] == "よびだす":
        next_PC = PC + 1
        func_value = lookup_env(tokens[1])
        args = func_value[2]

        PC = func_value[1] + 1
        push_local()

        for i, arg in enumerate(args):
            update_env(arg, eval_id_or_literal(tokens[i + 2]))

        exec_block()
        pop_local()
        PC = next_PC
        
    else:
        print(f"ふめいなめいれいをスキップします:{PC}")
        PC += 1
    return True


def skip_block():
    global PC
    for _ in range(INF):
        line = lines[PC]
        tokens = line.split(" ")
        if tokens and tokens[0] == "]":
            PC += 1
            break
        PC += 1

def main():
    global PC, lines, saved_boolen
    PC = 0
    saved_boolen = None
    lines = []

    stream = StringIO(program)
    with stream as file:
        for line in file:
            lines.append(line.rstrip("\n").strip(" "))

    execute()

make_env()
update_env("true", 1)
update_env("false", 0)
main()