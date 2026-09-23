from src.models.cart_models import CartItem


class CartService:
    def __init__(self):
        self.items = []

    def add_item(self, team, model, category, item_label, quantity):
        quantity = int(quantity or 0)
        if quantity <= 0:
            raise ValueError("A quantidade precisa ser maior que zero.")
        item_label = str(item_label or "").strip()
        if not item_label:
            raise ValueError("Informe o item.")
        if not team or not model:
            raise ValueError("Selecione time e camisa/modelo antes de adicionar.")

        new_item = CartItem(
            team_id=team.get("id", ""),
            team_name=team.get("name", ""),
            model_id=model.get("id", ""),
            model_name=model.get("name", ""),
            category_id=category["id"],
            category_name=category["name"],
            item_label=item_label,
            quantity=quantity,
        )
        for item in self.items:
            if item.key == new_item.key:
                item.quantity += quantity
                return item
        self.items.append(new_item)
        return new_item

    def set_quantity(self, index, quantity):
        quantity = int(quantity or 0)
        if quantity <= 0:
            raise ValueError("A quantidade precisa ser maior que zero.")
        self.items[index].quantity = quantity

    def remove(self, index):
        if 0 <= index < len(self.items):
            self.items.pop(index)

    def clear(self):
        self.items.clear()

    def total_items(self):
        return len(self.items)

    def total_quantities(self):
        return sum(item.quantity for item in self.items)

    def to_list(self):
        return [item.to_dict() for item in self.items]

    def load_list(self, items):
        self.items = [CartItem.from_dict(item) for item in items or []]
