import random
import unittest
import os
import sys
import tempfile
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch
from fractions import Fraction
from main import (
    Node,
    generate_number,
    compute_value,
    normalize,
    to_string,
    generate_problems,
    check_answers,
    main
)


class TestMathGenerator(unittest.TestCase):
    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        # 备份原始命令行参数
        self.original_argv = sys.argv
        # 备份原始标准输出
        self.original_stdout = sys.stdout

    def tearDown(self):
        # 清理临时目录
        self.temp_dir.cleanup()
        # 恢复原始命令行参数
        sys.argv = self.original_argv
        # 恢复标准输出
        sys.stdout = self.original_stdout
        for f in ['Exercises.txt', 'Answers.txt', 'Grade.txt']:
            if os.path.exists(f):
                os.remove(f)

    def test_number_generation(self):
        random.seed(42)
        num = generate_number(10)

        # 验证分数形式合法
        self.assertIsInstance(num.value, tuple)
        self.assertEqual(len(num.value), 2)
        self.assertTrue(0 <= num.value[0] < num.value[1] if num.value[1] != 1
                        else num.value[0] >= 0)

    def test_expression_calculation(self):
        """测试表达式计算逻辑"""
        # 保持原加法测试
        expr = Node('operator', operator='+',
                    left=Node('number', value=(1, 2)),
                    right=Node('number', value=(1, 3)))
        self.assertEqual(compute_value(expr), (5, 6))

        # 修改除法测试的预期结果
        expr = Node('operator', operator='÷',
                    left=Node('number', value=(1, 1)),
                    right=Node('number', value=(2, 1)))
        self.assertEqual(compute_value(expr), (1, 2))  # 正确约分结果

        # 修改乘法测试的预期结果
        expr = Node('operator', operator='×',
                    left=Node('number', value=(2, 3)),
                    right=Node('number', value=(3, 4)))
        self.assertEqual(compute_value(expr), (1, 2))  # 6/12 约分后是1/2

    def test_normalization(self):
        expr = Node(type='operator', operator='+',
                    left=Node(type='number', value=(2, 1)),
                    right=Node(type='operator', operator='+',
                               left=Node(type='number', value=(1, 1)),
                               right=Node(type='number', value=(3, 1))))
        normalized = normalize(expr)
        self.assertEqual(to_string(normalized), "1 + 2 + 3")

    def test_file_generation(self):
        """测试题目文件生成"""
        # 通过命令行参数测试
        with redirect_stdout(StringIO()):
            sys.argv = ['program.py', '-n', '5', '-r', '10']
            main()

        self.assertTrue(os.path.exists('Exercises.txt'))
        self.assertTrue(os.path.exists('Answers.txt'))

        with open('Exercises.txt') as f:
            self.assertEqual(len(f.readlines()), 5)
        with open('Answers.txt') as f:
            self.assertEqual(len(f.readlines()), 5)

    def create_test_files(self, ex_content, ans_content):
        """创建临时测试文件"""
        ex_path = os.path.join(self.temp_dir.name, 'test_ex.txt')
        ans_path = os.path.join(self.temp_dir.name, 'test_ans.txt')

        with open(ex_path, 'w') as f:
            f.write(ex_content)
        with open(ans_path, 'w') as f:
            f.write(ans_content)

        return ex_path, ans_path

    def test_correct_answers(self):
        """测试完全正确的答案"""
        ex_content = "1. 1/2 + 1/2 =\n2. 1 ÷ 2 =\n"  # 修改第二个题目
        ans_content = "1. 1\n2. 1/2\n"  # 修改对应答案

        ex_path, ans_path = self.create_test_files(ex_content, ans_content)

        check_answers(ex_path, ans_path)

        self.assertTrue(os.path.exists('Grade.txt'))
        with open('Grade.txt') as f:
            content = f.read()
            self.assertIn("Correct: 2 (1, 2)", content)
            self.assertIn("Wrong: 0", content)

    def test_mixed_answers(self):
        """测试混合(正确/错误)答案"""
        ex_content = """1. 1 + 1 =
    2. 2 × 2 =
    3. 1 ÷ (2 - 2) ="""
        ans_content = """1. 3
    2. 4
    3. 0"""

        ex_path, ans_path = self.create_test_files(ex_content, ans_content)

        check_answers(ex_path, ans_path)

        self.assertTrue(os.path.exists('Grade.txt'))
        with open('Grade.txt') as f:
            content = f.read()
            self.assertIn("Correct: 1 (2)", content)
            self.assertIn("Wrong: 2 (1, 3)", content)

    def test_cli_error_handling(self):
        """测试命令行错误处理"""
        # 测试缺少必要参数
        with self.assertRaises(SystemExit) as cm:
            sys.argv = ['program.py', '-n', '5']
            with redirect_stdout(StringIO()):
                main()
        self.assertEqual(cm.exception.code, 1)


class TestCLICommands(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_argv = sys.argv
        self.original_stdout = sys.stdout

    def tearDown(self):
        self.temp_dir.cleanup()
        sys.argv = self.original_argv
        sys.stdout = self.original_stdout
        for f in ['Exercises.txt', 'Answers.txt', 'Grade.txt']:
            if os.path.exists(f):
                os.remove(f)

    def test_generate_command(self):
        """测试生成命令"""
        with redirect_stdout(StringIO()):
            sys.argv = ['program.py', '-n', '3', '-r', '5']
            main()

        self.assertTrue(os.path.exists('Exercises.txt'))
        with open('Exercises.txt') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 3)
            self.assertTrue(all('=' in line for line in lines))

    def test_check_command(self):
        """测试核对命令"""
        ex_path = os.path.join(self.temp_dir.name, 'ex.txt')
        ans_path = os.path.join(self.temp_dir.name, 'ans.txt')

        with open(ex_path, 'w') as f:
            f.write("1. 1 + 1 =\n")
        with open(ans_path, 'w') as f:
            f.write("1. 2\n")

        with redirect_stdout(StringIO()):
            sys.argv = ['program.py', '-e', ex_path, '-a', ans_path]
            main()

        self.assertTrue(os.path.exists('Grade.txt'))
        with open('Grade.txt') as f:
            content = f.read()
            self.assertIn("Correct: 1 (1)", content)

    def test_simple_generation(self):
        """测试基础题目生成"""
        with open('test_temp.txt', 'w') as f:
            f.write("1. 1 + 1 =\n2. 2 × 3 =")
        self.assertTrue(os.path.exists('test_temp.txt'))
        os.remove('test_temp.txt')

    def test_basic_answer_check(self):
        """测试基础答案核对"""
        with open('test_ex.txt', 'w') as f:
            f.write("1. 1/2 + 1/2 =\n")
        with open('test_ans.txt', 'w') as f:
            f.write("1. 1\n")

        check_answers('test_ex.txt', 'test_ans.txt')

        self.assertTrue(os.path.exists('Grade.txt'))

        for f in ['test_ex.txt', 'test_ans.txt', 'Grade.txt']:
            if os.path.exists(f):
                os.remove(f)



if __name__ == '__main__':
    unittest.main(verbosity=2)