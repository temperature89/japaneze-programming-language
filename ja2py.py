from io import StringIO
program = ""
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
# program = """
# ていぎ fib n
# [
#     a を 1 にする
#     b を 1 にする
#     もし n 1 = なら
#     [
#         a とひょうじする
#     ]
#     もし n 2 = なら
#     [
#         b とひょうじする
#     ]
#     tmp を 0 にする
#     n 2 - かいくりかえす
#     [
#         tmp を a b + にする
#         a を b にする
#         b を tmp にする
#     ]
#     b とひょうじする
# ]
# よびだす fib 10
# おわる
# """

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

def eval_exp(tokens):
    translated_tokens = []
    for token in tokens:
        if token in ["+", "-", "*", "/", ">", "<", ">=", "<=", "!="]:
            translated_tokens.append(token)

        elif token == "=":
            translated_tokens.append("==")
            
        elif token == "かつ":
            translated_tokens.append("and")
            
        elif token == "または":
            translated_tokens.append("or")
            
        elif token == "ではない":
            translated_tokens.append("not")
            
        else:
            translated_tokens.append(token)
    return " ".join(translated_tokens)

INF = 1000
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

# 受け取ったトークンを評価し計算が必要であればする関数
def eval_tokens(tokens):
    if len(tokens) >= 2:
        result = eval_exp(tokens)
    else:
        result = tokens[0]
    return result

# 行ごとのトークンを読み取って実行する関数
# 反復はPCを保存して行う 
indent_number = 0
generated_code = []
def exec_inst(line):
    global PC, indent_number
    translated_line = ""
    translated_line += "    " * indent_number
    tokens = line.split(" ")
    tokens = integrate_str(tokens)
    
    if tokens[0] == "おわる":
        return False
    
    elif last_token(tokens) == "とひょうじする":
        result = eval_tokens(tokens[0 : len(tokens) - 1])
        translated_line += f"print({result})"
        PC += 1
        generated_code.append(translated_line)
        
    elif last_token(tokens) == "にする":
        result = eval_tokens(tokens[2 : len(tokens) - 1])
        translated_line += f"{tokens[0]} = {result}"
        PC += 1
        generated_code.append(translated_line)
        
    elif last_token(tokens) == "かいくりかえす":
        result = eval_tokens(tokens[0 : len(tokens) - 1])
        translated_line += f"for _ in range({result}):"
        PC += 1
        generated_code.append(translated_line)

    elif tokens[0] == "もし" and last_token(tokens) == "なら":
        result = eval_tokens(tokens[1 : len(tokens) - 1])
        translated_line += f"if {result}:"
        PC += 1
        generated_code.append(translated_line)
        
    elif tokens[0] == "でなければ":
        translated_line += f"else:"
        PC += 1
        generated_code.append(translated_line)
        
    elif tokens[0] == "ていぎ":
        args = ", ".join(tokens[2:])
        translated_line += f"def {tokens[1]}({args}):"
        PC += 1
        generated_code.append(translated_line)
    
    elif tokens[0] == "よびだす":
        args = ", ".join(tokens[2:])
        translated_line += f"{tokens[1]}({args})"
        PC += 1
        generated_code.append(translated_line)
        
    elif tokens[0] == "[":
        indent_number += 1
        PC += 1
        
    elif tokens[0] == "]":
        indent_number -= 1
        PC += 1
    
    elif tokens == [""]:
        PC += 1
    
    else:
        PC += 1
        print("skip unknown op")
    return True

def main():
    global PC, lines, line_number
    PC = 0
    lines = []
    line_number = 0
    stream = StringIO(program)
    with stream as file:
        for line in file:
            lines.append(line.rstrip("\n").strip(" "))
            line_number += 1
    execute()
    
    output_code = "\n".join(generated_code)
    print(output_code)
    
env = {"true" : 1, "false" : 0,}
main()