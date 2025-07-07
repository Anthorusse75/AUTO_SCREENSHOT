#!/usr/bin/env python3
"""
Script de test final pour la nouvelle détection de combats.
"""
import sys
import os
sys.path.append('.')

import cv2
import numpy as np
from fonctions.calendrier_du_championnat.Fonctions_detection_Combats import detecter_combats_simple
from fonctions.detection_page import charger_image_cv2

class MockWindow:
    """Fenêtre simulée pour les tests."""
    def __init__(self):
        self.left = 0
        self.top = 0

class MockLogger:
    """Logger simulé pour les tests."""
    def debug(self, msg):
        print(f"DEBUG: {msg}")
    
    def info(self, msg):
        print(f"INFO: {msg}")
        
    def warning(self, msg):
        print(f"WARNING: {msg}")

def simuler_detection_sur_image(image_path):
    """Simule la détection sur une image de test."""
    print(f"\n=== TEST SUR {image_path} ===")
    
    if not os.path.exists(image_path):
        print(f"❌ Image non trouvée: {image_path}")
        return []
    
    # Charger l'image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Impossible de charger: {image_path}")
        return []
    
    print(f"Image chargée: {img.shape[1]}x{img.shape[0]}")
    
    # Simulation avec des valeurs fictives mais réalistes
    # (normalement pyautogui.screenshot capture depuis la fenêtre)
    
    # Mock objets
    logger = MockLogger()
    window = MockWindow()
    
    # Sauvegarde temporaire pour le test
    temp_screenshot = "temp_test_screenshot.png"
    cv2.imwrite(temp_screenshot, img)
    
    # Patch pour simuler pyautogui.screenshot
    import pyautogui
    from PIL import Image
    original_screenshot = pyautogui.screenshot
    
    def mock_screenshot(region=None):
        """Screenshot simulé depuis notre image de test."""
        pil_img = Image.open(temp_screenshot)
        if region:
            # region = (left, top, width, height)
            left, top, width, height = region
            pil_img = pil_img.crop((left, top, left + width, top + height))
        return pil_img
    
    # Remplacer temporairement pyautogui.screenshot
    pyautogui.screenshot = mock_screenshot
    
    try:
        # Test de détection
        combats = detecter_combats_simple(logger, window)
        print(f"Résultat: {len(combats)} combats détectés")
        
        for i, combat in enumerate(combats):
            print(f"  Combat {i+1}: {combat['type']} à {combat['coord']} (score: {combat.get('score', 0):.3f})")
        
        return combats
        
    finally:
        # Restaurer pyautogui.screenshot
        pyautogui.screenshot = original_screenshot
        # Nettoyer
        if os.path.exists(temp_screenshot):
            os.remove(temp_screenshot)

def main():
    """Test principal."""
    print("=== TEST DE LA NOUVELLE DÉTECTION DE COMBATS ===")
    
    # Vérification des prérequis
    test_dir = "test"
    if not os.path.exists(test_dir):
        print(f"❌ Dossier {test_dir} introuvable")
        return
    
    # Templates à vérifier
    templates = [
        "templates/calendrier_du_championnat/victoire_cdc.png",
        "templates/calendrier_du_championnat/egalite_cdc.png", 
        "templates/calendrier_du_championnat/defaite_cdc.png"
    ]
    
    print("Vérification des templates:")
    for template_path in templates:
        if os.path.exists(template_path):
            template = charger_image_cv2(template_path)
            if template is not None:
                print(f"  ✅ {os.path.basename(template_path)}: {template.shape[1]}x{template.shape[0]}")
            else:
                print(f"  ❌ {os.path.basename(template_path)}: erreur de chargement")
        else:
            print(f"  ❌ {os.path.basename(template_path)}: fichier manquant")
    
    # Test sur toutes les images
    images_test = [f for f in os.listdir(test_dir) if f.endswith('.png') and not f.endswith('_debug.png')]
    
    total_combats = 0
    for image_name in sorted(images_test):
        image_path = os.path.join(test_dir, image_name)
        combats = simuler_detection_sur_image(image_path)
        total_combats += len(combats)
    
    print(f"\n=== RÉSUMÉ ===")
    print(f"Images testées: {len(images_test)}")
    print(f"Total combats détectés: {total_combats}")
    print(f"Moyenne par image: {total_combats / len(images_test) if images_test else 0:.1f}")
    
    if total_combats == 0:
        print("\n⚠️  AUCUN COMBAT DÉTECTÉ!")
        print("Vérifiez:")
        print("- Que les templates sont corrects")
        print("- Que les seuils ne sont pas trop élevés")
        print("- Que les images de test contiennent bien des combats visibles")
    else:
        print("\n✅ Détection fonctionnelle!")

if __name__ == "__main__":
    main()
