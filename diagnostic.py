#!/usr/bin/env python3
"""
Script de diagnostic simple pour analyser les problèmes de détection.
"""
import os
import sys
sys.path.append('.')

# Test si on peut importer les modules
try:
    from configuration.config import COMBAT_MATCH_THRESHOLD
    print(f"✅ Configuration importée, seuil: {COMBAT_MATCH_THRESHOLD}")
except Exception as e:
    print(f"❌ Erreur import config: {e}")

try:
    import cv2
    print(f"✅ OpenCV version: {cv2.__version__}")
except Exception as e:
    print(f"❌ Erreur import OpenCV: {e}")

try:
    import numpy as np
    print(f"✅ NumPy version: {np.__version__}")
except Exception as e:
    print(f"❌ Erreur import NumPy: {e}")

# Vérification des fichiers
print("\n=== Vérification des fichiers ===")
templates_dir = "templates/calendrier_du_championnat"
if os.path.exists(templates_dir):
    print(f"✅ Dossier templates existe: {templates_dir}")
    files = os.listdir(templates_dir)
    for f in files:
        print(f"  - {f}")
else:
    print(f"❌ Dossier templates manquant: {templates_dir}")

test_dir = "test"
if os.path.exists(test_dir):
    print(f"✅ Dossier test existe: {test_dir}")
    files = [f for f in os.listdir(test_dir) if f.endswith('.png')]
    for f in files:
        path = os.path.join(test_dir, f)
        try:
            import cv2
            img = cv2.imread(path)
            if img is not None:
                print(f"  ✅ {f}: {img.shape[1]}x{img.shape[0]}")
            else:
                print(f"  ❌ {f}: impossible à charger")
        except:
            print(f"  ❌ {f}: erreur de lecture")
else:
    print(f"❌ Dossier test manquant: {test_dir}")

print("\n=== Test de template matching basique ===")
# Test sur la première image disponible
test_images = [f for f in os.listdir("test") if f.endswith('.png')]
if test_images and os.path.exists("templates/calendrier_du_championnat/victoire_cdc.png"):
    test_img_path = os.path.join("test", test_images[0])
    template_path = "templates/calendrier_du_championnat/victoire_cdc.png"
    
    try:
        import cv2
        img = cv2.imread(test_img_path, cv2.IMREAD_GRAYSCALE)
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        
        if img is not None and template is not None:
            result = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            print(f"Template matching sur {test_images[0]}:")
            print(f"  Score max: {max_val:.3f} à {max_loc}")
            print(f"  Positions avec score > 0.7: {len(np.where(result >= 0.7)[0])}")
            print(f"  Positions avec score > 0.8: {len(np.where(result >= 0.8)[0])}")
            print(f"  Positions avec score > 0.9: {len(np.where(result >= 0.9)[0])}")
        else:
            print("❌ Impossible de charger l'image ou le template")
    except Exception as e:
        print(f"❌ Erreur test template matching: {e}")

print("\n=== Diagnostic terminé ===")
