"""
AstroOS — Priority 9: AstroDSL Lexer, Parser, & AST Domain

Provides a safe, declarative Domain-Specific Language (AstroDSL) for defining
custom astrological rules, yoga conditions, and timing predicates without requiring
arbitrary Python code execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional, Union


class TokenType(str, Enum):
    IDENTIFIER = "IDENTIFIER"
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COMMA = "COMMA"
    DOT = "DOT"
    EOF = "EOF"


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    column: int


class ASTNode:
    """Base class for all AstroDSL AST nodes."""
    pass


@dataclass
class LiteralNode(ASTNode):
    value: Union[str, int, float, bool]


@dataclass
class ListNode(ASTNode):
    elements: List[ASTNode]


@dataclass
class IdentifierNode(ASTNode):
    name: str


@dataclass
class AttributeAccessNode(ASTNode):
    target: ASTNode
    attribute: str


@dataclass
class FunctionCallNode(ASTNode):
    name: str
    args: List[ASTNode]


@dataclass
class BinaryOpNode(ASTNode):
    left: ASTNode
    operator: str  # '==', '!=', '<', '<=', '>', '>=', 'IN', 'NOT IN', 'AND', 'OR', '+', '-', '*', '/'
    right: ASTNode


@dataclass
class UnaryOpNode(ASTNode):
    operator: str  # 'NOT', '-'
    operand: ASTNode


@dataclass
class CustomRuleDefinition:
    rule_id: str
    name: str
    description: str
    dsl_source: str
    category: str = "custom_yoga"
    tags: List[str] = field(default_factory=list)
    author: str = "user"
    version: str = "1.0.0"
    created_at: str = ""


class AstroDSLSyntaxError(Exception):
    """Raised when AstroDSL lexing or parsing fails."""
    def __init__(self, message: str, line: int = 1, column: int = 1):
        super().__init__(f"AstroDSL Syntax Error [Line {line}, Col {column}]: {message}")
        self.message = message
        self.line = line
        self.column = column


class AstroDSLLexer:
    """Lexical analyzer converting raw AstroDSL string into Token sequence."""

    KEYWORDS = {"TRUE": True, "FALSE": False, "AND": "AND", "OR": "OR", "NOT": "NOT", "IN": "IN"}

    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.pos = 0
        self.line = 1
        self.column = 1

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= self.length:
            return "\0"
        return self.source[idx]

    def _advance(self) -> str:
        ch = self._peek()
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        return ch

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []

        while self.pos < self.length:
            ch = self._peek()

            # Skip whitespace
            if ch in " \t\r\n":
                self._advance()
                continue

            start_line = self.line
            start_col = self.column

            # String literal
            if ch in ('"', "'"):
                quote = self._advance()
                val_chars = []
                while self._peek() != "\0" and self._peek() != quote:
                    if self._peek() == "\\":
                        self._advance()
                    val_chars.append(self._advance())
                if self._peek() == "\0":
                    raise AstroDSLSyntaxError("Unterminated string literal", start_line, start_col)
                self._advance()  # closing quote
                tokens.append(Token(TokenType.STRING, "".join(val_chars), start_line, start_col))
                continue

            # Number literal
            if ch.isdigit() or (ch == "." and self._peek(1).isdigit()):
                num_chars = []
                has_dot = False
                while self._peek().isdigit() or (self._peek() == "." and not has_dot):
                    if self._peek() == ".":
                        has_dot = True
                    num_chars.append(self._advance())
                tokens.append(Token(TokenType.NUMBER, "".join(num_chars), start_line, start_col))
                continue

            # Identifiers / Keywords
            if ch.isalpha() or ch == "_":
                ident_chars = []
                while self._peek().isalnum() or self._peek() in "_-":
                    ident_chars.append(self._advance())
                word = "".join(ident_chars)
                word_upper = word.upper()

                if word_upper in ("TRUE", "FALSE"):
                    tokens.append(Token(TokenType.BOOLEAN, word_upper, start_line, start_col))
                elif word_upper in ("AND", "OR", "NOT", "IN"):
                    # Check for NOT IN
                    if word_upper == "NOT":
                        # peek next word
                        saved_pos = self.pos
                        saved_line = self.line
                        saved_col = self.column
                        # skip space
                        while self.pos < self.length and self._peek() in " \t\r\n":
                            self._advance()
                        next_ident = []
                        if self._peek().isalpha():
                            while self._peek().isalnum():
                                next_ident.append(self._advance())
                        if "".join(next_ident).upper() == "IN":
                            tokens.append(Token(TokenType.OPERATOR, "NOT IN", start_line, start_col))
                            continue
                        else:
                            # rewind
                            self.pos = saved_pos
                            self.line = saved_line
                            self.column = saved_col
                            tokens.append(Token(TokenType.OPERATOR, "NOT", start_line, start_col))
                    else:
                        tokens.append(Token(TokenType.OPERATOR, word_upper, start_line, start_col))
                else:
                    tokens.append(Token(TokenType.IDENTIFIER, word, start_line, start_col))
                continue

            # Operators and Delimiters
            if ch == "(":
                self._advance()
                tokens.append(Token(TokenType.LPAREN, "(", start_line, start_col))
            elif ch == ")":
                self._advance()
                tokens.append(Token(TokenType.RPAREN, ")", start_line, start_col))
            elif ch == "[":
                self._advance()
                tokens.append(Token(TokenType.LBRACKET, "[", start_line, start_col))
            elif ch == "]":
                self._advance()
                tokens.append(Token(TokenType.RBRACKET, "]", start_line, start_col))
            elif ch == ",":
                self._advance()
                tokens.append(Token(TokenType.COMMA, ",", start_line, start_col))
            elif ch == ".":
                self._advance()
                tokens.append(Token(TokenType.DOT, ".", start_line, start_col))
            elif ch in ("=", "!", "<", ">"):
                op_chars = [self._advance()]
                if self._peek() == "=":
                    op_chars.append(self._advance())
                op_str = "".join(op_chars)
                if op_str == "=":
                    op_str = "=="
                tokens.append(Token(TokenType.OPERATOR, op_str, start_line, start_col))
            elif ch in ("+", "-", "*", "/"):
                op_str = self._advance()
                tokens.append(Token(TokenType.OPERATOR, op_str, start_line, start_col))
            else:
                raise AstroDSLSyntaxError(f"Unexpected character '{ch}'", start_line, start_col)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens


class AstroDSLParser:
    """Recursive descent parser generating typed AST with depth limiting."""

    MAX_AST_DEPTH = 15

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _peek(self, offset: int = 1) -> Token:
        idx = min(self.pos + offset, len(self.tokens) - 1)
        return self.tokens[idx]

    def _advance(self) -> Token:
        tok = self._current()
        if tok.type != TokenType.EOF:
            self.pos += 1
        return tok

    def _match(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match_operator(self, *ops: str) -> bool:
        return self._current().type == TokenType.OPERATOR and self._current().value in ops

    def _expect(self, type_: TokenType, value: Optional[str] = None) -> Token:
        tok = self._current()
        if tok.type != type_ or (value is not None and tok.value != value):
            expected = f"'{value}'" if value else type_.value
            raise AstroDSLSyntaxError(f"Expected {expected}, got '{tok.value}'", tok.line, tok.column)
        return self._advance()

    def parse(self) -> ASTNode:
        ast = self._parse_expression(depth=1)
        if not self._match(TokenType.EOF):
            tok = self._current()
            raise AstroDSLSyntaxError(f"Unexpected token after expression end: '{tok.value}'", tok.line, tok.column)
        return ast

    def _parse_expression(self, depth: int) -> ASTNode:
        if depth > self.MAX_AST_DEPTH:
            raise AstroDSLSyntaxError(f"Maximum AST depth limit ({self.MAX_AST_DEPTH}) exceeded", self._current().line, self._current().column)
        return self._parse_logical_or(depth)

    def _parse_logical_or(self, depth: int) -> ASTNode:
        left = self._parse_logical_and(depth + 1)
        while self._match_operator("OR"):
            op_tok = self._advance()
            right = self._parse_logical_and(depth + 1)
            left = BinaryOpNode(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_logical_and(self, depth: int) -> ASTNode:
        left = self._parse_comparison(depth + 1)
        while self._match_operator("AND"):
            op_tok = self._advance()
            right = self._parse_comparison(depth + 1)
            left = BinaryOpNode(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_comparison(self, depth: int) -> ASTNode:
        left = self._parse_additive(depth + 1)
        while self._match_operator("==", "!=", "<", "<=", ">", ">=", "IN", "NOT IN"):
            op_tok = self._advance()
            right = self._parse_additive(depth + 1)
            left = BinaryOpNode(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_additive(self, depth: int) -> ASTNode:
        left = self._parse_multiplicative(depth + 1)
        while self._match_operator("+", "-"):
            op_tok = self._advance()
            right = self._parse_multiplicative(depth + 1)
            left = BinaryOpNode(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_multiplicative(self, depth: int) -> ASTNode:
        left = self._parse_unary(depth + 1)
        while self._match_operator("*", "/"):
            op_tok = self._advance()
            right = self._parse_unary(depth + 1)
            left = BinaryOpNode(left=left, operator=op_tok.value, right=right)
        return left

    def _parse_unary(self, depth: int) -> ASTNode:
        if self._match_operator("NOT", "-"):
            op_tok = self._advance()
            operand = self._parse_unary(depth + 1)
            return UnaryOpNode(operator=op_tok.value, operand=operand)
        return self._parse_primary(depth + 1)

    def _parse_primary(self, depth: int) -> ASTNode:
        tok = self._current()

        # Grouping (expr)
        if self._match(TokenType.LPAREN):
            self._advance()
            expr = self._parse_expression(depth + 1)
            self._expect(TokenType.RPAREN)
            return expr

        # List literal [el1, el2, ...]
        if self._match(TokenType.LBRACKET):
            self._advance()
            elements: List[ASTNode] = []
            if not self._match(TokenType.RBRACKET):
                elements.append(self._parse_expression(depth + 1))
                while self._match(TokenType.COMMA):
                    self._advance()
                    elements.append(self._parse_expression(depth + 1))
            self._expect(TokenType.RBRACKET)
            return ListNode(elements=elements)

        # Literals
        if self._match(TokenType.STRING):
            self._advance()
            return LiteralNode(value=tok.value)
        if self._match(TokenType.NUMBER):
            self._advance()
            num_val = float(tok.value) if "." in tok.value else int(tok.value)
            return LiteralNode(value=num_val)
        if self._match(TokenType.BOOLEAN):
            self._advance()
            return LiteralNode(value=(tok.value == "TRUE"))

        # Identifier, Function call, or Attribute Access
        if self._match(TokenType.IDENTIFIER):
            self._advance()
            node: ASTNode = IdentifierNode(name=tok.value)

            # Function call e.g. PLANET("Jupiter")
            if self._match(TokenType.LPAREN):
                self._advance()
                args: List[ASTNode] = []
                if not self._match(TokenType.RPAREN):
                    args.append(self._parse_expression(depth + 1))
                    while self._match(TokenType.COMMA):
                        self._advance()
                        args.append(self._parse_expression(depth + 1))
                self._expect(TokenType.RPAREN)
                node = FunctionCallNode(name=tok.value, args=args)

            # Chained dot attribute accesses e.g. .house, .is_combust, .rashi
            while self._match(TokenType.DOT):
                self._advance()
                attr_tok = self._expect(TokenType.IDENTIFIER)
                node = AttributeAccessNode(target=node, attribute=attr_tok.value)

            return node

        raise AstroDSLSyntaxError(f"Unexpected token '{tok.value}'", tok.line, tok.column)


def parse_astro_dsl(source: str) -> ASTNode:
    """Convenience helper to tokenize and parse AstroDSL string into an AST."""
    lexer = AstroDSLLexer(source)
    tokens = lexer.tokenize()
    parser = AstroDSLParser(tokens)
    return parser.parse()
