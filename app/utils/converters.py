"""Utilitários de conversão de tipos."""


def safe_float(val):
    """Converte valor para float de forma segura, retornando None se inválido."""
    if val is None or val == "":
        return None
    try:
        s = str(val).strip().replace(",", ".")
        return float(s) if s else None
    except (ValueError, TypeError):
        return None
