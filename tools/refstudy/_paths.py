"""Caminhos do estudo de referências (sobrepor com variáveis de ambiente)."""
import os
WORK = os.environ.get("HCG_REFSTUDY_WORK", os.path.join("out", "refstudy"))
os.makedirs(WORK, exist_ok=True)
