#!/usr/bin/env python3
"""
Script pour créer et tester les templates du journal de guerre de guildes.
"""

import os
import sys
import cv2
import numpy as np
from PIL import Image

# Ajouter le chemin du projet
sys.path.append('.')

from fonctions.detection_page import charger_image_cv2


def creer_templates_manquants():
    """Crée les templates manquants en analysant les images de test."""
    print("=== Création des templates manquants ===\n")
    
    # Créer les dossiers s'ils n'existent pas
    os.makedirs("templates/journal_de_guerre_de_guildes/onglets", exist_ok=True)
    os.makedirs("templates/journal_de_guerre_de_guildes/limites", exist_ok=True)
    
    # Analyser les images de test pour identifier les zones importantes
    images_test = [f for f in os.listdir("test") if "Journal" in f and f.endswith('.png')]
    
    if not images_test:
        print("❌ Aucune image de test trouvée")
        return
    
    print(f"📁 Images de test trouvées : {len(images_test)}")
    for img in images_test:
        print(f"  - {img}")
    
    # Analyser la première image d'attaque
    images_attaque = [img for img in images_test if "attaque" in img.lower()]
    images_defense = [img for img in images_test if "defense" in img.lower()]
    
    if images_attaque:
        analyser_image_pour_templates(images_attaque[0], "attaque")
    
    if images_defense:
        analyser_image_pour_templates(images_defense[0], "defense")


def analyser_image_pour_templates(nom_image, type_journal):
    """Analyse une image pour identifier les zones de templates."""
    chemin_image = os.path.join("test", nom_image)
    print(f"\n🔍 Analyse de {nom_image} pour type '{type_journal}'")
    
    # Charger l'image
    img = cv2.imread(chemin_image)
    if img is None:
        print(f"❌ Impossible de charger {chemin_image}")
        return
    
    print(f"📐 Dimensions : {img.shape[1]}x{img.shape[0]}")
    
    # Suggestions de zones à extraire pour les templates
    print("\n💡 Suggestions de zones importantes à extraire :")
    print("1. Zone onglet (en haut) - environ (200, 50, 150, 30)")
    print("2. Zone informations combat - chercher des patterns répétitifs")
    print("3. Zone de scroll - bords gauche/droit")
    
    # Créer une version annotée pour aider à identifier les zones
    img_annotee = img.copy()
    
    # Marquer quelques zones d'intérêt
    cv2.rectangle(img_annotee, (200, 50), (350, 80), (0, 255, 0), 2)  # Zone onglet
    cv2.rectangle(img_annotee, (100, 100), (500, 600), (255, 0, 0), 2)  # Zone contenu
    
    # Sauvegarder l'image annotée
    nom_sortie = f"test/{type_journal}_zones_annotees.png"
    cv2.imwrite(nom_sortie, img_annotee)
    print(f"💾 Image annotée sauvée : {nom_sortie}")


def tester_detection_basique():
    """Test basique de détection sur les images existantes."""
    print("\n=== Test de détection basique ===")
    
    # Tester sur la première image d'attaque
    images_attaque = [f for f in os.listdir("test") if "attaque" in f.lower() and f.endswith('.png')]
    
    if not images_attaque:
        print("❌ Aucune image d'attaque trouvée")
        return
    
    image_test = images_attaque[0]
    chemin_image = os.path.join("test", image_test)
    
    print(f"🧪 Test sur : {image_test}")
    
    # Charger l'image
    img = charger_image_cv2(chemin_image)
    if img is None:
        print("❌ Impossible de charger l'image")
        return
    
    print(f"✅ Image chargée : {img.shape}")
    
    # Tester la détection de patterns
    detecter_patterns_combats(img)


def detecter_patterns_combats(img):
    """Détecte des patterns répétitifs qui pourraient être des combats."""
    print("\n🔍 Recherche de patterns répétitifs...")
    
    # Convertir en niveaux de gris si nécessaire
    if len(img.shape) == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = img
    
    # Chercher des contours qui pourraient être des éléments d'interface
    contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    rectangles = []
    for contour in contours:
        # Approximation rectangulaire
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        if len(approx) == 4:  # Rectangle
            x, y, w, h = cv2.boundingRect(contour)
            if 20 < w < 200 and 10 < h < 50:  # Taille raisonnable pour un élément d'interface
                rectangles.append((x, y, w, h))
    
    print(f"📊 Rectangles détectés : {len(rectangles)}")
    
    # Grouper par taille similaire
    groupes_taille = {}
    for rect in rectangles:
        x, y, w, h = rect
        cle_taille = f"{w//10}x{h//10}"  # Grouper par dizaines de pixels
        if cle_taille not in groupes_taille:
            groupes_taille[cle_taille] = []
        groupes_taille[cle_taille].append(rect)
    
    # Afficher les groupes significatifs
    for taille, rects in groupes_taille.items():
        if len(rects) >= 3:  # Au moins 3 éléments similaires
            print(f"  - Groupe {taille} : {len(rects)} éléments")


def creer_template_exemple():
    """Crée un template d'exemple pour les informations de combat."""
    print("\n🛠️ Création d'un template d'exemple...")
    
    # Créer un template simple pour tester
    template = np.ones((30, 100), dtype=np.uint8) * 128  # Gris moyen
    
    # Ajouter quelques éléments pour simuler une interface
    cv2.rectangle(template, (5, 5), (95, 25), 200, -1)  # Rectangle clair
    cv2.rectangle(template, (10, 10), (90, 20), 100, 2)  # Bordure
    
    # Sauvegarder
    chemin_template = "templates/journal_de_guerre_de_guildes/informations_combat.png"
    cv2.imwrite(chemin_template, template)
    print(f"💾 Template d'exemple créé : {chemin_template}")


def main():
    print("🚀 Script de création et test des templates JGG")
    print("=" * 50)
    
    # Vérifier l'existence du dossier test
    if not os.path.exists("test"):
        print("❌ Dossier test non trouvé")
        return
    
    # Analyser les images existantes
    creer_templates_manquants()
    
    # Créer un template d'exemple
    creer_template_exemple()
    
    # Test basique
    tester_detection_basique()
    
    print("\n✅ Script terminé")
    print("\n📝 Actions suivantes recommandées :")
    print("1. Examiner les images annotées dans le dossier test/")
    print("2. Créer manuellement les templates manquants :")
    print("   - templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png")
    print("   - templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png")
    print("   - templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png")
    print("   - templates/journal_de_guerre_de_guildes/informations_combat.png")
    print("3. Ajuster les seuils de détection si nécessaire")


if __name__ == "__main__":
    main()
