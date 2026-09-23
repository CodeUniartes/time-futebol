from datetime import datetime


def blank_order_info():
    return {
        "cliente": "",
        "numero_pedido": "",
        "observacao": "",
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
