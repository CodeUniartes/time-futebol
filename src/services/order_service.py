from datetime import datetime

from src.utils.json_utils import load_json, save_json
from src.utils.path_utils import SAVED_ORDERS_DIR, ensure_dir
from src.utils.text_utils import safe_filename


class OrderService:
    def __init__(self):
        ensure_dir(SAVED_ORDERS_DIR)

    def save_order(self, order_info, selected_team_id, selected_model_id, cart_items):
        number = safe_filename(order_info.get("numero_pedido", ""), "pedido")
        client = safe_filename(order_info.get("cliente", ""), "cliente")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = SAVED_ORDERS_DIR / f"{number}_{client}_{timestamp}.json"
        save_json(
            path,
            {
                "order": order_info,
                "selected_team_id": selected_team_id,
                "selected_model_id": selected_model_id,
                "items": [item.to_dict() for item in cart_items],
                "saved_at": datetime.now().isoformat(timespec="seconds"),
            },
        )
        return path

    def list_orders(self):
        ensure_dir(SAVED_ORDERS_DIR)
        return sorted(SAVED_ORDERS_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)

    def load_order(self, path):
        return load_json(path, {})
