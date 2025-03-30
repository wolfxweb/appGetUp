# Este arquivo marca o diretório como um pacote Python 

from app.models.user import User
from app.models.basic_data import BasicData
from app.models.license import License

# Export all models
__all__ = ['User', 'BasicData', 'License'] 