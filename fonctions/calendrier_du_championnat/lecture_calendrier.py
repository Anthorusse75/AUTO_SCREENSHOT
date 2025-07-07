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
    for text, x, y in zip(data["text"], data["left"], data["top"]):
        txt = text.strip()
        if re.fullmatch(pattern, txt):
            dates.append({"date": txt, "x": x, "y": y})
    dates.sort(key=lambda d: (d["y"], d["x"]))
    return dates


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
