from pathlib import Path
from fonctions.calendrier_du_championnat.lecture_calendrier import (
    parcourir_calendrier,
    extraire_dates_image,
    grouper_par_colonne,
)


def main():
    dossier = Path('test')
    images = sorted(str(p) for p in dossier.glob('image*.png'))
    for img in images:
        dates = extraire_dates_image(img)
        colonnes = grouper_par_colonne(dates)
        print(f"Image: {img}")
        for i, col in enumerate(colonnes, 1):
            print(f" Colonne {i}:")
            for d in col["dates"]:
                print(f"  - {d['date']} ({d['x']},{d['y']})")

    print("\nToutes les dates triées:")
    for d in parcourir_calendrier(images):
        print(f" - {d}")


if __name__ == '__main__':
    main()
