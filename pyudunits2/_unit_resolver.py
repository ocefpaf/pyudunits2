from __future__ import annotations

import logging
import typing

from . import _expr_graph as unit_graph
from ._expr_graph import Identifier, Node, Visitor
from ._unit import DefinedUnit, Unit
from ._exceptions import UnresolvableUnitException


if typing.TYPE_CHECKING:
    # Note that UnitSystem imports this resolver, so we must only access
    # _unit_system when type checking to avoid circularity.
    from ._unit_system import UnitSystem


_log = logging.getLogger(__name__)


class UnitNode(Identifier):
    content: Unit


class ToBasisVisitor(Visitor):
    def __init__(self, identifier_lookup: IdentifierLookupVisitor):
        self._identifier_lookup = identifier_lookup

    def generic_visit(self, node: Node):
        if isinstance(node, unit_graph.Terminal):
            return node
        elif isinstance(node, unit_graph.BinaryOp):
            return type(node)(self.visit(node.lhs), self.visit(node.rhs))
        else:
            raise ValueError(f"Not yet supported {type(node)}")

    def visit_Shift(self, node: unit_graph.Shift):
        return unit_graph.Shift(
            self.visit(node.unit),
            self.visit(node.shift_from),
        )

    def visit_Identifier(self, node: unit_graph.Identifier):
        return self.visit(self._identifier_lookup.visit(node))

    def visit_UnitNode(self, node: UnitNode):
        from ._grammar import parse

        if isinstance(node.content, DefinedUnit):
            # Substitute the identifiers.
            unit_expr = self._identifier_lookup.visit(
                parse(node.content._unit_raw),
            )
            # Now potentially expand the derived units identified
            # until there are none left.
            return self.visit(unit_expr)

        return node


class IdentifierLookupVisitor(Visitor):
    # Warning: not yet recursive. See ToBasisVisitor
    def __init__(self, unit_system: UnitSystem):
        self._unit_system = unit_system
        super().__init__()

    if typing.TYPE_CHECKING:

        def visit(self, node: Node) -> unit_graph.Node:
            pass

    def generic_visit(self, node: Node):
        if isinstance(node, unit_graph.Terminal):
            return node
        elif isinstance(node, unit_graph.BinaryOp):
            return type(node)(self.visit(node.lhs), self.visit(node.rhs))
        elif isinstance(node, unit_graph.Shift):
            return unit_graph.Shift(self.visit(node.unit), node.shift_from)
        else:
            raise NotImplementedError(f"Node {type(node)} not implemented")

    def visit_Identifier(self, node: Identifier) -> Node:
        if node.content in self._unit_system._names:
            return UnitNode(self._unit_system._names[node.content])
        if node.content in self._unit_system._symbols:
            return UnitNode(self._unit_system._symbols[node.content])
        # TODO: Aliases.

        if node.content in self._unit_system._alias_names:
            return UnitNode(self._unit_system._alias_names[node.content])

        if node.content in self._unit_system._alias_symbols:
            return UnitNode(self._unit_system._alias_symbols[node.content])

        for prefix_name, prefix in self._unit_system._prefix_names.items():
            # TODO: We shouldn't strip off more than one prefix.
            #  (e.g. nautical_mile)

            if node.content.startswith(prefix_name):
                # TODO: Maybe we shouldn't match if it is a named prefix but a
                #  symbol unit e.g. kilom. The inverse also true e.g. kmeter
                return unit_graph.Multiply(
                    self._prefix_value(prefix.value),
                    self.visit(Identifier(node.content[len(prefix_name) :])),
                )
        for prefix_symbol, prefix in self._unit_system._prefix_symbols.items():
            if node.content.startswith(prefix_symbol):
                return unit_graph.Multiply(
                    self._prefix_value(prefix.value),
                    self.visit(Identifier(node.content[len(prefix_symbol) :])),
                )
        raise UnresolvableUnitException(
            f"Unable to convert the identifier '{node.content}' into a unit "
            "in the unit system"
        )

    def _prefix_value(self, value: str) -> unit_graph.Node:
        if "e" in value:
            number, _, exponent = value.partition("e")
            if "." in number:
                number = float(number)
            else:
                number = int(number)

            if "." in exponent:
                exponent = float(exponent)
            else:
                exponent = int(exponent)

            return unit_graph.Raise(
                unit_graph.Number(number),
                unit_graph.Number(exponent),
            )
        else:
            if "." in value:
                number = float(value)
            else:
                number = int(value)
            return unit_graph.Number(number)
