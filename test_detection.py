#!/usr/bin/env python3
"""
Script de test pour analyser la détection de combats sur les images d'exemple.
"""
import os
import cv2
import numpy as np
from PIL import Image

def analyser_image_test(image_path):
    """Analyse une image de test pour comprendre la structure."""
    print(f"\n=== Analyse de {image_path} ===")
    
    # Chargement de l'image
    img = cv2.imread(image_path)
    if img is None:
        print(f"Erreur: Impossible de charger {image_path}")
        return
    
    # Conversion en niveaux de gris
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    print(f"Dimensions: {gray.shape[1]}x{gray.shape[0]}")
    
    # Définition des colonnes comme dans le code
    colonnes = [
        {"nom": "Lundi", "x_start": 78, "x_end": 310},
        {"nom": "Mardi", "x_start": 324, "x_end": 556},
        {"nom": "Mercredi", "x_start": 570, "x_end": 802},
        {"nom": "Jeudi", "x_start": 816, "x_end": 1048},
        {"nom": "Vendredi", "x_start": 1062, "x_end": 1294}
    ]
    
    # Zone verticale
    y_start = 120
    y_end = 780
    
    # Test avec les templates
    templates = [
        ("templates/calendrier_du_championnat/victoire_cdc.png", "victoire"),
        ("templates/calendrier_du_championnat/egalite_cdc.png", "egalite"),
        ("templates/calendrier_du_championnat/defaite_cdc.png", "defaite"),
    ]
    
    total_detections = 0
    
    for template_path, type_combat in templates:
        if not os.path.exists(template_path):
            print(f"⚠️  Template manquant: {template_path}")
            continue
            
        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
        if template is None:
            print(f"⚠️  Impossible de charger: {template_path}")
            continue
        
        print(f"\n--- Test {type_combat} ---")
        print(f"Template dimensions: {template.shape[1]}x{template.shape[0]}")
        
        # Test global
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        locations = np.where(result >= 0.7)
        global_detections = len(locations[0])
        print(f"Détections globales (seuil 0.7): {global_detections}")
        
        # Test par colonne
        for col_idx, colonne in enumerate(colonnes):
            zone_x_start = max(0, colonne["x_start"])
            zone_x_end = min(gray.shape[1], colonne["x_end"])
            zone_y_start = max(0, y_start)
            zone_y_end = min(gray.shape[0], y_end)
            
            zone = gray[zone_y_start:zone_y_end, zone_x_start:zone_x_end]
            
            if zone.size == 0:
                continue
                
            result_zone = cv2.matchTemplate(zone, template, cv2.TM_CCOEFF_NORMED)
            locations_zone = np.where(result_zone >= 0.7)
            detections_zone = len(locations_zone[0])
            
            if detections_zone > 0:
                max_val = np.max(result_zone)
                print(f"  {colonne['nom']}: {detections_zone} détections (max score: {max_val:.3f})")
                total_detections += detections_zone
    
    print(f"\nTotal détections dans l'image: {total_detections}")
    
    # Sauvegarde d'une version annotée pour debug visuel
    debug_img = img.copy()
    
    # Dessiner les limites des colonnes
    for colonne in colonnes:
        cv2.rectangle(debug_img, 
                     (colonne["x_start"], y_start), 
                     (colonne["x_end"], y_end), 
                     (0, 255, 0), 2)
        cv2.putText(debug_img, colonne["nom"], 
                   (colonne["x_start"], y_start - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    debug_path = image_path.replace('.png', '_debug.png')
    cv2.imwrite(debug_path, debug_img)
    print(f"Image debug sauvée: {debug_path}")

def main():
    """Test principal."""
    test_dir = "test"
    if not os.path.exists(test_dir):
        print(f"Erreur: Le dossier {test_dir} n'existe pas")
        return
    
    # Liste des images de test
    images = [f for f in os.listdir(test_dir) if f.endswith('.png') and not f.endswith('_debug.png')]
    
    if not images:
        print(f"Aucune image PNG trouvée dans {test_dir}")
        return
    
    print("=== SCRIPT DE TEST DE DÉTECTION DE COMBATS ===")
    print(f"Analyse de {len(images)} images dans {test_dir}/")
    
    for image_name in sorted(images):
        image_path = os.path.join(test_dir, image_name)
        analyser_image_test(image_path)
    
    print("\n=== FIN DU TEST ===")
    print("Vérifiez les images *_debug.png pour voir les zones de détection.")

if __name__ == "__main__":
    main()
