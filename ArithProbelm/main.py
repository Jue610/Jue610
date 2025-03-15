import argparse
import random
from fractions import Fraction
import sys
import re


class Node:
    def __init__(self, type, value=None, operator=None, left=None, right=None):
        self.type = type
        self.value = value
        self.operator = operator
        self.left = left
        self.right = right


def simplify_fraction(numerator, denominator):
    gcd = lambda a, b: a if b == 0 else gcd(b, a % b)
    common = gcd(abs(numerator), abs(denominator))
    return (numerator // common, denominator // common)


def generate_number(r):
    choice = random.choices(['natural', 'fraction', 'mixed'], weights=[3, 2, 2], k=1)[0]
    if choice == 'natural':
        num = random.randint(0, r - 1)
        return Node('number', value=simplify_fraction(num, 1))
    elif choice == 'fraction':
        denominator = random.randint(2, r)
        numerator = random.randint(1, denominator - 1)
        return Node('number', value=simplify_fraction(numerator, denominator))
    else:
        integer = random.randint(1, r - 1)
        denominator = random.randint(2, r)
        numerator = random.randint(1, denominator - 1)
        total_numerator = integer * denominator + numerator
        return Node('number', value=simplify_fraction(total_numerator, denominator))


def generate_expression(r, max_ops):
    if max_ops == 0:
        return generate_number(r)
    else:
        op = random.choice(['+', '-', '×', '÷'])
        left_ops = random.randint(0, max_ops - 1)
        right_ops = max_ops - 1 - left_ops
        left = generate_expression(r, left_ops)
        right = generate_expression(r, right_ops)
        return Node('operator', operator=op, left=left, right=right)

def compute_value(node):
    if node.type == 'number':
        return node.value
    left = compute_value(node.left)
    right = compute_value(node.right)
    ln, ld = left
    rn, rd = right
    if node.operator == '+':
        numerator = ln * rd + rn * ld
        denominator = ld * rd
    elif node.operator == '-':
        numerator = ln * rd - rn * ld
        denominator = ld * rd
        if numerator < 0:
            raise ValueError("Negative result")
    elif node.operator == '×':
        numerator = ln * rn
        denominator = ld * rd
    elif node.operator == '÷':
        if rn == 0:
            raise ValueError("Division by zero")
        numerator = ln * rd
        denominator = ld * rn
        if numerator / denominator >= 1:
            raise ValueError("Improper fraction")
    return simplify_fraction(numerator, denominator)


def to_string(node, parent_priority=0):
    if node.type == 'number':
        return fraction_to_string(*node.value)
    current_priority = 2 if node.operator in ['×', '÷'] else 1
    left_str = to_string(node.left, current_priority)
    right_str = to_string(node.right, current_priority)
    expr_str = f"{left_str} {node.operator} {right_str}"
    if current_priority < parent_priority:
        expr_str = f"({expr_str})"
    return expr_str


def fraction_to_string(numerator, denominator):
    if denominator == 1:
        return str(numerator)
    integer = numerator // denominator
    remainder = numerator % denominator
    if integer == 0:
        return f"{remainder}/{denominator}"
    else:
        return f"{integer}'{remainder}/{denominator}" if remainder != 0 else str(integer)


def normalize(node):
    if node.type == 'number':
        return node
    if node.operator in ['+', '×']:
        terms = []
        stack = [node]
        while stack:
            current = stack.pop()
            if current.type == 'operator' and current.operator == node.operator:
                stack.append(current.right)
                stack.append(current.left)
            else:
                terms.append(current)
        terms = [normalize(term) for term in terms]
        terms.sort(key=lambda x: to_string(x))
        root = terms[0]
        for term in terms[1:]:
            root = Node('operator', operator=node.operator, left=root, right=term)
        return root
    else:
        return Node('operator', operator=node.operator, left=normalize(node.left), right=normalize(node.right))
def generate_problems(n, r):
    generated = set()
    exercises = []
    answers = []
    while len(exercises) < n:
        expr = generate_expression(r, 3)
        normalized = normalize(expr)
        expr_str = to_string(normalized) + " ="
        if expr_str in generated:
            continue
        try:
            result = compute_value(expr)
            generated.add(expr_str)
            exercises.append(expr_str)
            answers.append(fraction_to_string(*result))
        except ValueError:
            pass

    # 写入题目文件
    with open('Exercises.txt', 'w') as f:
        for i, expr in enumerate(exercises, 1):
            f.write(f"{i}. {expr}\n")

    # 写入答案文件（
    with open('Answers.txt', 'w') as f:
        for i, ans in enumerate(answers, 1):
            f.write(f"{i}. {ans}\n")


def parse_answer(answer_str):
    answer_str = answer_str.strip()
    if "'" in answer_str:
        mixed, frac = answer_str.split("'", 1)
        whole = int(mixed)
        numerator, denominator = frac.split('/')
        return Fraction(whole * int(denominator) + int(numerator), int(denominator))
    elif '/' in answer_str:
        numerator, denominator = answer_str.split('/')
        return Fraction(int(numerator), int(denominator))
    else:
        return Fraction(int(answer_str), 1)


def parse_expression(expr_str):
    expr_str = expr_str.replace(' ', '').replace('×', '*').replace('÷', '/')
    tokens = re.findall(r"(\d+'\d+/\d+|\d+/\d+|\d+|\+|\-|\*|/|\(|\))", expr_str)
    converted = []
    for token in tokens:
        if token in '()+-*/':
            converted.append(token)
        else:
            converted.append(convert_number(token))
    return ''.join(converted)


def convert_number(s):
    if "'" in s:
        mixed, frac = s.split("'", 1)
        numerator, denominator = frac.split('/')
        return f"Fraction({int(mixed) * int(denominator) + int(numerator)}, {denominator})"
    elif '/' in s:
        numerator, denominator = s.split('/')
        return f"Fraction({numerator}, {denominator})"
    else:
        return f"Fraction({s}, 1)"


def evaluate_expression(py_expr):
    try:
        return eval(py_expr, {'Fraction': Fraction})
    except:
        return None


def check_answers(exercise_file, answer_file):
    correct = []
    wrong = []

    # 读取题目文件
    with open(exercise_file, 'r') as f:
        exercises = [line.strip().split('. ', 1)[1].rstrip(' =') for line in f]  # 提取 "题目内容"

    # 读取答案文件
    with open(answer_file, 'r') as f:
        answers = [line.strip().split('. ', 1)[1] for line in f]  # 提取 "答案内容"

    if len(exercises) != len(answers):
        print("错误：题目与答案数量不匹配!")
        return

    for idx in range(len(exercises)):
        expr = exercises[idx]
        user_ans = answers[idx]

        # 解析表达式并计算正确答案
        py_expr = parse_expression(expr)
        correct_ans = evaluate_expression(py_expr)
        if correct_ans is None:
            wrong.append(idx + 1)
            continue

        # 解析答案
        try:
            user_frac = parse_answer(user_ans)
        except:
            wrong.append(idx + 1)
            continue

        # 比较答案
        if correct_ans == user_frac:
            correct.append(idx + 1)
        else:
            wrong.append(idx + 1)

    # 输出结果
    with open('Grade.txt', 'w') as f:
        f.write(f"Correct: {len(correct)} ({', '.join(map(str, correct))})\n")
        f.write(f"Wrong: {len(wrong)} ({', '.join(map(str, wrong))})\n")

def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-n", type=int)
    group.add_argument("-e", type=str)
    parser.add_argument("-r", type=int)
    parser.add_argument("-a", type=str)
    args = parser.parse_args()

    if args.n is not None:
        if args.r is None:
            print("Error: -r required")
            sys.exit(1)
        generate_problems(args.n, args.r)
    elif args.e is not None:
        if args.a is None:
            print("Error: -a required")
            sys.exit(1)
        check_answers(args.e, args.a)


if __name__ == '__main__':
    main()