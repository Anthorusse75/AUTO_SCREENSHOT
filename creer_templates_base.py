#!/usr/bin/env python3
"""
Script simple pour créer les templates de base nécessaires.
"""

import os
import numpy as np


def creer_template_informations_combat():
    """Crée un template basique pour les informations de combat."""
    # Créer le dossier si nécessaire
    os.makedirs("templates/journal_de_guerre_de_guildes", exist_ok=True)
    
    # Créer un template simple (sera à remplacer par un vrai template)
    # Format : rectangle gris avec bordure pour simulation
    template = np.ones((25, 80), dtype=np.uint8) * 180  # Gris clair
    
    # Ajouter une bordure pour le rendre plus distinctif
    template[0:2, :] = 100  # Bordure haut
    template[-2:, :] = 100  # Bordure bas
    template[:, 0:2] = 100  # Bordure gauche
    template[:, -2:] = 100  # Bordure droite
    
    # Ajouter du "contenu" simulé
    template[5:8, 10:70] = 120  # Ligne de texte 1
    template[12:15, 15:65] = 120  # Ligne de texte 2
    template[18:21, 20:60] = 120  # Ligne de texte 3
    
    # Sauvegarder en tant qu'image PNG
    try:
        import cv2
        cv2.imwrite("templates/journal_de_guerre_de_guildes/informations_combat.png", template)
        print("✅ Template informations_combat.png créé")
    except ImportError:
        # Fallback avec PIL si OpenCV n'est pas disponible
        from PIL import Image
        img = Image.fromarray(template, mode='L')
        img.save("templates/journal_de_guerre_de_guildes/informations_combat.png")
        print("✅ Template informations_combat.png créé (PIL)")


def creer_templates_onglets():
    """Crée des templates basiques pour les onglets."""
    os.makedirs("templates/journal_de_guerre_de_guildes/onglets", exist_ok=True)
    
    # Template journal d'attaque
    template_attaque = np.ones((30, 120), dtype=np.uint8) * 200
    template_attaque[5:25, 10:110] = 150  # Zone de texte
    template_attaque[10:20, 15:105] = 100  # Texte simulé
    
    # Template journal de défense
    template_defense = np.ones((30, 120), dtype=np.uint8) * 200
    template_defense[5:25, 10:110] = 150  # Zone de texte
    template_defense[10:20, 15:105] = 120  # Texte simulé (légèrement différent)
    
    # Template bouton défense
    template_bouton = np.ones((25, 100), dtype=np.uint8) * 180
    template_bouton[3:22, 5:95] = 140
    template_bouton[8:17, 10:90] = 110
    
    try:
        import cv2
        cv2.imwrite("templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png", template_attaque)
        cv2.imwrite("templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png", template_defense)
        cv2.imwrite("templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png", template_bouton)
        print("✅ Templates d'onglets créés")
    except ImportError:
        from PIL import Image
        Image.fromarray(template_attaque, mode='L').save("templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png")
        Image.fromarray(template_defense, mode='L').save("templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png")
        Image.fromarray(template_bouton, mode='L').save("templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png")
        print("✅ Templates d'onglets créés (PIL)")


def creer_templates_limites():
    """Crée des templates pour détecter les limites de scroll."""
    os.makedirs("templates/journal_de_guerre_de_guildes/limites", exist_ok=True)
    
    # Template pour le haut du scroll
    template_haut = np.ones((20, 100), dtype=np.uint8) * 240  # Zone très claire
    template_haut[15:20, :] = 200  # Petite bordure
    
    # Template pour le bas du scroll
    template_bas = np.ones((20, 100), dtype=np.uint8) * 240  # Zone très claire
    template_bas[0:5, :] = 200  # Petite bordure
    
    try:
        import cv2
        cv2.imwrite("templates/journal_de_guerre_de_guildes/limites/haut_scroll.png", template_haut)
        cv2.imwrite("templates/journal_de_guerre_de_guildes/limites/bas_scroll.png", template_bas)
        print("✅ Templates de limites créés")
    except ImportError:
        from PIL import Image
        Image.fromarray(template_haut, mode='L').save("templates/journal_de_guerre_de_guildes/limites/haut_scroll.png")
        Image.fromarray(template_bas, mode='L').save("templates/journal_de_guerre_de_guildes/limites/bas_scroll.png")
        print("✅ Templates de limites créés (PIL)")


def main():
    print("🛠️ Création des templates de base pour JGG")
    print("=" * 40)
    
    creer_template_informations_combat()
    creer_templates_onglets()
    creer_templates_limites()
    
    print("\n✅ Tous les templates de base ont été créés")
    print("\n📝 Note importante :")
    print("Ces templates sont des placeholders basiques.")
    print("Vous devrez les remplacer par de vrais extraits de vos images de test")
    print("pour obtenir une détection précise.")
    
    print("\n📁 Templates créés :")
    print("- templates/journal_de_guerre_de_guildes/informations_combat.png")
    print("- templates/journal_de_guerre_de_guildes/onglets/journal_d_attaque.png")
    print("- templates/journal_de_guerre_de_guildes/onglets/journal_de_defense.png")
    print("- templates/journal_de_guerre_de_guildes/onglets/bouton_journal_defense.png")
    print("- templates/journal_de_guerre_de_guildes/limites/haut_scroll.png")
    print("- templates/journal_de_guerre_de_guildes/limites/bas_scroll.png")


if __name__ == "__main__":
    main()
