import os
import sys

# Додаємо батьківську директорію до шляху пошуку модулів
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import db
db.drop_all()
db.create_all()
from scripts.create_tables import *