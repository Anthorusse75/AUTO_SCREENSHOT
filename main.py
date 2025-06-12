import sys
import time

from configuration.log_config import setup_logger
from configuration.bluestacks_configurator import configurer_bluestacks
from configuration.fenetre_utils import initialiser_fenetre_bluestacks
from fonctions.menu import boucle_principale

logger = setup_logger()
logger.info("▶ Lancement de la vérification BlueStacks")

# Étape 1 : vérifier que le fichier de conf est conforme
configurer_bluestacks(logger)
logger.info("✅ Vérification du fichier de configuration terminée")

# Étape 2 : vérifier la fenêtre (taille + position)
window = initialiser_fenetre_bluestacks(logger)
if not window:
    logger.critical("❌ Impossible de poursuivre : la fenêtre BlueStacks est introuvable ou invalide.")
    sys.exit(1)

logger.info("✅ Fenêtre BlueStacks prête pour les actions automatiques")

# Attendre un peu pour s'assurer que la fenêtre est prête
time.sleep(2)


# Boucle principale d'interaction
boucle_principale(logger, window)
