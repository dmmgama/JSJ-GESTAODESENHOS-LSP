"""
Utility functions for normalizing TIPO and ELEMENTO values to database keys.
"""
import re
from unidecode import unidecode


def normalize_tipo_display_to_key(tipo: str) -> str:
    """
    Normalize TIPO display value to database key.
    
    Examples:
        "Betão armado" -> "BETAO_ARMADO"
        "Planta de implantação" -> "PLANTA_DE_IMPLANTACAO"
        "" -> ""
    
    Args:
        tipo: Display value from AutoCAD attribute
        
    Returns:
        Normalized key (uppercase, no accents, underscores for spaces)
    """
    if not tipo or tipo.strip() == "":
        return ""
    
    # Remove accents
    normalized = unidecode(tipo)
    
    # Uppercase
    normalized = normalized.upper()
    
    # Replace spaces with underscores
    normalized = normalized.replace(" ", "_")
    
    # Remove special characters (keep only A-Z, 0-9, _)
    normalized = re.sub(r'[^A-Z0-9_]', '', normalized)
    
    return normalized


def normalize_elemento_to_key(elemento: str) -> str:
    """
    Normalize ELEMENTO value to database key.
    
    Examples:
        "Fundações" -> "FUNDACOES"
        "LAJ" -> "LAJ"
        "" -> ""
    
    Args:
        elemento: Element value from AutoCAD attribute
        
    Returns:
        Normalized key (uppercase, no accents)
    """
    if not elemento or elemento.strip() == "":
        return ""
    
    # Strip whitespace
    normalized = elemento.strip()
    
    # Remove accents
    normalized = unidecode(normalized)
    
    # Uppercase
    normalized = normalized.upper()
    
    return normalized
