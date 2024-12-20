from pyudunits2 import UnitSystem, UnresolvableUnitException
from pyudunits2._unit import Unit
import pytest


@pytest.mark.parametrize(
    ["unit_spec", "definition"],
    [
        ["m", "meter"],
        ["Bm", "(lg(re 1·0.001·watt))"],
        ["1e-3 Bm", "0.001·(lg(re 1·0.001·watt))"],
        ["mBm", "0.001·(lg(re 1·0.001·watt))"],
        ["km", "1000·meter"],
        ["m 1000", "meter·1000"],  # The definition isn't fully normalised (yet).
        ["kmetres", "1000·meter"],
        ["kilom", "1000·meter"],
    ],
)
def test__unit__expansion(
    simple_unit_system: UnitSystem, unit_spec: str, definition: str
):
    # We have a non defined plural name, with a symbol based prefix.
    unit = simple_unit_system.unit(unit_spec)
    assert isinstance(unit, Unit)
    # TODO: Fix this.
    assert str(unit.expanded()) == definition


@pytest.mark.parametrize(
    "unit_spec",
    [
        "other",
        "deci",  # A valid prefix.
    ],
)
def test__unit__undefined_unit(simple_unit_system: UnitSystem, unit_spec):
    match = rf"Unable to convert the identifier '{unit_spec}' into a unit in the unit system"
    with pytest.raises(UnresolvableUnitException, match=match):
        simple_unit_system.unit(unit_spec)


@pytest.mark.parametrize(
    ["unit_lhs", "unit_rhs"],
    [
        ["km", "1000 m"],
    ],
)
def test__unit__symbolic_eq(
    simple_unit_system: UnitSystem, unit_lhs: str, unit_rhs: str
):
    # We have a non defined plural name, with a symbol based prefix.
    unit1 = simple_unit_system.unit(unit_lhs)
    unit2 = simple_unit_system.unit(unit_rhs)

    assert unit1 == unit2
