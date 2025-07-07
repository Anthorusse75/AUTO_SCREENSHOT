#!/usr/bin/env python3
"""
Script d'analyse spécialisé pour vos images de test du calendrier.
"""
import os
import sys
import cv2
import numpy as np

# Ajouter le chemin du projet
sys.path.append('.')

def analyser_detection_detaillee():
    """Analyse détaillée de la détection sur vos images."""
    print("=== ANALYSE DÉTAILLÉE DE LA DÉTECTION DE COMBATS ===\n")
    
    # Vérification des prérequis
    if not os.path.exists("test"):
        print("❌ Dossier 'test' introuvable")
        return
        
    images_test = [f for f in os.listdir("test") if f.endswith('.png') and not f.endswith('_debug.png')]
    if not images_test:
        print("❌ Aucune image de test trouvée")
        return
    
    # Templates à tester
    templates = {
        "victoire": "templates/calendrier_du_championnat/victoire_cdc.png",
        "egalite": "templates/calendrier_du_championnat/egalite_cdc.png", 
        "defaite": "templates/calendrier_du_championnat/defaite_cdc.png"
    }
    
    # Vérification des templates
    print("Vérification des templates:")
    templates_valides = {}
    for nom, chemin in templates.items():
        if os.path.exists(chemin):
            template = cv2.imread(chemin, cv2.IMREAD_GRAYSCALE)
            if template is not None:
                templates_valides[nom] = template
                print(f"  ✅ {nom}: {template.shape[1]}x{template.shape[0]} pixels")
            else:
                print(f"  ❌ {nom}: impossible à charger")
        else:
            print(f"  ❌ {nom}: fichier manquant ({chemin})")
    
    if not templates_valides:
        print("❌ Aucun template valide trouvé")
        return
    
    print(f"\n{len(templates_valides)} template(s) chargé(s)\n")
    
    # Analyse de chaque image
    for image_name in sorted(images_test):
        print(f"=== ANALYSE DE {image_name} ===")
        image_path = os.path.join("test", image_name)
        
        # Chargement
        img_couleur = cv2.imread(image_path)
        img_gris = cv2.cvtColor(img_couleur, cv2.COLOR_BGR2GRAY)
        print(f"Dimensions: {img_gris.shape[1]}x{img_gris.shape[0]}")
        
        # Créer une image de debug
        debug_img = img_couleur.copy()
        
        # Dessiner les zones de colonnes  
        colonnes = [
            {"nom": "Lundi", "x": 78, "w": 232, "color": (255, 0, 0)},      
            {"nom": "Mardi", "x": 324, "w": 232, "color": (0, 255, 0)},     
            {"nom": "Mercredi", "x": 570, "w": 232, "color": (0, 0, 255)},  
            {"nom": "Jeudi", "x": 816, "w": 232, "color": (255, 255, 0)},   
            {"nom": "Vendredi", "x": 1062, "w": 232, "color": (255, 0, 255)} 
        ]
        
        y_top = 120
        y_bottom = 780
        
        # Dessiner les grilles des colonnes
        for col in colonnes:
            cv2.rectangle(debug_img, 
                         (col["x"], y_top), 
                         (col["x"] + col["w"], y_bottom), 
                         col["color"], 2)
            cv2.putText(debug_img, col["nom"][:3], 
                       (col["x"] + 5, y_top - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, col["color"], 1)
        
        total_detections = 0
        
        # Test de chaque template
        for nom_template, template in templates_valides.items():
            print(f"\n--- Template {nom_template.upper()} ---")
            
            # Test global d'abord
            result_global = cv2.matchTemplate(img_gris, template, cv2.TM_CCOEFF_NORMED)
            max_score_global = np.max(result_global)
            print(f"Score maximum global: {max_score_global:.3f}")
            
            # Test avec différents seuils
            seuils = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9]
            for seuil in seuils:
                locs = np.where(result_global >= seuil)
                nb_detections = len(locs[0])
                if nb_detections > 0:
                    print(f"  Seuil {seuil}: {nb_detections} détection(s)")
            
            # Détection par colonne
            for col_idx, col in enumerate(colonnes):
                x_start = max(0, col["x"])
                x_end = min(img_gris.shape[1], col["x"] + col["w"])
                zone = img_gris[y_top:y_bottom, x_start:x_end]
                
                if zone.size == 0:
                    continue
                
                result_zone = cv2.matchTemplate(zone, template, cv2.TM_CCOEFF_NORMED)
                max_score_zone = np.max(result_zone) if result_zone.size > 0 else 0
                
                # Détections avec seuil 0.7
                locs = np.where(result_zone >= 0.7)
                nb_detections = len(locs[0])
                
                if nb_detections > 0 or max_score_zone > 0.6:
                    print(f"  {col['nom']}: {nb_detections} détections (max: {max_score_zone:.3f})")
                    
                    # Marquer les détections sur l'image debug
                    for pt in zip(*locs[::-1]):
                        x_global = x_start + pt[0]
                        y_global = y_top + pt[1]
                        cv2.rectangle(debug_img,
                                    (x_global, y_global),
                                    (x_global + template.shape[1], y_global + template.shape[0]),
                                    col["color"], 3)
                        cv2.putText(debug_img, nom_template[:3],
                                  (x_global, y_global - 5),
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.4, col["color"], 1)
                        total_detections += 1
        
        print(f"\nTotal détections marquées: {total_detections}")
        
        # Sauvegarder l'image debug
        debug_path = os.path.join("test", f"debug_{image_name}")
        cv2.imwrite(debug_path, debug_img)
        print(f"Image debug sauvée: {debug_path}")
        print("-" * 50)

if __name__ == "__main__":
    analyser_detection_detaillee()
