"""
Curated local question bank.

Every question is a plain dict validated once here (see `_validate_bank` below)
so a typo never reaches gameplay. This is the trusted fallback the AI generator
(ai/generator.py) always has behind it — the game never depends on the AI being
available or correct.

Difficulty tiers: "Easy", "Medium", "Hard", "Expert"
Question types:
  mcq            -> options: list[str], correct: int (index)
  true_false     -> options implicit True/False, correct: bool
  output         -> predict what `code` prints; options + correct like mcq
  completion     -> fill the blank; options + correct like mcq
  debugging      -> identify the bug; options + correct like mcq
  complexity     -> Big-O of `code`; options + correct like mcq
  short_answer   -> correct: str, matched case-insensitively against accepted list
  code_writing   -> free-form function; has `starter_code`, `tests` (see security/code_sandbox.py)
"""
from __future__ import annotations
import random

QUESTIONS: list[dict] = [
    # ---------------- python_basics ----------------
    {
        "id": "py001", "category": "python_basics", "difficulty": "Easy", "type": "mcq",
        "question": "Which keyword defines a function in Python?",
        "options": ["func", "def", "function", "lambda"], "correct": 1,
        "explanation": "`def` introduces a function definition; `lambda` only makes anonymous one-liners.",
        "time_limit": 15,
    },
    {
        "id": "py002", "category": "python_basics", "difficulty": "Easy", "type": "true_false",
        "question": "Python is a statically typed language.",
        "correct": False,
        "explanation": "Python is dynamically typed — variable types are checked at runtime, not compile time.",
        "time_limit": 12,
    },
    {
        "id": "py003", "category": "python_basics", "difficulty": "Medium", "type": "output",
        "question": "What does this print?",
        "code": "x = 5\ny = '5'\nprint(x == y)",
        "options": ["True", "False", "Error", "None"], "correct": 1,
        "explanation": "`==` compares value AND type here; an int is never equal to a str, so it's False.",
        "time_limit": 20,
    },
    {
        "id": "py004", "category": "python_basics", "difficulty": "Medium", "type": "mcq",
        "question": "Which of these is immutable in Python?",
        "options": ["list", "dict", "tuple", "set"], "correct": 2,
        "explanation": "Tuples cannot be modified after creation; lists, dicts and sets can.",
        "time_limit": 15,
    },
    {
        "id": "py005", "category": "python_basics", "difficulty": "Hard", "type": "output",
        "question": "What does this print?",
        "code": "def f(a, b=[]):\n    b.append(a)\n    return b\n\nprint(f(1))\nprint(f(2))",
        "options": ["[1] then [2]", "[1] then [1, 2]", "[2] then [1, 2]", "Error"], "correct": 1,
        "explanation": "Mutable default arguments are created once and reused across calls — the classic gotcha.",
        "time_limit": 25,
    },
    {
        "id": "py006", "category": "python_basics", "difficulty": "Expert", "type": "output",
        "question": "What does this print?",
        "code": "class A:\n    x = []\n\na, b = A(), A()\na.x.append(1)\nprint(b.x)",
        "options": ["[]", "[1]", "AttributeError", "None"], "correct": 1,
        "explanation": "`x` is a class attribute (shared list), so mutating it through any instance affects all instances.",
        "time_limit": 30,
    },
    {
        "id": "py007", "category": "python_basics", "difficulty": "Easy", "type": "short_answer",
        "question": "What built-in function returns the number of items in a list?",
        "correct": "len", "accept": ["len", "len()"],
        "explanation": "`len(obj)` works on any sized container: list, str, dict, tuple, set.",
        "time_limit": 15,
    },
    {
        "id": "py008", "category": "python_basics", "difficulty": "Medium", "type": "completion",
        "question": "Fill in the blank so this prints 'HELLO':",
        "code": "s = 'hello'\nprint(s.________())",
        "options": ["upper", "capitalize", "title", "swapcase"], "correct": 0,
        "explanation": "`.upper()` converts every character to uppercase.",
        "time_limit": 15,
    },

    # ---------------- lists_strings ----------------
    {
        "id": "ls001", "category": "lists_strings", "difficulty": "Easy", "type": "output",
        "question": "What does this print?",
        "code": "x = [1, 2, 3]\nprint(x[::-1])",
        "options": ["[1, 2, 3]", "[3, 2, 1]", "Error", "None"], "correct": 1,
        "explanation": "A step of -1 reverses the sequence.",
        "time_limit": 15,
    },
    {
        "id": "ls002", "category": "lists_strings", "difficulty": "Easy", "type": "output",
        "question": "What does this print?",
        "code": "x = [1, 2, 3]\nprint(x[-1])",
        "options": ["1", "3", "Error", "None"], "correct": 1,
        "explanation": "Negative indices count from the end; -1 is the last element.",
        "time_limit": 12,
    },
    {
        "id": "ls003", "category": "lists_strings", "difficulty": "Medium", "type": "output",
        "question": "What does this print?",
        "code": "s = 'python'\nprint(s[1:4])",
        "options": ["'pyt'", "'yth'", "'ytho'", "'python'"], "correct": 1,
        "explanation": "Slicing [1:4] takes indices 1,2,3 -> 'y','t','h' -> 'yth'.",
        "time_limit": 18,
    },
    {
        "id": "ls004", "category": "lists_strings", "difficulty": "Medium", "type": "debugging",
        "question": "This code should print each number's neighbor sum but crashes. What's the bug?",
        "code": "numbers = [1, 2, 3, 4, 5]\nfor i in range(len(numbers)):\n    print(numbers[i + 1])",
        "options": ["Syntax error", "IndexError on the last iteration", "Infinite loop", "No bug"], "correct": 1,
        "explanation": "When i is the last valid index, `i + 1` is out of range -> IndexError.",
        "time_limit": 25,
    },
    {
        "id": "ls005", "category": "lists_strings", "difficulty": "Hard", "type": "output",
        "question": "What does this print?",
        "code": "a = [1, 2, 3]\nb = a\nb.append(4)\nprint(a)",
        "options": ["[1, 2, 3]", "[1, 2, 3, 4]", "Error", "[4]"], "correct": 1,
        "explanation": "`b = a` copies the reference, not the list — both names point to the same object.",
        "time_limit": 20,
    },
    {
        "id": "ls006", "category": "lists_strings", "difficulty": "Medium", "type": "completion",
        "question": "Fill in the blank so this produces [1, 4, 9, 16]:",
        "code": "nums = [1, 2, 3, 4]\nsquares = [________ for n in nums]",
        "options": ["n * n", "n + n", "n ** 1", "n / n"], "correct": 0,
        "explanation": "`n * n` (or `n ** 2`) squares each element.",
        "time_limit": 18,
    },
    {
        "id": "ls007", "category": "lists_strings", "difficulty": "Expert", "type": "output",
        "question": "What does this print?",
        "code": "x = [[0] * 3] * 3\nx[0][0] = 1\nprint(x)",
        "options": ["[[1,0,0],[0,0,0],[0,0,0]]", "[[1,0,0],[1,0,0],[1,0,0]]", "Error", "[[0,0,0],[0,0,0],[0,0,0]]"], "correct": 1,
        "explanation": "`[[0]*3]*3` repeats the SAME inner list object 3 times, so mutating one row mutates all.",
        "time_limit": 30,
    },
    {
        "id": "ls008", "category": "lists_strings", "difficulty": "Easy", "type": "true_false",
        "question": "Strings in Python are mutable (you can change a character in place).",
        "correct": False,
        "explanation": "Strings are immutable; `s[0] = 'x'` raises a TypeError.",
        "time_limit": 12,
    },

    # ---------------- loops_control ----------------
    {
        "id": "lp001", "category": "loops_control", "difficulty": "Easy", "type": "output",
        "question": "What does this print?",
        "code": "for i in range(3):\n    print(i)",
        "options": ["1 2 3", "0 1 2", "0 1 2 3", "1 2"], "correct": 1,
        "explanation": "`range(3)` yields 0, 1, 2 — stops before the stop value.",
        "time_limit": 12,
    },
    {
        "id": "lp002", "category": "loops_control", "difficulty": "Medium", "type": "output",
        "question": "What does this print?",
        "code": "for i in range(5):\n    if i == 3:\n        break\n    print(i)",
        "options": ["0 1 2", "0 1 2 3", "0 1 2 3 4", "3"], "correct": 0,
        "explanation": "`break` exits the loop entirely as soon as i == 3, before printing it.",
        "time_limit": 15,
    },
    {
        "id": "lp003", "category": "loops_control", "difficulty": "Medium", "type": "output",
        "question": "What does this print?",
        "code": "for i in range(5):\n    if i % 2 == 0:\n        continue\n    print(i)",
        "options": ["0 2 4", "1 3", "1 3 5", "0 1 2 3 4"], "correct": 1,
        "explanation": "`continue` skips printing on even i, so only the odd values 1 and 3 print.",
        "time_limit": 18,
    },
    {
        "id": "lp004", "category": "loops_control", "difficulty": "Hard", "type": "debugging",
        "question": "This is meant to sum 1..10 but returns the wrong value. What's the bug?",
        "code": "total = 0\nfor i in range(10):\n    total += i\nprint(total)",
        "options": ["It sums 0..9, not 1..10", "Infinite loop", "TypeError", "No bug"], "correct": 0,
        "explanation": "`range(10)` is 0..9; to sum 1..10 you need `range(1, 11)`.",
        "time_limit": 22,
    },
    {
        "id": "lp005", "category": "loops_control", "difficulty": "Expert", "type": "debugging",
        "question": "This never terminates. What's the bug?",
        "code": "i = 0\nwhile i < 10:\n    print(i)\n    if i == 5:\n        i -= 1\n    i += 1",
        "options": ["It's fine, terminates normally", "i gets stuck oscillating around 5, looping forever", "SyntaxError", "IndexError"], "correct": 1,
        "explanation": "When i hits 5 it decrements then increments back to 5, repeating forever without ever passing 5.",
        "time_limit": 30,
    },
    {
        "id": "lp006", "category": "loops_control", "difficulty": "Easy", "type": "true_false",
        "question": "A `while` loop with condition `True` and no `break` will run forever.",
        "correct": True,
        "explanation": "Without a break/return/exception, `while True:` never stops on its own.",
        "time_limit": 12,
    },

    # ---------------- functions_oop ----------------
    {
        "id": "oop001", "category": "functions_oop", "difficulty": "Easy", "type": "mcq",
        "question": "Which method is automatically called when you create a new instance of a class?",
        "options": ["__new__", "__init__", "__create__", "__start__"], "correct": 1,
        "explanation": "`__init__` initializes a newly created instance (after `__new__` allocates it).",
        "time_limit": 15,
    },
    {
        "id": "oop002", "category": "functions_oop", "difficulty": "Medium", "type": "output",
        "question": "What does this print?",
        "code": "def outer():\n    x = 1\n    def inner():\n        nonlocal x\n        x += 1\n        return x\n    return inner()\nprint(outer())",
        "options": ["1", "2", "Error", "None"], "correct": 1,
        "explanation": "`nonlocal` lets `inner` modify `outer`'s x; it becomes 2 before being returned.",
        "time_limit": 22,
    },
    {
        "id": "oop003", "category": "functions_oop", "difficulty": "Medium", "type": "mcq",
        "question": "What does inheritance let a subclass do?",
        "options": ["Delete the parent class", "Reuse and extend the parent class's attributes/methods", "Run faster than the parent", "Become a module"], "correct": 1,
        "explanation": "Inheritance lets a subclass reuse and override behavior defined on its parent.",
        "time_limit": 15,
    },
    {
        "id": "oop004", "category": "functions_oop", "difficulty": "Hard", "type": "output",
        "question": "What does this print?",
        "code": "class Animal:\n    def speak(self):\n        return 'generic sound'\n\nclass Dog(Animal):\n    def speak(self):\n        return 'woof'\n\nanimals = [Animal(), Dog()]\nprint([a.speak() for a in animals])",
        "options": ["['generic sound', 'generic sound']", "['generic sound', 'woof']", "['woof', 'woof']", "Error"], "correct": 1,
        "explanation": "Polymorphism: each object's own (overridden) `speak` is called.",
        "time_limit": 22,
    },
    {
        "id": "oop005", "category": "functions_oop", "difficulty": "Expert", "type": "output",
        "question": "What does this print?",
        "code": "def make_multiplier(n):\n    return lambda x: x * n\n\ndouble = make_multiplier(2)\ntriple = make_multiplier(3)\nprint(double(5), triple(5))",
        "options": ["5 5", "10 15", "10 10", "Error"], "correct": 1,
        "explanation": "Each closure captures its own `n` (2 and 3), so double(5)=10 and triple(5)=15.",
        "time_limit": 25,
    },
    {
        "id": "oop006", "category": "functions_oop", "difficulty": "Medium", "type": "true_false",
        "question": "In Python, `self` must be named exactly `self` — it's a reserved keyword.",
        "correct": False,
        "explanation": "`self` is just a convention (first param of instance methods); any name works, but everyone uses `self`.",
        "time_limit": 15,
    },

    # ---------------- algorithms_ds ----------------
    {
        "id": "al001", "category": "algorithms_ds", "difficulty": "Easy", "type": "mcq",
        "question": "Which data structure is First-In-First-Out (FIFO)?",
        "options": ["Stack", "Queue", "Tree", "Hash Table"], "correct": 1,
        "explanation": "A queue serves the earliest-added item first, like a checkout line.",
        "time_limit": 15,
    },
    {
        "id": "al002", "category": "algorithms_ds", "difficulty": "Medium", "type": "mcq",
        "question": "Which sorting algorithm repeatedly picks the smallest remaining element and places it at the front?",
        "options": ["Selection sort", "Merge sort", "Quick sort", "Bubble sort"], "correct": 0,
        "explanation": "Selection sort scans the unsorted part for the minimum and swaps it into place each pass.",
        "time_limit": 18,
    },
    {
        "id": "al003", "category": "algorithms_ds", "difficulty": "Medium", "type": "mcq",
        "question": "Binary search requires the input to be:",
        "options": ["Sorted", "A linked list", "Unique values only", "A power of two in length"], "correct": 0,
        "explanation": "Binary search relies on being able to discard half the remaining elements each step, which only works on sorted data.",
        "time_limit": 15,
    },
    {
        "id": "al004", "category": "algorithms_ds", "difficulty": "Hard", "type": "mcq",
        "question": "Which structure naturally implements recursion's call stack behavior (LIFO)?",
        "options": ["Queue", "Stack", "Graph", "Hash map"], "correct": 1,
        "explanation": "Last-In-First-Out matches how function calls return in reverse order of being called.",
        "time_limit": 18,
    },
    {
        "id": "al005", "category": "algorithms_ds", "difficulty": "Hard", "type": "output",
        "question": "What does this print? (classic recursive function)",
        "code": "def f(n):\n    if n <= 1:\n        return n\n    return f(n - 1) + f(n - 2)\n\nprint(f(6))",
        "options": ["6", "8", "13", "5"], "correct": 1,
        "explanation": "This is Fibonacci; f(6) = 8 following 0,1,1,2,3,5,8.",
        "time_limit": 28,
    },
    {
        "id": "al006", "category": "algorithms_ds", "difficulty": "Expert", "type": "mcq",
        "question": "A graph traversal that explores as deep as possible before backtracking is:",
        "options": ["BFS", "DFS", "Dijkstra's", "Topological sort"], "correct": 1,
        "explanation": "Depth-First Search dives down one path fully before backtracking; BFS explores level by level.",
        "time_limit": 20,
    },
    {
        "id": "al007", "category": "algorithms_ds", "difficulty": "Medium", "type": "true_false",
        "question": "A hash table gives average O(1) lookup time.",
        "correct": True,
        "explanation": "With a good hash function and low collision rate, lookups are on average constant time.",
        "time_limit": 15,
    },

    # ---------------- complexity ----------------
    {
        "id": "cx001", "category": "complexity", "difficulty": "Easy", "type": "complexity",
        "question": "What is the time complexity of this code?",
        "code": "for i in range(n):\n    print(i)",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n^2)"], "correct": 2,
        "explanation": "A single pass over n elements is linear time, O(n).",
        "time_limit": 15,
    },
    {
        "id": "cx002", "category": "complexity", "difficulty": "Medium", "type": "complexity",
        "question": "What is the time complexity of this code?",
        "code": "for i in range(n):\n    for j in range(n):\n        print(i, j)",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(2^n)"], "correct": 2,
        "explanation": "Nested loops each running n times give n * n = O(n^2) total operations.",
        "time_limit": 18,
    },
    {
        "id": "cx003", "category": "complexity", "difficulty": "Medium", "type": "complexity",
        "question": "What is the time complexity of binary search?",
        "code": "# binary search on a sorted array of size n",
        "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"], "correct": 1,
        "explanation": "Each comparison halves the search space, giving logarithmic time.",
        "time_limit": 18,
    },
    {
        "id": "cx004", "category": "complexity", "difficulty": "Hard", "type": "complexity",
        "question": "What is the time complexity of this code?",
        "code": "i = 1\nwhile i < n:\n    print(i)\n    i *= 2",
        "options": ["O(n)", "O(log n)", "O(n^2)", "O(1)"], "correct": 1,
        "explanation": "i doubles each iteration, so the loop runs about log2(n) times.",
        "time_limit": 22,
    },
    {
        "id": "cx005", "category": "complexity", "difficulty": "Expert", "type": "complexity",
        "question": "What is the time complexity of naive recursive Fibonacci (fib(n) = fib(n-1) + fib(n-2))?",
        "code": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(2^n)"], "correct": 3,
        "explanation": "Without memoization, the call tree branches in two at every level, giving exponential O(2^n) calls.",
        "time_limit": 28,
    },
    {
        "id": "cx006", "category": "complexity", "difficulty": "Medium", "type": "complexity",
        "question": "What is the time complexity of merge sort?",
        "code": "# merge sort on an array of size n",
        "options": ["O(n)", "O(n log n)", "O(n^2)", "O(log n)"], "correct": 1,
        "explanation": "Merge sort splits log n times and does O(n) merge work at each level -> O(n log n).",
        "time_limit": 18,
    },

    # ---------------- debugging ----------------
    {
        "id": "db001", "category": "debugging", "difficulty": "Easy", "type": "debugging",
        "question": "What's wrong with this code?",
        "code": "def greet(name)\n    print('Hello ' + name)",
        "options": ["Missing colon after the function signature", "Missing return statement", "Wrong string concatenation", "No bug"], "correct": 0,
        "explanation": "`def greet(name)` needs a trailing `:` — this is a SyntaxError.",
        "time_limit": 15,
    },
    {
        "id": "db002", "category": "debugging", "difficulty": "Medium", "type": "debugging",
        "question": "This should filter even numbers but returns an empty list. What's the bug?",
        "code": "def get_evens(nums):\n    result = []\n    for n in nums:\n        if n % 2 = 0:\n            result.append(n)\n    return result",
        "options": ["Should use `==` not `=` in the comparison", "`result` should be a dict", "`for` should be `while`", "No bug"], "correct": 0,
        "explanation": "`=` is assignment; comparisons need `==`. As written this is actually a SyntaxError in Python.",
        "time_limit": 20,
    },
    {
        "id": "db003", "category": "debugging", "difficulty": "Medium", "type": "debugging",
        "question": "This is meant to compute an average but crashes on an empty list. What's the safest fix?",
        "code": "def average(nums):\n    return sum(nums) / len(nums)",
        "options": ["Multiply by 0 instead of dividing", "Check `if not nums: return 0` before dividing", "Use `//` instead of `/`", "There's no way to fix this"], "correct": 1,
        "explanation": "Guarding the empty case avoids a ZeroDivisionError.",
        "time_limit": 20,
    },
    {
        "id": "db004", "category": "debugging", "difficulty": "Hard", "type": "debugging",
        "question": "What's wrong with this code?",
        "code": "def add_item(item, items=[]):\n    items.append(item)\n    return items\n\ncart1 = add_item('apple')\ncart2 = add_item('banana')\nprint(cart2)",
        "options": ["Prints ['banana'] only", "Prints ['apple', 'banana'] — mutable default arg shared across calls", "TypeError", "Prints []"], "correct": 1,
        "explanation": "The default list `items=[]` is created once at function definition and reused on every call missing that argument.",
        "time_limit": 25,
    },
    {
        "id": "db005", "category": "debugging", "difficulty": "Hard", "type": "debugging",
        "question": "This recursive function is supposed to compute factorial but crashes with RecursionError for n=5. What's the bug?",
        "code": "def factorial(n):\n    return n * factorial(n - 1)",
        "options": ["Missing base case (e.g. `if n <= 1: return 1`)", "Should use a loop instead", "`n - 1` should be `n + 1`", "No bug"], "correct": 0,
        "explanation": "Without a base case, the recursion never stops and blows the call stack.",
        "time_limit": 22,
    },
    {
        "id": "db006", "category": "debugging", "difficulty": "Expert", "type": "debugging",
        "question": "What's the subtle bug here?",
        "code": "def process(items=None):\n    if items == None:\n        items = []\n    items.append('x')\n    return items",
        "options": ["`== None` should be `is None` (style, not a real bug here)", "This will silently share state across calls just like a mutable default", "Missing colon", "No bug at all, and it's also the idiomatic way to write it"], "correct": 0,
        "explanation": "Behaviourally this is correct (a fresh list per call) — the only real issue is style: prefer `is None` over `== None` for identity checks against singletons.",
        "time_limit": 28,
    },

    # ---------------- databases_web ----------------
    {
        "id": "dw001", "category": "databases_web", "difficulty": "Easy", "type": "mcq",
        "question": "Which SQL keyword retrieves rows from a table?",
        "options": ["GET", "SELECT", "FETCH", "PULL"], "correct": 1,
        "explanation": "`SELECT ... FROM table` is the standard SQL query for reading rows.",
        "time_limit": 12,
    },
    {
        "id": "dw002", "category": "databases_web", "difficulty": "Medium", "type": "mcq",
        "question": "What does a PRIMARY KEY constraint guarantee?",
        "options": ["Values can repeat", "Uniqueness and non-null for that column", "Automatic sorting", "Faster INSERTs only"], "correct": 1,
        "explanation": "A primary key uniquely identifies each row and cannot be NULL.",
        "time_limit": 15,
    },
    {
        "id": "dw003", "category": "databases_web", "difficulty": "Medium", "type": "mcq",
        "question": "Which HTTP status code means 'Not Found'?",
        "options": ["200", "301", "404", "500"], "correct": 2,
        "explanation": "404 means the server couldn't find the requested resource.",
        "time_limit": 12,
    },
    {
        "id": "dw004", "category": "databases_web", "difficulty": "Hard", "type": "mcq",
        "question": "What's the main risk of building SQL queries by string-concatenating raw user input?",
        "options": ["Slower queries", "SQL injection", "Extra memory usage", "Nothing, it's fine"], "correct": 1,
        "explanation": "Unsanitized concatenation lets an attacker inject SQL, e.g. `' OR 1=1 --`; use parameterized queries instead.",
        "time_limit": 20,
    },
    {
        "id": "dw005", "category": "databases_web", "difficulty": "Hard", "type": "mcq",
        "question": "Which SQL JOIN returns all rows from the left table, with NULLs where there's no match on the right?",
        "options": ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "CROSS JOIN"], "correct": 1,
        "explanation": "A LEFT JOIN keeps every row from the left table regardless of a match.",
        "time_limit": 20,
    },
    {
        "id": "dw006", "category": "databases_web", "difficulty": "Medium", "type": "true_false",
        "question": "Storing passwords as plain text in a database is an acceptable practice if the database itself is access-controlled.",
        "correct": False,
        "explanation": "Passwords should always be hashed (e.g. bcrypt/argon2), never stored in plain text, regardless of other access controls.",
        "time_limit": 15,
    },
]

# ---------------- code-writing "final boss" challenges ----------------
CODE_CHALLENGES: list[dict] = [
    {
        "id": "cw001", "category": "algorithms_ds", "difficulty": "Hard",
        "title": "Largest Number",
        "prompt": "Write a function `largest(numbers)` that returns the largest number in a non-empty list.",
        "starter_code": "def largest(numbers):\n    # your code here\n    pass\n",
        "tests": [
            {"args": [[1, 5, 2]], "expected": 5},
            {"args": [[-3, -1, -7]], "expected": -1},
            {"args": [[42]], "expected": 42},
            {"args": [[3, 3, 3]], "expected": 3},
        ],
        "time_limit": 90,
    },
    {
        "id": "cw002", "category": "algorithms_ds", "difficulty": "Expert",
        "title": "Is Palindrome",
        "prompt": "Write a function `is_palindrome(s)` that returns True if the string reads the same forwards and backwards (case-sensitive, no cleanup needed).",
        "starter_code": "def is_palindrome(s):\n    # your code here\n    pass\n",
        "tests": [
            {"args": ["racecar"], "expected": True},
            {"args": ["hello"], "expected": False},
            {"args": [""], "expected": True},
            {"args": ["a"], "expected": True},
        ],
        "time_limit": 90,
    },
    {
        "id": "cw003", "category": "algorithms_ds", "difficulty": "Expert",
        "title": "FizzBuzz Sum",
        "prompt": "Write `fizzbuzz_sum(n)` that returns the sum of all multiples of 3 or 5 below n (classic Project Euler #1 style).",
        "starter_code": "def fizzbuzz_sum(n):\n    # your code here\n    pass\n",
        "tests": [
            {"args": [10], "expected": 23},
            {"args": [1], "expected": 0},
            {"args": [20], "expected": 78},
        ],
        "time_limit": 90,
    },
]


def _validate_bank() -> None:
    ids = set()
    for q in QUESTIONS:
        assert q["id"] not in ids, f"duplicate id {q['id']}"
        ids.add(q["id"])
        assert q["difficulty"] in {"Easy", "Medium", "Hard", "Expert"}
        if q["type"] in {"mcq", "output", "completion", "debugging", "complexity"}:
            assert isinstance(q["correct"], int) and 0 <= q["correct"] < len(q["options"])
        elif q["type"] == "true_false":
            assert isinstance(q["correct"], bool)
        elif q["type"] == "short_answer":
            assert isinstance(q["correct"], str)
    for c in CODE_CHALLENGES:
        assert c["id"] not in ids
        ids.add(c["id"])
        assert c["tests"], f"{c['id']} has no tests"


_validate_bank()

CATEGORIES = sorted({q["category"] for q in QUESTIONS})
DIFFICULTIES = ["Easy", "Medium", "Hard", "Expert"]


def get_questions(category: str | None = None, difficulty: str | None = None) -> list[dict]:
    pool = QUESTIONS
    if category:
        pool = [q for q in pool if q["category"] == category]
    if difficulty:
        pool = [q for q in pool if q["difficulty"] == difficulty]
    return pool


def pick_question(
    difficulty: str,
    exclude_ids: set[str],
    category: str | None = None,
) -> dict | None:
    """Pick a random question at (or near) the requested difficulty, avoiding repeats."""
    pool = [q for q in get_questions(category=category, difficulty=difficulty) if q["id"] not in exclude_ids]
    if not pool:
        # relax the difficulty constraint before giving up
        pool = [q for q in get_questions(category=category) if q["id"] not in exclude_ids]
    if not pool:
        pool = [q for q in QUESTIONS if q["id"] not in exclude_ids]
    if not pool:
        pool = QUESTIONS
    return random.choice(pool)


def pick_code_challenge(exclude_ids: set[str]) -> dict:
    pool = [c for c in CODE_CHALLENGES if c["id"] not in exclude_ids] or CODE_CHALLENGES
    return random.choice(pool)
