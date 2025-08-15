import os

import opik
from opik.configurator.configure import OpikConfigurator

from application.core.config import settings
from application.core.logging import get_logger

logger = get_logger(__name__)


def configure() -> None:
    if settings.COMET_API_KEY and settings.COMET_PROJECT:
        try:
            client = OpikConfigurator(api_key=settings.COMET_API_KEY)
            default_workspace = client._get_default_workspace()
        except Exception as e:
            logger.warning(f"Default workspace not found: {e}. Setting workspace to None.")
            default_workspace = None

        os.environ["OPIK_PROJECT_NAME"] = settings.COMET_PROJECT

        try:
            opik.configure(
                api_key=settings.COMET_API_KEY,
                workspace=default_workspace,
                use_local=False,
                force=True,
            )
            logger.info(f"Opik configured successfully using workspace '{default_workspace}'")
        except Exception as e:
            logger.warning(f"Couldn't configure Opik: {e}. Check COMET_API_KEY, COMET_PROJECT, or Opik server.")
    else:
        logger.warning(
            "COMET_API_KEY and COMET_PROJECT are not set. Set them to enable prompt monitoring with Opik (powered by Comet ML)."
        )