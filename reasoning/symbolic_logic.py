"""Simple symbolic logic helpers for deterministic reasoning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class Proposition:
    """Represents a boolean proposition."""

    name: str
    value: bool


class LogicEngine:
    """Evaluate logical expressions composed of propositions."""

    def __init__(self, propositions: Dict[str, bool]) -> None:
        self.propositions = propositions

    def evaluate(self, expression: str) -> bool:
        """Evaluate a simple logical expression using AND/OR/NOT."""

        tokens = expression.replace("(", " ( ").replace(")", " ) ").split()
        return self._evaluate_tokens(tokens)

    def _evaluate_tokens(self, tokens: list[str]) -> bool:
        stack: list[str] = []
        for token in tokens:
            if token == ")":
                clause_tokens: list[str] = []
                while stack and stack[-1] != "(":
                    clause_tokens.append(stack.pop())
                if not stack:
                    raise ValueError("Unbalanced parentheses in expression")
                stack.pop()
                clause_tokens.reverse()
                result = self._resolve_clause(clause_tokens)
                stack.append("true" if result else "false")
            else:
                stack.append(token)
        return self._resolve_clause(stack)

    def _resolve_clause(self, tokens: list[str]) -> bool:
        result: bool | None = None
        operator = "AND"
        index = 0
        while index < len(tokens):
            token = tokens[index]
            if token.upper() in {"AND", "OR"}:
                operator = token.upper()
            elif token.upper() == "NOT":
                index += 1
                operand = self._token_value(tokens[index])
                value = not operand
                result = self._apply_operator(result, value, operator)
            elif token.lower() in {"true", "false"}:
                value = token.lower() == "true"
                result = self._apply_operator(result, value, operator)
            else:
                value = self._token_value(token)
                result = self._apply_operator(result, value, operator)
            index += 1
        if result is None:
            raise ValueError("Expression could not be evaluated")
        return result

    def _token_value(self, token: str) -> bool:
        if token not in self.propositions:
            raise KeyError(f"Unknown proposition: {token}")
        return self.propositions[token]

    @staticmethod
    def _apply_operator(current: bool | None, value: bool, operator: str) -> bool:
        if current is None:
            return value
        if operator == "AND":
            return current and value
        if operator == "OR":
            return current or value
        raise ValueError(f"Unsupported operator: {operator}")
