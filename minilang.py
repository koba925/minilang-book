class Scanner:
    def __init__(self, source) -> None:
        self._source = source
        self._current_position = 0

    def next_token(self):
        while self._current_char().isspace(): self._current_position += 1

        start = self._current_position
        match self._current_char():
            case "$EOF": return "$EOF"
            case c if c.isalpha() or self._current_char() == "_":
                while self._current_char().isalnum() or self._current_char() == "_":
                    self._current_position += 1
                token = self._source[start:self._current_position]
                match token:
                    case "true": return True
                    case "false": return False
                    case "null": return None
                    case _: return token
            case c if c.isnumeric():
                while self._current_char().isnumeric():
                    self._current_position += 1
                return int(self._source[start:self._current_position])
            case "!":
                self._current_position += 1
                while self._current_char() != "\n":
                    self._current_position += 1
                return self.next_token()
            case "'":
                self._current_position += 1
                while self._current_char() != "'":
                    self._current_position += 1
                self._current_position += 1
                return ["str", self._source[start + 1:self._current_position - 1]]
            case "$":
                self._current_position += 1
                if self._current_char() == "[":
                    self._current_position += 1
                return self._source[start:self._current_position]
            case _:
                self._current_position += 1
                return self._source[start:self._current_position]

    def _current_char(self):
        if self._current_position < len(self._source):
            return self._source[self._current_position]
        else:
            return "$EOF"

class Parser:
    def __init__(self, source):
        self.scanner = Scanner(source)
        self._current_token = ""
        self._next_token()

    def parse_program(self):
        program: list = ["program"]
        while self._current_token != "$EOF":
            program.append(self._parse_statement())
        return program

    def _parse_statement(self):
        match self._current_token:
            case "{": return self._parse_block()
            case "var" | "set": return self._parse_var_set()
            case "if": return self._parse_if()
            case "while": return self._parse_while()
            case "for": return self._parse_for()
            case "break": return self._parse_break()
            case "continue": return self._parse_continue()
            case "def": return self._parse_def()
            case "return": return self._parse_return()
            case "print": return self._parse_print()
            case _: return self._parse_expression_statement()

    def _parse_block(self):
        block: list = ["block"]
        self._next_token()
        while self._current_token != "}":
            block.append(self._parse_statement())
        self._next_token()
        return block

    def _parse_var_set(self):
        op = self._current_token
        self._next_token()
        target = self._parse_primary()
        assert isinstance(target, str),  f"Expected a name, found `{target}`."
        while (left := self._current_token) in ("[", "."):
            self._next_token()
            if left == "[":
                index = self._parse_expression()
                target = ["index", target, index]
                self._consume_token("]")
            else:
                index = self._current_token
                target = ["dot", target, ["str", str(index)]]
                self._next_token()
        self._consume_token("=")
        value = self._parse_expression()
        self._consume_token(";")
        return [op, target, value]

    def _parse_if(self):
        self._next_token()
        cond = self._parse_expression()
        self._check_token("{")
        conseq = self._parse_block()
        alt = ["block"]
        if self._current_token == "elif":
            alt = self._parse_if()
        elif self._current_token == "else":
            self._next_token()
            self._check_token("{")
            alt = self._parse_block()
        return ["if", cond, conseq, alt]

    def _parse_while(self):
        self._next_token()
        cond = self._parse_expression()
        self._check_token("{")
        body = self._parse_block()
        return ["while", cond, body]

    def _parse_for(self):
        self._next_token()
        var = self._parse_primary()
        assert isinstance(var, str),  f"Expected a name, found `{var}`."
        self._consume_token("in")
        col = self._parse_expression()
        self._check_token("{")
        body = self._parse_block()
        return ["for", var, col, body]

    def _parse_break(self):
        self._next_token()
        self._consume_token(";")
        return ["break"]

    def _parse_continue(self):
        self._next_token()
        self._consume_token(";")
        return ["continue"]

    def _parse_def(self):
        self._next_token()
        name = self._parse_primary()
        assert isinstance(name, str),  f"Expected a name, found `{name}`."
        params = self._parse_parameters()
        body = self._parse_block()
        return ["var", name, ["func", params, body]]

    def _parse_return(self):
        self._next_token()
        value = None
        if self._current_token != ";": value = self._parse_expression()
        self._consume_token(";")
        return ["return", value]

    def _parse_print(self):
        self._next_token()
        expr = self._parse_expression()
        self._consume_token(";")
        return ["print", expr]

    def _parse_expression_statement(self):
        expr = self._parse_expression()
        self._consume_token(";")
        return ["expr", expr]

    def _parse_expression(self):
        return self._parse_or()

    def _parse_or(self): return self._parse_binop_left(("or",), self._parse_and)
    def _parse_and(self): return self._parse_binop_left(("and",), self._parse_not)
    def _parse_not(self): return self._parse_unary(("not",), self._parse_equality)
    def _parse_equality(self): return self._parse_binop_left(("=", "#"), self._parse_comparison)
    def _parse_comparison(self): return self._parse_binop_left(("<", ">"), self._parse_add_sub)
    def _parse_add_sub(self): return self._parse_binop_left(("+", "-"), self._parse_mult_div_mod)
    def _parse_mult_div_mod(self): return self._parse_binop_left(("*", "/", "%"), self._parse_unary_minus)
    def _parse_unary_minus(self): return self._parse_unary(("-",), self._parse_power)

    def _parse_binop_left(self, ops, sub_element):
        result = sub_element()
        while (op := self._current_token) in ops:
            self._next_token()
            result = [op, result, sub_element()]
        return result

    def _parse_unary(self, ops, sub_element):
        if (op := self._current_token) not in ops: return sub_element()
        self._next_token()
        return [op, self._parse_unary(ops, sub_element)]

    def _parse_power(self):
        power = self._parse_call_index_dot()
        if self._current_token != "^": return power
        self._next_token()
        return ["^", power, self._parse_power()]

    def _parse_call_index_dot(self):
        parens = {"(": ")", "[": "]", ".": None}

        result = self._parse_primary()
        while isinstance((left := self._current_token), str) and left in parens:
            self._next_token()
            if left == ".":
                result = ["dot", result, ["str", str(self._current_token)]]
                self._next_token()
            else:
                args = []
                while self._current_token != parens[left]:
                    args.append(self._parse_expression())
                    if self._current_token != parens[left]:
                        self._consume_token(",")
                if left == "(": result = [result] + args
                else: result = ["index", result, args[0]]
                self._consume_token(parens[left])
        return result

    def _parse_primary(self):
        match self._current_token:
            case "(":
                self._next_token()
                exp = self._parse_expression()
                self._consume_token(")")
                return exp
            case "[": return self._parse_array()
            case "$[": return self._parse_dic()
            case "func": return self._parse_func()
            case int(value) | bool(value) | str(value):
                self._next_token()
                return value
            case ["str", s]:
                self._next_token()
                return ["str", s]
            case None:
                self._next_token()
                return None
            case unexpected: assert False, f"Unexpected token `{unexpected}`."

    def _parse_array(self):
        self._next_token()
        array = []
        while self._current_token != "]":
            array.append(self._parse_expression())
            if self._current_token != "]":
                self._consume_token(",")
        self._consume_token("]")
        return ["arr", array]

    def _parse_dic(self):
        self._next_token()
        dic = {}
        while self._current_token != "]":
            index = self._current_token
            assert isinstance(index, str), f"Name expected, found `{index}`."
            self._next_token()
            self._consume_token(":")
            val = self._parse_expression()
            dic[index] = val
            if self._current_token != "]":
                self._consume_token(",")
        self._consume_token("]")
        return ["dic", dic]

    def _parse_func(self):
        self._next_token()
        params = self._parse_parameters()
        body = self._parse_block()
        return ["func", params, body]

    def _parse_parameters(self):
        self._consume_token("(")
        params = []
        while self._current_token != ")":
            param = self._current_token
            assert isinstance(param, str), f"Name expected, found `{param}`."
            self._next_token()
            params.append(param)
            if self._current_token != ")":
                self._consume_token(",")
        self._consume_token(")")
        return params

    def _consume_token(self, expected_token):
        self._check_token(expected_token)
        return self._next_token()

    def _check_token(self, expected_token):
        assert self._current_token == expected_token, \
               f"Expected `{expected_token}`, found `{self._current_token}`."

    def _next_token(self):
        self._current_token = self.scanner.next_token()
        return self._current_token

class Break(Exception): pass
class Continue(Exception): pass
class Return(Exception):
    def __init__(self, value): self.value = value

class Environment:
    def __init__(self, parent:"Environment | None"=None):
        self._values = {}
        self._parent = parent

    def define(self, name, value):
        assert name not in self._values, f"`{name}` already defined."
        self._values[name] = value

    def assign(self, name, value):
        if name in self._values: self._values[name] = value
        elif self._parent is not None: self._parent.assign(name, value)
        else: assert False, f"`{name}` not defined."

    def get(self, name):
        if name in self._values: return self._values[name]
        if self._parent is not None: return self._parent.get(name)
        assert False, f"`{name}` not defined."

    def list(self):
        if self._parent is None: return [self._values]
        return self._parent.list() + [self._values]

import operator
import functools

class Evaluator:
    def __init__(self):
        self.output = []
        self._env = Environment()
        self._env.define("less", lambda a, b: a < b)
        self._env.define("print_env", self._print_env)
        self._env.define("push", lambda a, v: a[1].append(v))
        self._env.define("pop", lambda a: a[1].pop())
        self._env.define("len", lambda a: len(a) if isinstance(a, str) else len(a[1]))
        self._env.define("keys", lambda a: ["arr", [k for k in a[1].keys() if not k.startswith("__")]])
        self._env.define("to_print", lambda a: self._to_print(a))

    def _print_env(self):
        for values in self._env.list():
            print({ k: self._to_print(v) for k, v in values.items() })

    def eval_program(self, program):
        self.output = []
        try:
            match program:
                case ["program", *statements]:
                    for statement in statements:
                        self._eval_statement(statement)
                case unexpected: assert False, f"Internal Error at `{unexpected}`."
        except Return: assert False, "Return at top level."
        except Break: assert False, "Break at top level."
        except Continue: assert False, "Continue at top level."

    def _eval_statement(self, statement):
        match statement:
            case ["block", *statements]: self._eval_block(statements)
            case ["var", name, value]: self._eval_var(name, value)
            case ["set", name, value]: self._eval_set(name, value)
            case ["if", cond, conseq, alt]: self._eval_if(cond, conseq, alt)
            case ["while", cond, body]: self._eval_while(cond, body)
            case ["for", var, col, body]: self._eval_for(var, col, body)
            case ["break"]: raise Break()
            case ["continue"]: raise Continue()
            case ["return", value]: raise Return(self._eval_expr(value))
            case ["print", expr]: self._eval_print(expr)
            case ["expr", expr]: self._eval_expr(expr)
            case unexpected: assert False, f"Internal Error at `{unexpected}`."

    def _eval_block(self, statements):
        parent_env = self._env
        self._env = Environment(parent_env)
        try:
            for statement in statements:
                self._eval_statement(statement)
        finally:
            self._env = parent_env

    def _eval_var(self, target, value):
        self._env.define(target, self._eval_expr(value))

    def _eval_set(self, target, value):
        match target:
            case ["index", expr, index] | ["dot", expr, index]:
                match [self._eval_expr(expr), self._eval_expr(index)]:
                    case [["arr", values], int(ind)] | [["dic", values], str(ind)]:
                        values[ind] = self._eval_expr(value)
                        return
            case str(name):
                self._env.assign(target, self._eval_expr(value))
                return
        assert False, f"Illegal assignment."

    def _eval_if(self, cond, conseq, alt):
        if self._eval_expr(cond):
            self._eval_statement(conseq)
        else:
            self._eval_statement(alt)

    def _eval_while(self, cond, body):
        while self._eval_expr(cond):
            try: self._eval_statement(body)
            except Continue: continue
            except Break: break

    def _eval_for(self, var, col, body):
        parent_env = self._env
        self._env = Environment(parent_env)
        self._env.define(var, None)
        match self._eval_expr(col):
            case ["arr", value] | str(value): col = value
            case ["dic", value]: col = value.keys()
        for val in col:
            self._env.assign(var, val)
            try: self._eval_statement(body)
            except Continue: continue
            except Break: break
        self._env = parent_env

    def _eval_print(self, expr):
        self.output.append(self._to_print(self._eval_expr(expr)))

    def _to_print(self, value):
        match value:
            case bool(b): return "true" if b else "false"
            case int(i): return str(i)
            case str(s): return s
            case None: return "null"
            case v if callable(v): return "<builtin>"
            case ["func", *_]: return "<func>"
            case ["arr", values]:
                return "[" + ", ".join([self._to_print(value) for value in values]) + "]"
            case ["dic", values]:
                return "$[" + ", ".join([
                    self._to_print(key) + ": " + self._to_print(values[key])
                    for key in values
                ]) + "]"
            case unexpected: assert False, f"`{unexpected}` unexpected in `_to_print`."

    def _eval_expr(self, expr):
        match expr:
            case int(value) | bool(value): return value
            case None: return None
            case ["str", s]: return s
            case ["arr", exprs]:
                return ["arr", [self._eval_expr(expr) for expr in exprs]]
            case ["dic", exprs]:
                return ["dic", {key: self._eval_expr(exprs[key]) for key in exprs}]
            case ["index", expr, index]:
                return self._eval_index(self._eval_expr(expr), self._eval_expr(index))
            case ["dot", left, right]:
                return self._eval_dot(self._eval_expr(left), self._eval_expr(right))
            case str(name): return self._eval_variable(name)
            case ["func", param, body]: return ["func", param, body, self._env]
            case ["^", a, b]: return self._eval_expr(a) ** self._eval_expr(b)
            case ["-", a]: return -self._eval_expr(a)
            case ["*", a, b]: return self._eval_mul(self._eval_expr(a), self._eval_expr(b))
            case ["/", a, b]: return self._div_mod_in(operator.floordiv, self._eval_expr(a), self._eval_expr(b))
            case ["%", a, b]: return self._div_mod_in(operator.mod, self._eval_expr(a), self._eval_expr(b))
            case ["+", a, b]: return self._eval_plus(self._eval_expr(a), self._eval_expr(b))
            case ["-", a, b]: return self._eval_expr(a) - self._eval_expr(b)
            case ["<", a, b]: return self._eval_expr(a) < self._eval_expr(b)
            case [">", a, b]: return self._eval_expr(a) > self._eval_expr(b)
            case ["=", a, b]: return self._eval_expr(a) == self._eval_expr(b)
            case ["#", a, b]: return self._eval_expr(a) != self._eval_expr(b)
            case ["not", a]: return not self._eval_expr(a)
            case ["and", a, b]: return self._eval_expr(a) and self._eval_expr(b)
            case ["or", a, b]: return self._eval_expr(a) or self._eval_expr(b)
            case [func, *args]:
                return self._apply(self._eval_expr(func),
                                   [self._eval_expr(arg) for arg in args])
            case unexpected: assert False, f"Internal Error at `{unexpected}`."

    def _eval_index(self, col, index):
        match col:
            case ["arr", col] | ["dic", col] | str(col):
                return col[index]
            case _:
                assert False, "Index must be applied to an array, a dic or a string."

    def _eval_dot(self, left, right, this = None):
        def ufcs(right):
            match right:
                case ["func", parameters, body, env]:
                    env = Environment(env)
                    env.define(parameters[0], this)
                    return ["func", parameters[1:], body, env]
                case builtin if callable(builtin):
                    return functools.partial(builtin, left)
                case _:
                    return right

        if this is None: this = left
        match left:
            case ["dic", dic]:
                if right not in dic:
                    if not "__proto__" in dic:
                        return ufcs(self._env.get(right))
                    return self._eval_dot(dic["__proto__"], right, this)
                return ufcs(dic[right])
            case _:
                return ufcs(self._env.get(right))

    def _eval_mul(self, a, b):
        match [a, b]:
            case [["arr", values], int(times)]:
                return ["arr", values * times]
        return a * b

    def _eval_plus(self, a, b):
        match [a, b]:
            case [["arr", values_a], ["arr", values_b]]:
                return ["arr", values_a + values_b]
        return a + b

    def _div_mod_in(self, op, a, b):
        match b:
            case ["arr", col] | ["dic", col] | str(col):
                return a in col
            case _:
                assert b != 0, f"Division by zero."
                return op(a, b)

    def _apply(self, func, args):
        if callable(func): return func(*args)

        [_, parameters, body, env] = func
        parent_env = self._env
        self._env = Environment(env)
        for param, arg in zip(parameters, args): self._env.define(param, arg)
        value = None
        try:
            self._eval_statement(body)
        except Break: assert False, "Break outside loop."
        except Continue: assert False, "Continue outside loop."
        except Return as ret: value = ret.value
        finally:
            self._env = parent_env
        return value

    def _eval_variable(self, name):
        return self._env.get(name)

if __name__ == "__main__":
    import sys

    evaluator = Evaluator()
    while True:
        print("Input source and enter Ctrl+D:")
        if (source := sys.stdin.read()) == "": break

        print("Output:")
        try:
            ast = Parser(source).parse_program()
            print(ast)
            evaluator.eval_program(ast)
            print(*evaluator.output, sep="\n")
        except AssertionError as e:
            print("Error:", e)
