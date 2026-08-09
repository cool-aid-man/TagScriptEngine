from __future__ import annotations, division

import math
import operator
from typing import Any, Callable, Dict, Final, List, Tuple, cast
from typing import Optional as TypingOptional

from pyparsing import (
    CaselessLiteral,
    Combine,
    Forward,
    Group,
    Literal,
    Optional,
    ParserElement,
    Word,
    ZeroOrMore,
    alphas,
    nums,
    one_of,
)

from ..interface import Block
from ..interpreter import Context

__all__: Tuple[str, ...] = ("MathBlock",)


# Floats raise OverflowError themselves, but `int ** int` is arbitrary
# precision - it never overflows, it just keeps computing. round/trunc/abs all
# return ints, so `{math:round(9)^round(9)^round(9)}` is 9**387420489 and hangs
# the event loop. Must be checked before the operation, not caught after.
MAX_EXPONENT: Final[int] = 1000
MAX_RESULT_DIGITS: Final[int] = 1000


class _MathLimitError(Exception):
    """Raised when an expression would produce an unreasonably large result."""


def _guarded_pow(base: Any, exponent: Any) -> Any:
    """``operator.pow`` with a ceiling on the result size."""
    try:
        if abs(exponent) > MAX_EXPONENT:
            raise _MathLimitError(f"exponent {exponent} exceeds the maximum of {MAX_EXPONENT}")
        # log10 estimates the digit count without computing the value.
        if base and abs(exponent) * math.log10(abs(base)) > MAX_RESULT_DIGITS:
            raise _MathLimitError(f"the result would exceed {MAX_RESULT_DIGITS} digits")
    except (TypeError, ValueError) as error:
        raise _MathLimitError(str(error)) from error
    return operator.pow(base, exponent)


class NumericStringParser(object):
    """
    Most of this code comes from the fourFn.py pyparsing example

    """

    def pushFirst(self, strg: Any, loc: Any, toks: Any) -> Any:
        self.exprStack.append(toks[0])

    def pushUMinus(self, strg: Any, loc: Any, toks: Any) -> Any:
        if toks and toks[0] == "-":
            self.exprStack.append("unary -")

    def __init__(self) -> None:
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        point: Literal = Literal(".")
        e: CaselessLiteral = CaselessLiteral("E")
        fnumber: Combine = Combine(
            Word("+-" + nums, nums)
            + Optional(point + Optional(Word(nums)))
            + Optional(e + Word("+-" + nums, nums))
        )
        ident: Word = Word(alphas, alphas + nums + "_$")
        mod: Literal = Literal("%")
        plus: Literal = Literal("+")
        minus: Literal = Literal("-")
        mult: Literal = Literal("*")
        iadd: Literal = Literal("+=")
        imult: Literal = Literal("*=")
        idiv: Literal = Literal("/=")
        isub: Literal = Literal("-=")
        div: Literal = Literal("/")
        lpar: ParserElement = Literal("(").suppress()
        rpar: ParserElement = Literal(")").suppress()
        addop: ParserElement = plus | minus
        multop: ParserElement = mult | div | mod
        iop: ParserElement = iadd | isub | imult | idiv
        expop: Literal = Literal("^")
        pi: CaselessLiteral = CaselessLiteral("PI")
        expr: Forward = Forward()
        atom: ParserElement = (
            (
                Optional(one_of("- +"))
                + (ident + lpar + expr + rpar | pi | e | fnumber).set_parse_action(self.pushFirst)
            )
            | Optional(one_of("- +")) + Group(lpar + expr + rpar)
        ).set_parse_action(self.pushUMinus)
        # by defining exponentiation as "atom [ ^ factor ]..." instead of
        # "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-right
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor: Forward = Forward()
        factor << atom + ZeroOrMore((expop + factor).set_parse_action(self.pushFirst))  # type: ignore
        term: ParserElement = factor + ZeroOrMore(
            (multop + factor).set_parse_action(self.pushFirst)
        )
        expr << term + ZeroOrMore((addop + term).set_parse_action(self.pushFirst))  # type: ignore
        final: ParserElement = expr + ZeroOrMore((iop + expr).set_parse_action(self.pushFirst))
        # addop_term = ( addop + term ).set_parse_action( self.pushFirst )
        # general_term = term + ZeroOrMore( addop_term ) | OneOrMore( addop_term)
        # expr <<  general_term
        self.bnf: ParserElement = final
        # map operator symbols to corresponding arithmetic operations
        epsilon: float = 1e-12
        self.opn: Dict[str, Callable[[Any, Any], Any]] = {
            "+": operator.add,
            "-": operator.sub,
            "+=": operator.iadd,
            "-=": operator.isub,
            "*": operator.mul,
            "*=": operator.imul,
            "/": operator.truediv,
            "/=": operator.itruediv,
            "^": _guarded_pow,
            "%": operator.mod,
        }
        self.fn: Dict[str, Any] = {
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "sinh": math.sinh,
            "cosh": math.cosh,
            "tanh": math.tanh,
            "exp": math.exp,
            "abs": abs,
            "trunc": lambda a: int(a),
            "round": round,
            "sgn": lambda a: abs(a) > epsilon and ((a > 0) - (a < 0)) or 0,
            "log": lambda a: math.log(a, 10),
            "ln": math.log,
            "log2": math.log2,
            "sqrt": math.sqrt,
        }

    def evaluateStack(self, s: List[Any]) -> Any:
        op = s.pop()
        if op == "unary -":
            return -self.evaluateStack(s)
        if op in self.opn:
            op2 = self.evaluateStack(s)
            op1 = self.evaluateStack(s)
            return self.opn[op](op1, op2)
        elif op == "PI":
            return math.pi  # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in self.fn:
            return self.fn[op](self.evaluateStack(s))
        elif op[0].isalpha():
            return 0
        else:
            return float(op)

    def eval(self, num_string: str, parse_all: bool = True) -> Any:
        self.exprStack = []
        results = self.bnf.parse_string(num_string, parse_all)  # noqa: F841
        return self.evaluateStack(self.exprStack[:])


NSP: NumericStringParser = NumericStringParser()


class MathBlock(Block):
    """
    The math block performs mathematical calculations from the given payload expression.

    Supports standard arithmetic operators, exponentiation, modulo, in-place operators,
    mathematical functions, and constants.

    **Supported Operators:**

    +----------+---------------------+
    | Operator | Description         |
    +==========+=====================+
    | ``+``    | Addition            |
    +----------+---------------------+
    | ``-``    | Subtraction         |
    +----------+---------------------+
    | ``*``    | Multiplication      |
    +----------+---------------------+
    | ``/``    | Division            |
    +----------+---------------------+
    | ``^``    | Exponentiation      |
    +----------+---------------------+
    | ``%``    | Modulo              |
    +----------+---------------------+
    | ``+=``   | In-place addition   |
    +----------+---------------------+
    | ``-=``   | In-place subtraction|
    +----------+---------------------+
    | ``*=``   | In-place multiply   |
    +----------+---------------------+
    | ``/=``   | In-place division   |
    +----------+---------------------+

    **Supported Functions:**
    ``sin``, ``cos``, ``tan``, ``sinh``, ``cosh``, ``tanh``,
    ``exp``, ``abs``, ``trunc``, ``round``, ``sgn``,
    ``log`` (base 10), ``ln`` (natural), ``log2``, ``sqrt``

    **Constants:** ``PI``, ``E``

    **Usage:** ``{math:<expression>}``

    **Aliases:** ``m, +, calc``

    **Payload:** expression

    **Parameter:** None

    **Examples:** ::

        {math:2+3}
        # 5

        {m:round(7/3)}
        # 2

        {calc:sin(PI/2)}
        # 1.0

        {+:7*6}
        # 42

        {m:sqrt(144)}
        # 12.0

    .. note::
        An expression with no real, finite result - ``1/0``, ``5%0``, ``sqrt(-1)``,
        ``(0-2)^0.5`` - is declined, so the raw ``{math:...}`` stays in the message.
        A bare ``{math}`` is declined too, which is what lets a variable named
        ``math`` be read.
    """

    ACCEPTED_NAMES: Tuple[str, ...] = ("math", "m", "+", "calc")

    def process(self, ctx: Context) -> TypingOptional[str]:
        try:
            result = NSP.eval(cast(str, ctx.verb.payload).strip(" "))
        except _MathLimitError as error:
            # Report this one - a raw `{math:...}` gives no hint it was refused.
            return f"`MATH LIMIT EXCEEDED ({error})`"
        except Exception:
            return None
        # Handle ints first without `isfinite()`, as float coercion raises OverflowError on large ints.
        if isinstance(result, int):
            return str(result)
        # Decline complex numbers (non-real results) to prevent leaking Python repr into output.
        if not isinstance(result, float) or not math.isfinite(result):
            return None
        return str(result)
