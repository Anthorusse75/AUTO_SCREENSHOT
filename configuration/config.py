# Dimensions attendues pour la fenêtre BlueStacks
WINDOW_WIDTH = 1632
WINDOW_HEIGHT = 933

# Nom exact de la fenêtre BlueStacks (à adapter si besoin)
BLUESTACKS_WINDOW_TITLE = "BlueStacks App Player"

# Timeout d’attente max (si on veut attendre qu'elle apparaisse)
WINDOW_TIMEOUT_SECONDS = 10

# Chemins importants
TEMPLATES_PAGES_DIR = "templates/pages"
PAGES_STRUCTURE_PATH = "configuration/pages_structure.json"

# Seuils de match
PAGE_MATCH_THRESHOLD = 0.94      # seuil pour matchTemplate sur les pages
TAB_MATCH_THRESHOLD = 0.85       # seuil pour matchTemplate sur les onglets
LIMIT_MATCH_THRESHOLD = 0.80     # seuil pour les limites (scroll)
COMBAT_MATCH_THRESHOLD = 0.99    # seuil pour la détection des combats
COMBAT_RECT_MATCH_THRESHOLD = 0.80  # seuil pour la détection des rectangles de défaite
