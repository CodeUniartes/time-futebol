import pytest

from src.services.cart_service import CartService

TEAM = {"id": "galo", "name": "Galo"}
MODEL = {"id": "branca", "name": "Branca"}
CATEGORY = {"id": "numero_costas", "name": "Número Costas"}


def test_add_same_item_merges_quantity():
    cart = CartService()
    cart.add_item(TEAM, MODEL, CATEGORY, "0", 1)
    cart.add_item(TEAM, MODEL, CATEGORY, "0", 2)
    assert cart.total_items() == 1
    assert cart.total_quantities() == 3


def test_same_label_different_team_stays_separate():
    cart = CartService()
    cart.add_item(TEAM, MODEL, CATEGORY, "0", 1)
    cart.add_item({"id": "cruzeiro", "name": "Cruzeiro"}, MODEL, CATEGORY, "0", 1)
    assert cart.total_items() == 2


def test_label_match_is_case_insensitive():
    cart = CartService()
    cart.add_item(TEAM, MODEL, CATEGORY, "A", 1)
    cart.add_item(TEAM, MODEL, CATEGORY, "a", 1)
    assert cart.total_items() == 1


@pytest.mark.parametrize("quantity", [0, -1])
def test_rejects_non_positive_quantity(quantity):
    with pytest.raises(ValueError):
        CartService().add_item(TEAM, MODEL, CATEGORY, "1", quantity)


def test_roundtrip_to_list_and_load_list():
    cart = CartService()
    cart.add_item(TEAM, MODEL, CATEGORY, "7", 2)
    other = CartService()
    other.load_list(cart.to_list())
    assert other.to_list() == cart.to_list()
