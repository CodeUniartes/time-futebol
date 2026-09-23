from dataclasses import asdict, dataclass


@dataclass
class CartItem:
    team_id: str
    team_name: str
    model_id: str
    model_name: str
    category_id: str
    category_name: str
    item_label: str
    quantity: int

    @property
    def key(self):
        return (
            self.team_id,
            self.model_id,
            self.category_id,
            self.item_label.casefold(),
        )

    @property
    def source_label(self):
        if self.team_name and self.model_name:
            return f"{self.team_name} / {self.model_name}"
        return self.team_name or self.model_name or "Sem time/modelo"

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(
            team_id=data.get("team_id", ""),
            team_name=data.get("team_name", ""),
            model_id=data.get("model_id", ""),
            model_name=data.get("model_name", ""),
            category_id=data.get("category_id", ""),
            category_name=data.get("category_name", ""),
            item_label=data.get("item_label", ""),
            quantity=int(data.get("quantity", 0) or 0),
        )
