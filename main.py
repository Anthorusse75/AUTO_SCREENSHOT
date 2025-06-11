import time

from configuration.log_config import setup_logger
from configuration.bluestacks_configurator import configurer_bluestacks
from configuration.fenetre_utils import initialiser_fenetre_bluestacks
from fonctions.detection_page import detecter_page_actuelle
from fonctions.calendrier_du_championnat.Fonctions_detection_Combats import traiter_tous_les_combats

logger = setup_logger()
logger.info("▶ Lancement de la vérification BlueStacks")

# Étape 1 : vérifier que le fichier de conf est conforme
configurer_bluestacks(logger)
logger.info("✅ Vérification du fichier de configuration terminée")

# Étape 2 : vérifier la fenêtre (taille + position)
window = initialiser_fenetre_bluestacks(logger)
if not window:
    logger.critical("❌ Impossible de poursuivre : la fenêtre BlueStacks est introuvable ou invalide.")
    exit(1)

logger.info("✅ Fenêtre BlueStacks prête pour les actions automatiques")

# Attendre un peu pour s'assurer que la fenêtre est prête
time.sleep(2)

# Étape 3 : détecter la page actuelle
page = detecter_page_actuelle(logger, window)
if not page:
    logger.error("❌ Page inconnue – impossible de continuer.")
    exit(1)

logger.info(f"📄 Page en cours : {page}")

# Étape 4 : lancer la détection et le traitement des combats si on est sur le calendrier
if page.get("page") == "calendrier_du_championnat":
    traiter_tous_les_combats(logger, window)
else:
    logger.warning("⚠️ Pas sur la page calendrier du championnat, automation des combats non lancée.")