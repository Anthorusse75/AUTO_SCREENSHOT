from pathlib import Path
from fonctions.calendrier_du_championnat.lecture_calendrier import parcourir_calendrier


def main():
    dossier = Path('test')
    images = sorted(str(p) for p in dossier.glob('image*.png'))
    dates = parcourir_calendrier(images)
    for d in dates:
        print(d)


if __name__ == '__main__':
    main()
