import re
from typing import Iterable, List, Dict
from PIL import Image
import pytesseract
from pytesseract import Output


def extraire_dates_image(path: str) -> List[Dict[str, int]]:
    """Extrait les dates (jj/mm/aaaa) présentes dans une image."""
    image = Image.open(path)
    data = pytesseract.image_to_data(image, output_type=Output.DICT)
    pattern = r"\d{2}/\d{2}/\d{4}"
    dates = []
    for text, x, y, w, h in zip(
        data["text"], data["left"], data["top"], data["width"], data["height"]
    ):
        txt = text.strip()
        if re.fullmatch(pattern, txt):
            dates.append({"date": txt, "x": x, "y": y, "w": w, "h": h})
    dates.sort(key=lambda d: (d["y"], d["x"]))
    return dates


def grouper_par_colonne(dates: List[Dict[str, int]], tolerance: int = 60):
    """Regroupe les dates par colonne selon leur abscisse."""
    colonnes: List[Dict[str, List[Dict[str, int]]]] = []
    for d in sorted(dates, key=lambda d: d["x"]):
        placed = False
        for col in colonnes:
            if abs(d["x"] - col["x"]) < tolerance:
                col["dates"].append(d)
                placed = True
                break
        if not placed:
            colonnes.append({"x": d["x"], "dates": [d]})
    for col in colonnes:
        col["dates"].sort(key=lambda d: d["y"])
    return colonnes


def parcourir_calendrier(images: Iterable[str]) -> List[str]:
    """Renvoie la liste unique des dates trouvées, triées chronologiquement."""
    vues = set()
    toutes = []
    for img in images:
        for d in extraire_dates_image(img):
            if d["date"] not in vues:
                vues.add(d["date"])
                toutes.append(d["date"])
    def ordre(date: str) -> tuple:
        j, m, a = map(int, date.split("/"))
        return (a, m, j)
    return sorted(toutes, key=ordre)


__all__ = [
    "extraire_dates_image",
    "grouper_par_colonne",
    "parcourir_calendrier",
]
