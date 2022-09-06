class SolutionChecker:

    def __init__(self, x1, y1, x2, y2):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.m = int((y2 - y1) / (x2 - x1))
        self.c = int(y1 - (self.m * x1))

    @staticmethod
    def _correct_syntax(u: str):
        """
        Checks whether or not the user input has correctly formatted brackets and has not put '++' or '---'
        :param u: short for user_input
        :return: True if the syntax is correct, False otherwise
        """
        # No need to remove white space since this is handled in the compare() function in the main.py file
        stack = []  # Checks whether the brackets in the expression are correct
        for i, char in enumerate(u):
            if char == '(':
                stack.append(char)
            elif char == ')':
                if len(stack) == 0:
                    return False  # Prevents )() and other such issues
                elif u[i - 1] == '+' or u[i - 1] == '/' or u[i - 1] == '×' or u[i - 1] == '-':
                    return False  # +) /) ×)
                stack.pop()
            elif char == '/' or char == '×':
                if i == 0:
                    return False
                elif u[i - 1] == '+' or u[i - 1] == '/' or u[i - 1] == '×' or u[i - 1] == '-' or u[i - 1] == '=':
                    return False  # /+ /- // /× =/ ×+ ×- ×/ ×× =×
            elif char == '+':
                if i == 0:  # Expression that starts with a plus is allowed
                    continue
                elif u[i - 1] == '+' or u[i - 1] == '×' or u[i - 1] == '/' or u[i - 1] == '=':  # ++ ×+ /+ =+
                    return False
                elif i > 2:
                    if u[i - 1] == '-' and not u[i - 2].isnumeric():  # +-+ --+ +++ -++ (-+ etc.
                        return False
            elif char == '-':
                if i == 0:  # Expression that starts with -- is allowed
                    continue
                elif i > 2:
                    if (u[i - 1] == '+' or u[i - 1] == '-' or u[i - 1] == '*' or u[i - 1] == '/') \
                            and not u[i - 2].isnumeric():  # +-- --- -+- ++- (-- *-- *+- /-- etc.
                        return False
            elif char == '=':
                if i == 0:
                    continue  # Expression that starts with = is allowed
                elif u[i - 1] == '+' or u[i - 1] == '/' or u[i - 1] == '×' or u[i - 1] == '-' or u[i - 1] == '=':
                    return False  # /= -= ×= += ==
                elif len(stack) > 0:
                    return False  # Prevents (x = c) = 4
            elif char.isnumeric():
                if i == 0:
                    continue
                if u[i - 1].isalpha():
                    return False  # Prevents a2
            elif char.isalpha() and char not in 'ymxc':
                return False  # Not all that useful but acts as a safety net if user attempts to add other characters

        if len(stack) > 0:
            return False  # Prevents (() and other errors with opening and closing brackets

        return True

    @staticmethod
    def _format_expression(expression: str):
        """
        Takes any string, and arranges into a list. All - signs are replaced by + and the number proceeding the
        negative has its sign inverted. An equal sign in the expression will split the string into two lists.
        :return: list of list
        """
        # expression = expression.replace(" ", "")  # Start by removing all spaces
        # No need to remove white space since this is handled in the compare() function in the main.py file
        temp = ''  # A temporary string we will use to store numbers (since the loop will read them one at a time)
        prev = None  # Stores the previous value - used to check for -- or +-
        res = [[]]  # Our list of lists
        for char in expression:
            if char == '=':
                if prev is None:
                    continue
                if len(temp) > 0:
                    res[-1].append(temp)
                    temp = ''
                res.append([])
            elif char.isnumeric():
                temp += char
            else:
                if prev is None:
                    if char.isnumeric():
                        temp += char
                    else:
                        if char == '+' or char == '-':
                            temp += char
                        else:
                            res[-1].append(char)
                elif prev.isnumeric():
                    res[-1].append(temp)
                    res[-1].append(char)
                    temp = ''
                elif prev == ')':
                    res[-1].append(char)
                    if len(temp) > 0:
                        res[-1].append(temp)
                        temp = ''
                else:
                    if char == '+' or char == '-':
                        temp += char
                    else:
                        if temp == '+' or temp == '-':
                            res[-1].append(temp)
                        res[-1].append(char)
                        temp = ''
            prev = char
        if len(temp) > 0:
            res[-1].append(temp)
        return res

    def _evaluate_expression(self, expression: list):
        """
        Will return False if there was a ZeroDivisionError
        :param expression:
        :return:
        """
        stack = []
        for i, x in enumerate(expression):
            if x == '(':
                stack.append(i)
            elif x == ')':
                start = stack.pop()
                result = self._evaluate_brackets(expression[start + 1: i])
                if result is not False:
                    expression[start: i + 1] = result
                    return self._evaluate_expression(expression)
                else:
                    return False
        return self._evaluate_brackets(expression)

    @staticmethod
    def _evaluate_brackets(expression: list):
        count = 1
        while len(expression) > 1:
            if '×' in expression:
                index = expression.index('×')
                product = float(expression[index - 1]) * float(expression[index + 1])
                expression.insert(index + 2, product)
                del expression[index - 1:index + 2]
                continue
            if '/' in expression:
                index = expression.index('/')
                try:
                    division = float(expression[index - 1]) / float(expression[index + 1])
                except ZeroDivisionError:
                    return False
                expression.insert(index + 2, division)
                del expression[index - 1:index + 2]
                continue
            if '+' in expression:
                index = expression.index('+')
                summation = float(expression[index - 1]) + float(expression[index + 1])
                expression.insert(index + 2, summation)
                del expression[index - 1:index + 2]
                continue
            if '-' in expression:
                index = expression.index('-')
                subtraction = float(expression[index - 1]) - float(expression[index + 1])
                expression.insert(index + 2, subtraction)
                del expression[index - 1:index + 2]
                continue
            # If the loop has descended to this point then something has gone wrong
            if count > 5:
                break
            count += 1
        return expression

    def _check_solution(self, user_input: str, solution=None):
        """
        First the function re-formats the solution using the format expression function. Then it iterates over the list
        of list and reduced each expression submitted by the user to its simplest form. If a solution is given the
        function checks whether or not each given expression equals the solution. If a solution is not given, then the
        function checks whether submitted expression is equal to each other.
        :param user_input: user input expressed as str
        :param solution: model answer expressed as an integer - default is None
        :return: True if all expressions reduce to "solution". False if any expression cannot be reduced to "solution".
        """
        user_answers = self._format_expression(user_input)

        if solution is None:
            evaluated_expressions = set()
            for expression in user_answers:
                simplified = self._evaluate_expression(expression)  # Evaluate each expression
                evaluated_expressions.add(float(simplified[0]))

            return len(evaluated_expressions) == 1

        else:
            for expression in user_answers:
                simplified = self._evaluate_expression(expression)
                if simplified is False:  # ZeroDivisionError
                    return False
                elif len(simplified) == 0:  # User left the solution blank
                    return False
                if float(simplified[0]) != solution:
                    return False
            return True

    @staticmethod
    def _adjust_coefficient(user_input: str, variable: str):
        i = user_input.index(variable)
        if i != 0:
            if user_input[i - 1].isnumeric() or user_input[i - 1] == ')':  # If Nx [and not -x (x or +x]
                user_input = user_input[:i] + '×' + user_input[i:]
            elif user_input[i - 1] == '-':  # If -x
                user_input = user_input[:i - 1] + '-1×' + user_input[i:]
        return user_input

    def step_one(self, user_input: str):
        """
        First checks whether solution has the correct syntax, evaluates the users solution, substituting m for the value
        of m if present. The function then checks whether each evaluated expression is equal to self.m (aka correct)
        :return True if step is correct, False otherwise
        """
        if not self._correct_syntax(user_input):
            return False
        user_input = user_input.replace('m', f'{self.m}')

        return self._check_solution(user_input, solution=self.m)

    def step_two(self, user_input: str):
        """
        Checks whether the user_input is in the correct format. Then checks whether 'c', 'x', 'y' and '=' is in the user
        input. Then substitutes values.
        :return: True if step is correct, False otherwise
        """
        if not self._correct_syntax(user_input):
            return False
        if (user_input.count('y') != 1) or (user_input.count('=') != 1):
            # y and = must be in solution
            return False
        if 'x' in user_input:
            user_input = self._adjust_coefficient(user_input, 'x')
        user_input = self._adjust_coefficient(user_input, 'y')

        user_input = user_input.replace('c', f'{self.c}')
        user_input = user_input.replace('x', f'{self.x1}')
        user_input = user_input.replace('y', f'{self.y1}')

        return self._check_solution(user_input)

    def step_three(self, user_input: str):
        """
        Checks whether the user_input is in the correct format. Then checks whether 'c' and '=' is in the user input.
        Then substitutes self.c in for c.
        :return: True if step is correct, False otherwise
        """
        if not self._correct_syntax(user_input):
            return False
        if (user_input.count('c') != 1) or '=' not in user_input:
            return False

        user_input = user_input.replace('c', f'{self.c}')

        return self._check_solution(user_input)

    def step_four(self, user_input: str):
        """
        Checks whether the user_input is in the correct format. Next it checks whether the user has submitted at least
        one number. Then, if present, substitutes values substitutes "c" for
        self.c
        :return: True if step is correct, False otherwise
        """
        if not self._correct_syntax(user_input):
            return False
        if not any(char.isdigit() for char in user_input):  # Prevents c, c = c, c = c = c, etc.
            return False

        user_input = user_input.replace('c', f'{self.c}')

        return self._check_solution(user_input, self.c)

    def step_five(self, user_input: str):
        """
        Checks whether solution is in correct syntax, then if '=', 'x', 'y' in user_input. Converts Nx --> N×x then
        replaces x and y with x1 and y1. Finally checks whether the solution is valid.
        :return: True if step is correct, False otherwise
        """
        if not self._correct_syntax(user_input):
            return False
        if (user_input.count('=') != 1) or (user_input.count('x') != 1) or (user_input.count('y') != 1):
            # Only one =, x and y allowed
            return False

        user_input = self._adjust_coefficient(user_input, 'x')
        user_input = self._adjust_coefficient(user_input, 'y')

        user_input = user_input.replace('x', f'{self.x1}')
        user_input = user_input.replace('y', f'({self.y1})')

        return self._check_solution(user_input)


if __name__ == "__main__":

    # Tests

    solution_checker = SolutionChecker(-3, 22, 1, 2)
    print(solution_checker.m)

    _user_input = "y=(-5)x+c"

    print(solution_checker.step_two(_user_input))

    zero = ['((7-5)/(2-1))=2', '((5-7)/(1-2))=2', '2=((7-5)/(2-1))', '2=((5-7)/(1-2))', '((-2)/(-1))=2',
            'm=((5-7)/(1-2))=((-2)/(-1))=2',
            '((2)/(1))=2', '2=((2)/(1))', '2', '=2', '=((7-5)/(2-1))', '((7-5)/(2-1))', '((5-7)/(1-2))',
            '=((5-7)/(1-2))', '((-2)/(-1))', 'm=((-2)/(-1))', '((2)/(1))', '=((2)/(1))']
#     one = ['y=(2)x+c', 'y=c+2x', '2x+c=y', 'c+2x=y']
#     two = ['5=(2)×1+c', '7=2×2+c', '5=1×2+c', '1×2+c=5', '2×1+c=5', '5=c+2×1', '5=c+1×2', 'c+2×1=5', 'c+1×2=5', '2+c=5',
#            'c+2=5', '5=2+c', '5=c+2', 'c=5-2', '5-2=c', '2×2+c=7', '2×2+c=7', 'c+2×2=7', '4+c=7', 'c+4=7', '7-4=c']
#     three = ['c=3', '3=c', '=3', '3']
#     four = ['y=2x+3', 'y=3+2x', '3+2x=y', '2x+3=y']
#
#     for solution in zero:
#         if not solution_checker.step_one(solution):
#             print(solution)
#
#     for solution in one:
#         if not solution_checker.step_two(solution):
#             print(solution)
#
#     for solution in two:
#         if not solution_checker.step_three(solution):
#             print(solution, 'two')
#
#     for solution in three:
#         if not solution_checker.step_four(solution):
#             print(solution, 'three')
#
#     for solution in four:
#         if not solution_checker.step_five(solution):
#             print(solution, 'four')
