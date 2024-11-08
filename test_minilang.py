import unittest

from minilang import Parser, Evaluator

def get_ast(source): return Parser(source).parse_program()

def get_output(source):
    evaluator = Evaluator()
    evaluator.eval_program(Parser(source).parse_program())
    return evaluator.output

def get_error(source):
    try: output = get_output(source)
    except AssertionError as e: return str(e)
    else: return f"Error not occurred. out={output}"

class TestMinilang(unittest.TestCase):
    def test_print(self):
        self.assertEqual(get_ast(""), ["program"])
        self.assertEqual(get_output(""), [])

        self.assertEqual(get_ast(" \t\n"), ["program"])
        self.assertEqual(get_output(" \t\n"), [])

        self.assertEqual(get_ast("print 123;"), ["program", ["print", 123]])
        self.assertEqual(get_output("print 123;"), ["123"])

        self.assertEqual(get_ast("print 5; print 6; print 7;"), \
                         ["program", ["print", 5], ["print", 6], ["print", 7]])
        self.assertEqual(get_output("print 5; print 6; print 7;"), ["5", "6", "7"])
        self.assertEqual(get_output("  print  5  ;\n\tprint  6  ;  \n  print\n7\n\n ; \n"), ["5", "6", "7"])

        self.assertEqual(get_error("prin 5;"), "Expected `;`, found `5`.")
        self.assertEqual(get_error("print 5:"), "Expected `;`, found `:`.")
        self.assertEqual(get_error("print 5"), "Expected `;`, found `$EOF`.")
        self.assertEqual(get_error("print 5; prin 6;"), "Expected `;`, found `6`.")

    def test_add_sum(self):
        self.assertEqual(get_output("print 5 + 6;"), ["11"])
        self.assertEqual(get_ast("print 5 + 6 + 7;"), ["program", ["print", ["+", ["+", 5, 6], 7]]])
        self.assertEqual(get_output("print 5 + 6 + 7;"), ["18"])

        self.assertEqual(get_output("print 18 - 7;"), ["11"])
        self.assertEqual(get_ast("print 18 - 7 - 6;"), ["program", ["print", ["-", ["-", 18, 7], 6]]])
        self.assertEqual(get_output("print 18 - 7 - 6;"), ["5"])

    def test_mul_div_mod(self):
        self.assertEqual(get_output("print 5 * 6;"), ["30"])
        self.assertEqual(get_ast("print 5 * 6 * 7;"), ["program", ["print", ["*", ["*", 5, 6], 7]]])
        self.assertEqual(get_output("print 5 * 6 * 7;"), ["210"])

        self.assertEqual(get_output("print 210 / 7;"), ["30"])
        self.assertEqual(get_output("print 211 / 7;"), ["30"])
        self.assertEqual(get_ast("print 210 / 7 / 6;"), ["program", ["print", ["/", ["/", 210, 7], 6]]])
        self.assertEqual(get_output("print 210 / 7 / 6;"), ["5"])
        self.assertEqual(get_error("print 5 / 0;"), "Division by zero.")

        self.assertEqual(get_output("print 62 % 9;"), ["8"])
        self.assertEqual(get_ast("print 62 % 9 % 3;"), ["program", ["print", ["%", ["%", 62, 9], 3]]])
        self.assertEqual(get_output("print 62 % 9 % 3;"), ["2"])
        self.assertEqual(get_error("print 5 % 0;"), "Division by zero.")

        self.assertEqual(get_ast("print 5 * 6 + 7;"), ["program", ["print", ["+", ["*", 5, 6], 7]]])
        self.assertEqual(get_ast("print 5 + 6 * 7;"), ["program", ["print", ["+", 5, ["*", 6, 7]]]])
        self.assertEqual(get_ast("print 5 / 6 + 7;"), ["program", ["print", ["+", ["/", 5, 6], 7]]])
        self.assertEqual(get_ast("print 5 + 6 / 7;"), ["program", ["print", ["+", 5, ["/", 6, 7]]]])
        self.assertEqual(get_ast("print 5 % 6 + 7;"), ["program", ["print", ["+", ["%", 5, 6], 7]]])
        self.assertEqual(get_ast("print 5 + 6 % 7;"), ["program", ["print", ["+", 5, ["%", 6, 7]]]])

    def test_parens(self):
        self.assertEqual(get_ast("print (5 + 6) * 7;"), ["program", ["print", ["*", ["+", 5, 6], 7]]])
        self.assertEqual(get_output("print (5 + 6) * 7;"), ["77"])
        self.assertEqual(get_ast("print 5 * (6 + 7);"), ["program", ["print", ["*", 5, ["+", 6, 7]]]])
        self.assertEqual(get_output("print 5 * (6 + 7);"), ["65"])

    def test_power(self):
        self.assertEqual(get_output("print 2 ^ 3;"), ["8"])
        self.assertEqual(get_ast("print 2 ^ 2 ^ 3;"), ["program", ["print", ["^", 2, ["^", 2, 3]]]])
        self.assertEqual(get_output("print 2 ^ 2 ^ 3;"), ["256"])
        self.assertEqual(get_output("print 5 * 2 ^ 3;"), ["40"])

    def test_boolean(self):
        self.assertEqual(get_output("print true; print false;"), ["true", "false"])

    def test_equality(self):
        self.assertEqual(get_output("print 5 + 7 = 3 * 4;"), ["true"])
        self.assertEqual(get_output("print 5 + 6 = 3 * 4;"), ["false"])
        self.assertEqual(get_output("print 5 + 7 # 3 * 4;"), ["false"])
        self.assertEqual(get_output("print 5 + 6 # 3 * 4;"), ["true"])
        self.assertEqual(get_output("print true = true;"), ["true"])
        self.assertEqual(get_output("print true = false;"), ["false"])
        self.assertEqual(get_output("print true # true;"), ["false"])
        self.assertEqual(get_output("print true # false;"), ["true"])
        self.assertEqual(get_ast("print 5 = 6 = true;"), ["program", ["print", ["=", ["=", 5, 6], True]]])
        self.assertEqual(get_output("print 5 = 6 = true;"), ["false"])

    def test_variable(self):
        self.assertEqual(get_output("var aa = 5 + 6; var bb = 7 * 8; print aa + bb;"), ["67"])
        self.assertEqual(get_output("var a = 5; print a; set a = a + 6; print a;"), ["5", "11"])
        self.assertEqual(get_output("var a = true; print a; set a = false; print a;"), ["true", "false"])
        self.assertEqual(get_error("var 1 = 1;"), "Expected a name, found `1`.")
        self.assertEqual(get_error("var a = 1; var a = 1;"), "`a` already defined.")
        self.assertEqual(get_error("set a;"), "Expected `=`, found `;`.")
        self.assertEqual(get_error("set a + 1 = 1;"), "Expected `=`, found `+`.")
        self.assertEqual(get_error("set a = 1;"), "`a` not defined.")
        self.assertEqual(get_error("print a;"), "`a` not defined.")

    def test_scope(self):
        self.assertEqual(get_output("var a = 5 + 6; { var a = 7; print a; } print a;"), ["7", "11"])
        self.assertEqual(get_output("var a = 5 + 6; { set a = 7; print a; } print a;"), ["7", "7"])
        self.assertEqual(get_error("var a = 5 + 6; { var b = 7; print b; } print b;"), "`b` not defined.")
        self.assertEqual(get_error("{ print 1;"), "Expected `;`, found `$EOF`.")

    def test_if(self):
        self.assertEqual(get_ast("if 5 = 5 { print 6; }"), \
                         ["program", ["if", ["=", 5, 5], ["block", ["print", 6]], ["block"]]])
        self.assertEqual(get_output("if 5 = 5 { print 6; }"), ["6"])
        self.assertEqual(get_output("if 5 # 5 { print 6; }"), [])

        self.assertEqual(get_output("if true { if true { print 6; } }"), ["6"])
        self.assertEqual(get_output("if true { if false { print 6; } }"), [])

        self.assertEqual(get_error("if true print 5;"), "Expected `{`, found `print`.")

    def test_else(self):
        self.assertEqual(get_ast("if 5 = 5 { print 6; } else { print 7; }"), \
                         ["program", ["if", ["=", 5, 5], ["block", ["print", 6]], ["block", ["print", 7]]]])
        self.assertEqual(get_output("if 5 = 5 { print 6; } else { print 7; }"), ["6"])
        self.assertEqual(get_output("if 5 # 5 { print 6; } else { print 7; }"), ["7"])

        self.assertEqual(get_output("if true { print 6; } else { if true { print 7; } else {print 8;} }"), ["6"])
        self.assertEqual(get_output("if false { print 6; } else { if true { print 7; } else {print 8;} }"), ["7"])
        self.assertEqual(get_output("if false { print 6; } else { if false { print 7; } else {print 8;} }"), ["8"])

        self.assertEqual(get_error("if true { print 5; } else print 6;"), "Expected `{`, found `print`.")

    def test_elif(self):
        self.assertEqual(get_ast("if 5 # 5 { print 5; } elif 5 = 5 { print 6; } else { print 7; }"), \
                         ["program", ["if", ["#", 5, 5], ["block", ["print", 5]], ["if", ["=", 5, 5], ["block", ["print", 6]], ["block", ["print", 7]]]]])
        self.assertEqual(get_output("if 5 # 5 { print 5; } elif 5 = 5 { print 6; } else { print 7; }"), ["6"])

        self.assertEqual(get_output("if true { print 5; } elif true { print 6; } elif true { print 7; } else { print 8; }"), ["5"])
        self.assertEqual(get_output("if false { print 5; } elif true { print 6; } elif true { print 7; } else { print 8; }"), ["6"])
        self.assertEqual(get_output("if false { print 5; } elif false { print 6; } elif true { print 7; } else { print 8; }"), ["7"])
        self.assertEqual(get_output("if false { print 5; } elif false { print 6; } elif false { print 7; } else { print 8; }"), ["8"])
        self.assertEqual(get_output("if false { print 5; } elif false { print 6; } elif false { print 7; }"), [])

    def test_while(self):
        self.assertEqual(get_output("""
                                    var i = 0;
                                    while i # 3 {
                                        print i;
                                        set i = i + 1;
                                    }
                                    """), ["0", "1", "2"])
        self.assertEqual(get_error("while true print 2;"), "Expected `{`, found `print`.")

    def test_fib(self):
        self.assertEqual(get_output("""
                                    var i = 0; var a = 1; var b = 0; var tmp = 0;
                                    while i # 5 {
                                        print a;
                                        set tmp = a; set a = a + b; set b = tmp;
                                        set i = i + 1;
                                    }
                                    """), ["1", "1", "2", "3", "5"])

    def test_builtin_function(self):
        self.assertEqual(get_ast("print less(5 + 6, 5 * 6);"),
                         ["program", ["print", ["less", ["+", 5, 6], ["*", 5, 6]]]])
        self.assertEqual(get_output("print less(5 + 6, 5 * 6);"), ["true"])
        self.assertEqual(get_output("print less(5 * 6, 5 + 6);"), ["false"])
        self.assertEqual(get_output("print less;"), ["<builtin>"])
        self.assertEqual(get_error("print less(5 * 6 7);"), "Expected `,`, found `7`.")

    def test_gcd(self):
        self.assertEqual(get_output("""
                                    var a = 36; var b = 24; var tmp = 0;
                                    while b # 0 {
                                        if less(a, b) {
                                            set tmp = a; set a = b; set b = tmp;
                                        }
                                        set a = a - b;
                                    }
                                    print a;
                                    """), ["12"])

    def test_expression_statement(self):
        self.assertEqual(get_ast("5 + 6;"), ["program", ["expr", ["+", 5, 6]]])
        self.assertEqual(get_output("5 + 6;"), [])

    def test_user_function_type(self):
        self.assertEqual(get_ast("func() {};"), \
                         ["program", ["expr", ["func", [], ["block"]]]])
        self.assertEqual(get_output("print func() {};"), ["<func>"])

        self.assertEqual(get_ast("func(a, b) { a + b; };"), \
                         ["program", ["expr", ["func", ["a", "b"], ["block", ["expr", ["+", "a", "b"]]]]]])
        self.assertEqual(get_output("print func(a, b) { a + b; };"), ["<func>"])

    def test_user_function_call(self):
        self.assertEqual(get_output("print func() {}();"), ["null"])
        self.assertEqual(get_output("func() { print 5; }();"), ["5"])
        self.assertEqual(get_output("func(a, b) { print a + b; }(5, 6);"), ["11"])
        self.assertEqual(get_output("""
                                    var sum = func(a, b) {
                                        print a + b;
                                    };
                                    sum(5, 6); sum(7, 8);
                                    """), ["11", "15"])

    def test_fib2(self):
        self.assertEqual(get_output("""
                                    var fib = func(n) {
                                        var i = 0; var a = 1; var b = 0; var tmp = 0;
                                        while i # n {
                                            print a;
                                            set tmp = a; set a = a + b; set b = tmp;
                                            set i = i + 1;
                                        }
                                    };
                                    fib(3); fib(5);
                                    """), ["1", "1", "2", "1", "1", "2", "3", "5"])

    def test_return(self):
        self.assertEqual(get_output("print func() { return; }();"), ["null"])
        self.assertEqual(get_output("print func() { return 5; }();"), ["5"])
        self.assertEqual(get_output("print func(a, b) { return a + b; }(5, 6);"), ["11"])
        self.assertEqual(get_output("func() { print 5; return; print 6; }();"), ["5"])
        self.assertEqual(get_output("""
                                    var sum = func(a, b) {
                                        return a + b;
                                    };
                                    print sum(5, 6);
                                    print sum(7, 8);
                                    """), ["11", "15"])
        self.assertEqual(get_output("""
                                    var nums_to_n = func(n) {
                                        var k = 1;
                                        while true {
                                            print k;
                                            if k = n { return; }
                                            set k = k + 1;
                                        }
                                    };
                                    nums_to_n(5);
                                    """), ["1", "2", "3", "4", "5"])
        self.assertEqual(get_output("print func() { return less; }();"), ["<builtin>"])
        self.assertEqual(get_output("print func() { return less; }()(5, 6);"), ["true"])
        self.assertEqual(get_output("print func() { return func(a) { return a + 5; }; }()(6);"), ["11"])
        self.assertEqual(get_error("return;"), "Return at top level.")

    def test_gcd2(self):
        self.assertEqual(get_output("""
                                    var gcd = func(a, b) {
                                        var tmp = 0;
                                        while b # 0 {
                                            if less(a, b) {
                                                set tmp = a; set a = b; set b = tmp;
                                            }
                                            set a = a - b;
                                        }
                                        return a;
                                    };
                                    print gcd(36, 12);
                                    """), ["12"])

    def test_fib3(self):
        self.assertEqual(get_output("""
                                    var fib = func(n) {
                                        if n = 1 { return 1; }
                                        if n = 2 { return 1; }
                                        return fib(n - 1) + fib(n - 2);
                                    };
                                    print fib(6);
                                    """), ["8"])

    def test_even_odd(self):
        self.assertEqual(get_output("""
                                    var is_even = func(a) { if a = 0 { return true; } else { return is_odd(a - 1); } };
                                    var is_odd = func(a) { if a = 0 { return false; } else { return is_even(a - 1); } };
                                    print is_even(5);
                                    print is_odd(5);
                                    print is_even(6);
                                    print is_odd(6);
                                    """), ["false", "true", "true", "false"])

    def test_closure(self):
        self.assertEqual(get_error("print func(a) { return a + b; }(5);"), "`b` not defined.")
        self.assertEqual(get_output("var b = 6; print func(a) { return a + b; } (5);"), ["11"])
        self.assertEqual(get_output("""
                                    var fa = func(a) { return a + b; };
                                    var b = 6;
                                    print fa(5);
                                    """), ["11"])
        self.assertEqual(get_error("""
                                   var fa = func(a) { return a + b; };
                                   var fb = func() {
                                       var b = 6;
                                       return fa(5);
                                   };
                                   print fb();
                                   """), "`b` not defined.")
        self.assertEqual(get_output("""
                                    var fb = func() {
                                        var b = 6;
                                        return func(a) { return a + b; };
                                    };
                                    var fa = fb();
                                    print fa(5);
                                    """), ["11"])
        self.assertEqual(get_output("""
                                    var make_adder = func(a) {
                                        return func(b) { return a + b; };
                                    };
                                    var a = 5;
                                    var add_6 = make_adder(6);
                                    print add_6(7);
                                    """), ["13"])
    def test_def(self):
        self.assertEqual(get_ast("def sum(a, b) { return a + b; }"), \
                         ["program", ["var", "sum", ["func", ["a", "b"], ["block", ["return", ["+", "a", "b"]]]]]])
        self.assertEqual(get_output("""
                                    def sum(a, b) {
                                        return a + b;
                                    }
                                    print sum(2, 3);
                                    print sum(4, 5);
                                    """), ["5", "9"])

    def test_gcd3(self):
        self.assertEqual(get_output("""
                                    def gcd(a, b) {
                                        var tmp = 0;
                                        while b # 0 {
                                            if less(a, b) {
                                                set tmp = a; set a = b; set b = tmp;
                                            }
                                            set a = a - b;
                                        }
                                        return a;
                                    }
                                    print gcd(36, 12);
                                    """), ["12"])

    def test_fib4(self):
        self.assertEqual(get_output("""
                                    def fib(n) {
                                        if n = 1 { return 1; }
                                        if n = 2 { return 1; }
                                        return fib(n - 1) + fib(n - 2);
                                    }
                                    print fib(6);
                                    """), ["8"])

    def test_comment(self):
        self.assertEqual(get_ast("""
                                 print 5; ! print 6;
                                 ! print 7;
                                 print 8; ! print 9;
                                 """), \
                         get_ast("print 5; print 8;"))
        self.assertEqual(get_output("""
                                    print 5; ! print 6;
                                    ! print 7;
                                    print 8; ! print 9;
                                    """), ["5", "8"])

    def test_comparison(self):
        self.assertEqual(get_ast("5 + 6 < 5 * 6;"),
                         ["program", ["expr", ["<", ["+", 5, 6], ["*", 5, 6]]]])
        self.assertEqual(get_ast("5 < 6 = 7 > 8;"),
                         ["program", ["expr", ["=", ["<", 5, 6], [">", 7, 8]]]])
        self.assertEqual(get_output("print 5 < 6;"), ["true"])
        self.assertEqual(get_output("print 5 < 5;"), ["false"])
        self.assertEqual(get_output("print 6 < 5;"), ["false"])
        self.assertEqual(get_output("print 5 > 6;"), ["false"])
        self.assertEqual(get_output("print 5 > 5;"), ["false"])
        self.assertEqual(get_output("print 6 > 5;"), ["true"])

    def test_gcd4(self):
        self.assertEqual(get_output("""
                                    def gcd(a, b) {
                                        var tmp = 0;
                                        while b > 0 {
                                            if a < b {
                                                set tmp = a; set a = b; set b = tmp;
                                            }
                                            set a = a - b;
                                        }
                                        return a;
                                    }
                                    print gcd(36, 12);
                                    """), ["12"])

    def test_gcd5(self):
        self.assertEqual(get_output("""
                                    def gcd(a, b) {
                                        var tmp = 0;
                                        while b > 0 {
                                            set tmp = b; set b = a % b; set a = tmp;
                                        }
                                        return a;
                                    }
                                    print gcd(36, 24);
                                    """), ["12"])

    def test_and_or(self):
        self.assertEqual(get_ast("5 # 6 or 7 # 8 and 9 = 5;"),
                         ["program", ["expr", ["or", ["#", 5, 6], ["and", ["#", 7, 8], ["=", 9, 5]]]]])
        self.assertEqual(get_output("print true and true;"), ["true"])
        self.assertEqual(get_output("print true and false;"), ["false"])
        self.assertEqual(get_output("print false and 1 / 0;"), ["false"])
        self.assertEqual(get_output("print true or 1 / 0;"), ["true"])
        self.assertEqual(get_output("print false or true;"), ["true"])
        self.assertEqual(get_output("print false or false;"), ["false"])

    def test_fib5(self):
        self.assertEqual(get_output("""
                                    def fib(n) {
                                        if n = 1 or n = 2 { return 1; }
                                        return fib(n - 1) + fib(n - 2);
                                    }
                                    print fib(6);
                                    """), ["8"])

    def test_not(self):
        self.assertEqual(get_ast("not true or false;"), ["program", ["expr", ["or", ["not", True], False]]])
        self.assertEqual(get_ast("not true = false;"), ["program", ["expr", ["not", ["=", True, False]]]])
        self.assertEqual(get_ast("not not true;"), ["program", ["expr", ["not", ["not", True]]]])
        self.assertEqual(get_output("print not true;"), ["false"])
        self.assertEqual(get_output("print not false;"), ["true"])
        self.assertEqual(get_output("print not not true;"), ["true"])

    def test_unary_minus(self):
        self.assertEqual(get_ast("- 5 ^ 6;"), ["program", ["expr", ["-", ["^", 5, 6]]]])
        self.assertEqual(get_ast("- 5 * 6;"), ["program", ["expr", ["*", ["-", 5], 6]]])
        self.assertEqual(get_ast("--5;"), ["program", ["expr", ["-", ["-", 5]]]])
        self.assertEqual(get_output("print -5 * 6;"), ["-30"])
        self.assertEqual(get_output("print 5--6;"), ["11"])
        self.assertEqual(get_output("print 5---6;"), ["-1"])

    def test_break(self):
        self.assertEqual(get_output("""
                                    var n = 5;
                                    while true {
                                        if n = 8 { break; }
                                        print n;
                                        set n = n + 1;
                                    }
                                    print 10;
                                    """), ["5", "6", "7", "10"])
        self.assertEqual(get_error("break;"), "Break at top level.")
        self.assertEqual(get_error("func() { break; }();"), "Break outside loop.")

    def test_continue(self):
        self.assertEqual(get_output("""
                                    var n = 5;
                                    while n < 8 {
                                        set n = n + 1;
                                        if n = 7 { continue; }
                                        print n;
                                    }
                                    print 10;
                                    """), ["6", "8", "10"])
        self.assertEqual(get_error("continue;"), "Continue at top level.")
        self.assertEqual(get_error("func() { continue; } ();"), "Continue outside loop.")

    def test_null(self):
        self.assertEqual(get_output("print null;"), ["null"])
        self.assertEqual(get_output("print null = null;"), ["true"])
        self.assertEqual(get_output("print null = 0;"), ["false"])

    def test_array(self):
        self.assertEqual(get_output("print [];"), ["[]"])
        self.assertEqual(get_output("print [1 + 2, 3 * 4];"), ["[3, 12]"])
        self.assertEqual(get_output("print [1, true, false, less, func () {}, null, []];"),
                         ["[1, true, false, <builtin>, <func>, null, []]"])
        self.assertEqual(get_output("var a = [1, 2]; print a;"), ["[1, 2]"])

        self.assertEqual(get_output("print [] = [];"), ["true"])
        self.assertEqual(get_output("print [] # [];"), ["false"])
        self.assertEqual(get_output("print [5, 6] = [5, 6];"), ["true"])
        self.assertEqual(get_output("print [5, 6] # [5, 6];"), ["false"])
        self.assertEqual(get_output("print [5, 6] = [5, 7];"), ["false"])
        self.assertEqual(get_output("print [5, 6] # [5, 7];"), ["true"])
        self.assertEqual(get_output("print [5, 6] = [5];"), ["false"])
        self.assertEqual(get_output("print [5, 6] # [5];"), ["true"])

        self.assertEqual(get_output("print [5, 6] + [7, 8];"), ["[5, 6, 7, 8]"])
        self.assertEqual(get_output("print [5, 6] * 3;"), ["[5, 6, 5, 6, 5, 6]"])

        self.assertEqual(get_output("print [5, 6, 7, 8][0];"), ["5"])
        self.assertEqual(get_output("print [5, 6, 7, 8][3];"), ["8"])
        self.assertEqual(get_output("print [[5, 6], [7, 8]][1];"), ["[7, 8]"])
        self.assertEqual(get_output("print [[5, 6], [7, 8]][1][0];"), ["7"])
        self.assertEqual(get_output("print func(){ return [5, 6, 7, 8]; }()[0];"), ["5"])
        self.assertEqual(get_output("print [func(i){ return [5, 6, 7, 8][i]; }][0](3);"), ["8"])

        self.assertEqual(get_output("var a = [5, 6, 7]; set a[1] = 8; print a;"), ["[5, 8, 7]"])
        self.assertEqual(get_output("var a = [[5, 6], [7, 8]]; set a[1][0] = 9; print a;"), ["[[5, 6], [9, 8]]"])
        self.assertEqual(get_error("set 3[1] = 1;"), "Expected a name, found `3`.")

        self.assertEqual(get_output("var a = [5, 6]; push(a, 7); print a;"), ["[5, 6, 7]"])
        self.assertEqual(get_output("var a = [5, 6, 7]; print pop(a); print a;"), ["7", "[5, 6]"])
        self.assertEqual(get_output("print len([5, 6, 7]);"), ["3"])

        self.assertEqual(get_output("print 5 % [5, 6, 7];"), ["true"])
        self.assertEqual(get_output("print 8 % [5, 6, 7];"), ["false"])

    def test_insertion_sort(self):
        self.assertEqual(get_output("""
                                    var a = [3, 7, 6, 4, 9, 2];
                                    var i = 0;
                                    while i < len(a) {
                                        var v = a[i];
                                        var j = i;
                                        while 0 < j {
                                            if v < a[j - 1] {
                                                set a[j] = a[j - 1];
                                            } else {
                                                break;
                                            }
                                            set j = j - 1;
                                        }
                                        set a[j] = v;
                                        set i = i + 1;
                                    }
                                    print a;
                                    """), ["[2, 3, 4, 6, 7, 9]"])

    def test_primes(self):
        self.assertEqual(get_output("""
                                    var N = 10;
                                    var is_prime = [false, false] + [true] * (N - 2);
                                    var i = 2;
                                    while i * i < N {
                                        if is_prime[i] {
                                            var j = i + i;
                                            while j < N { set is_prime[j] = false; set j = j + i; }
                                        }
                                        set i = i + 1;
                                    }
                                    set i = 2;
                                    while i < N {
                                        if is_prime[i] { print i; }
                                        set i = i + 1;
                                    }
                                    """), ["2", "3", "5", "7"])

    def test_for_in(self):
        self.assertEqual(get_output("for i in [5, [6], 7] { print i; }"), ["5", "[6]", "7"])
        self.assertEqual(get_output("""
                                    for i in [5, 6, 7] { if i = 6 { break; } print i; }
                                    """), ["5"])
        self.assertEqual(get_output("""
                                    for i in [5, 6, 7] { if i = 6 { continue; } print i; }
                                    """), ["5", "7"])

    def test_range(self):
        self.assertEqual(get_output("""
                                    def range(start, end) {
                                        var result = []; var i = start;
                                        while i < end { push(result, i); set i = i + 1; }
                                        return result;
                                    }

                                    var sum = 0;
                                    for i in range(1, 10) { set sum = sum + i; }
                                    print sum;
                                    """), ["45"])

    def test_functional(self):
        self.assertEqual(get_output("""
                                    def map(array, f) {
                                        var result = [];
                                        for e in array { push(result, f(e)); }
                                        return result;
                                    }

                                    def filter(array, f) {
                                        var result = [];
                                        for e in array { if f(e) { push(result, e); } }
                                        return result;
                                    }

                                    def reduce(array, f, init) {
                                        var result = init;
                                        for e in array { set result = f(result, e); }
                                        return result;
                                    }

                                    print
                                        reduce(
                                            map(
                                                filter(
                                                    [5, 2, 3, 9, 6],
                                                    func (e) { return e % 2 = 1; }
                                                ),
                                                func (e) { return e * 2; }
                                            ),
                                            func (acc, e) { return acc + e; },
                                            0
                                        );
                                    """), ["34"])

    def test_str(self):
        self.assertEqual(get_output("print 'hello, world';"), ["hello, world"])
        self.assertEqual(get_output("print '';"), [""])
        self.assertEqual(get_output("print 'abc' + 'def';"), ["abcdef"])
        self.assertEqual(get_output("print 'abc' * 3;"), ["abcabcabc"])
        self.assertEqual(get_output("print 'abc' = 'abc';"), ["true"])
        self.assertEqual(get_output("print 'abc' # 'abc';"), ["false"])
        self.assertEqual(get_output("print 'abc' < 'abd';"), ["true"])
        self.assertEqual(get_output("print 'abc' > 'abd';"), ["false"])

        self.assertEqual(get_output("print 'abc'[0];"), ["a"])

        self.assertEqual(get_output("print 'abc' + to_print(true);"), ["abctrue"])
        self.assertEqual(get_output("print 'abc' + to_print(false);"), ["abcfalse"])
        self.assertEqual(get_output("print 'abc' + to_print(5);"), ["abc5"])
        self.assertEqual(get_output("print 'abc' + to_print('def');"), ["abcdef"])
        self.assertEqual(get_output("print 'abc' + to_print(null);"), ["abcnull"])
        self.assertEqual(get_output("print 'abc' + to_print(less);"), ["abc<builtin>"])
        self.assertEqual(get_output("print 'abc' + to_print(func(){});"), ["abc<func>"])
        self.assertEqual(get_output("print 'abc' + to_print([5, 'abc']);"), ["abc[5, abc]"])
        self.assertEqual(get_output("""print 'line 1
line 2';"""), ["line 1\nline 2"])

        self.assertEqual(get_output("print len('abc');"), ["3"])

        self.assertEqual(get_output("for c in 'abc' { print c; }"), ["a", "b", "c"])
        self.assertEqual(get_output("""
                                    for c in 'abc' { if c = 'b' { break; } print c; }
                                    """), ["a"])
        self.assertEqual(get_output("""
                                    for c in 'abc' { if c = 'b' { continue; } print c; }
                                    """), ["a", "c"])

        self.assertEqual(get_output("print 'a' % 'abc';"), ["true"])
        self.assertEqual(get_output("print 'd' % 'abc';"), ["false"])

    def test_dic(self):
        self.assertEqual(get_output("print $[];"), ["$[]"])
        self.assertEqual(get_output("print $[a: 1 + 2, b: 3 * 4];"), ["$[a: 3, b: 12]"])
        self.assertEqual(get_error("print $[1: 1];"), "Name expected, found `1`.")
        self.assertEqual(get_error("print $[a; 1 + 2, b: 3 * 4];"), "Expected `:`, found `;`.")
        self.assertEqual(get_error("print $[a: 1 + 2; b: 3 * 4];"), "Expected `,`, found `;`.")

        self.assertEqual(get_output("print $[a: 5, b: 6]['a'];"), ["5"])

        self.assertEqual(get_output("print keys($[a: 5, b: 6]);"), ["[a, b]"])
        self.assertEqual(get_output("print 'a' % $[a: 5, b: 6];"), ["true"])
        self.assertEqual(get_output("print 'd' % $[a: 5, b: 6];"), ["false"])

        self.assertEqual(get_output("var a = $[a: 5, b: 6]; for k in a { print a[k]; }"), ["5", "6"])

    def test_dict_by_dot(self):
        self.assertEqual(get_output("var a = $[]; set a.abc = 5; print a; print a.abc; print a['abc'];"),
                                    ["$[abc: 5]", "5", "5"])
        self.assertEqual(get_output("var a = $[cde: true]; set a.abc = 5; print a;"),
                                    ["$[cde: true, abc: 5]"])
        self.assertEqual(get_output("""
                                    var a = $[]; set a.abc = $[]; set a.abc.cde = 5;
                                    print a; print a.abc.cde; print a['abc'].cde; print a.abc['cde'];
                                    """),
                                    ["$[abc: $[cde: 5]]", "5", "5", "5"])
        self.assertEqual(get_output("""
                                    var a = $[]; set a.abc = func(a) { return 2 * a; };
                                    print a; print a.abc; print a['abc'](5);
                                    """),
                                    ["$[abc: <func>]", "<func>", "10"])
        self.assertEqual(get_output("""
                                    var a = $[val: 5]; set a.abc = func(this) { return 2 * this.val; };
                                    print a; print a.abc; print a['abc'](a);
                                    """),
                                    ["$[val: 5, abc: <func>]", "<func>", "10"])
        self.assertEqual(get_output("""
                                    var a = $[val: 5]; set a.abc = func(this) { return 2 * this.val; };
                                    print a; print a.abc; print a.abc();
                                    """),
                                    ["$[val: 5, abc: <func>]", "<func>", "10"])

if __name__ == "__main__":
    unittest.main()
