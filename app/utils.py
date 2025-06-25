def format_amount(amount):
    try:
        # Convertir en entier si possible, sinon float
        if isinstance(amount, float):
            # Format float avec 2 décimales, espace pour milliers
            parts = f"{amount:,.2f}".split(".")
            parts[0] = parts[0].replace(",", " ")
            if parts[1] == "00":
                return parts[0]
            return f"{parts[0]}.{parts[1]}"
        else:
            # Format entier avec espace
            return f"{int(amount):,}".replace(",", " ")
    except Exception:
        return str(amount)

