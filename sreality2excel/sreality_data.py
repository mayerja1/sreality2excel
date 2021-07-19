import requests
from typing import ClassVar, Dict, Any, Union, Literal, Optional, Iterable
from fake_useragent import UserAgent
from enum import Enum, auto
from datetime import date, timedelta, datetime
import re
import unicodedata
import pickle

UA = UserAgent()

class ConstructionType(Enum):
    BRICK = 1
    PANEL = 2
    OTHER = 0


class OwnershipType(Enum):
    PERSONAL    = 1
    COOPERATIVE = 2
    OTHER       = 3


class HeatingType(Enum):
    LOCAL   = 1
    ETAGE   = 2
    CENTRAL = 3
    REMOTE  = 4


class ConditionType(Enum):
    GOOD = 'D'
    BAD  = 'S'


class Advertisment:

    def __init__(self, url: str):
        self.data = self.get_ad_data_from_url(url)
        self._hash = int(self.hash_id_from_url(url))
        self.data_items = {
            item['name']: item for item in self.data['items']
        }

    def __hash__(self) -> int:
        return self._hash

    @staticmethod
    def get_ad_data_from_hash_id(hash_id: str) -> Dict[str, Any]:
        """Tries to get data about an estate given the corresponding
        hash_id from sreality.cz in json format

        Args:
            hash_id (str): The hash id

        Returns:
            Dict[str, Any]: the data in json format
        """
        header = {'User-Agent':str(UA.chrome)}
        response = requests.get(
            f'https://www.sreality.cz/api/cs/v2/estates/{hash_id}?tms=200',
            headers=header
        )
        return response.json()

    @staticmethod
    def get_ad_data_from_url(url: str) -> Dict[str, Any]:
        """Tries to get data about an estate given the corresponding
        url from sreality.cz in json format

        Args:
            url (str): url of the advertisment

        Returns:
            Dict[str, Any]: the data in json format
        """
        hash_id = Advertisment.hash_id_from_url(url)
        return Advertisment.get_ad_data_from_hash_id(hash_id)

    @staticmethod
    def hash_id_from_url(url: str) -> str:
        """Stupid but simple way to extract the hash_id from an advertisement
        url

        Args:
            url (str): advert url

        Returns:
            str: hash_id of the estate
        """
        tail = url.split('/')[-1]
        for idx, c in enumerate(tail):
            if not c.isnumeric():
                break
        return tail[:idx]

    def check_keywords(self, keywords: Iterable[str], s: Optional[str] = None):
        if s is None:
            s = self.data['text']['value'].lower()
        return any(re.search(k, s) for k in keywords)

    def save(self, path: Optional[str] = None):
        if path is None:
            path = f'../wrongly_processed_ads/{hash(self)}'
        with open(path, 'wb') as f:
            pickle.dump(self, f)

    @property
    def size_m2(self) -> int:
        return int(self.data_items['Užitná plocha']['value'])

    @property
    def rentable(self) -> bool:
        unit = self.data_items['Celková cena']['unit']
        if unit == 'za měsíc':
            return True
        elif unit == 'za nemovitost':
            return False
        raise Exception(f'unexpected unit: {unit}')

    @property
    def price_czk(self) -> Optional[int]:
        if self.rentable:
            return None
        price = self.data_items['Celková cena']['value']
        return int(unicodedata.normalize('NFKD', price).encode('ascii', 'ignore').replace(b' ', b''))

    @property
    def rent_czk(self) -> Optional[int]:
        if not self.rentable:
            return None
        price = self.data_items['Celková cena']['value']
        return int(unicodedata.normalize('NFKD', price).encode('ascii', 'ignore').replace(b' ', b''))
    
    @property
    def provision(self) -> bool:
        for note in self.data_items['Celková cena']['notes']:
            if 'provize' in note.lower():
                return True
        return False

    @property
    def rooms_num(self) -> int:
        s = self.data['meta_description'].lower()
        match = re.search('[1-9]\+([0-9]|kk)', s)
        if match is None:
            raise Exception(f'number of rooms not found in: {s}')
        match = match.group()
        return int(match[0])

    @property
    def kitchen(self) -> bool:
        s = self.data['meta_description'].lower()
        match = re.search('[1-9]\+([0-9]|kk)', s)
        if match is None:
            raise Exception(f'number of rooms not found in: {s}')
        match = match.group()
        kitchen_str = match.split('+')[1]
        if kitchen_str == '1':
            return True
        elif kitchen_str == 'kk':
            return False
        raise Exception(f'unknown kitchen type from meta description {s}')

    @property
    def construction(self) -> ConstructionType:
        con = self.data_items['Stavba']['value'].lower()
        if con == 'cihlová':
            return ConstructionType.BRICK
        elif con == 'panelová':
            return ConstructionType.PANEL
        return ConstructionType.OTHER

    @property
    def condition(self) -> ConditionType:
        s = self.data_items['Stav objektu']['value'].lower()
        if 'špatný' in s:
            return ConditionType.BAD
        return ConditionType.GOOD

    @property
    def reconstruction(self) -> bool:
        keywords = (
            'zrekonstruováno',
            'zrekonstruovano',
            'po .*rekonstrukci',
            'rekonstrukcí'
        )
        return self.check_keywords(keywords) and not self.check_keywords(['před rekonstrukcí'])

    @property
    def ownership(self) -> OwnershipType:
        s = self.data_items['Vlastnictví']['value'].lower()
        if s == 'osobní':
            return OwnershipType.PERSONAL
        elif s == 'družstevní':
            return OwnershipType.COOPERATIVE
        return OwnershipType.OTHER

    @property
    def floors_num(self) -> Optional[int]:
        s = self.data_items['Podlaží']['value']
        try:
            return int(s.split(' ')[-1])
        except ValueError:
            return None

    @property
    def floor(self) -> int:
        s = self.data_items['Podlaží']['value']
        return int(s.split('.')[0])

    @property
    def balcony_num(self) -> int:
        keys = ('Balkón', 'Lodžie')
        for k in keys:
            try:
                return int(self.data_items[k]['value'])
            except KeyError:
                pass
        return 0

    @property
    def cellar(self) -> bool:
        keywords = (
            'sklep',
            'sklýpek',
            'sklypek'
        )
        return self.check_keywords(keywords)

    @property
    def heating(self) -> HeatingType:
        try:
            s = ' '.join(v['value'] for v in self.data_items['Topení']['value']).lower()
        except KeyError:
            s = self.data['text']['value'].lower()
        keywords = {
            HeatingType.LOCAL: (
                'lokální plynové',
                'lokální elektrické',
            ),
            HeatingType.ETAGE: (
                'etážové',
            ),
            HeatingType.CENTRAL: (
                'ústřední plynové',
            ),
            HeatingType.REMOTE: (
                'ústřední dálkové',
            )
        }
        for k, v in keywords.items():
            if self.check_keywords(v, s):
                return k
        raise Exception('heating type not found')

    @property
    def elevator(self) -> bool:
        return self.data_items['Výtah']['value']

    @property
    def insulation(self) -> bool:
        keywords = (
            'zateplení',
            'střecha',
            'fasáda'
        )
        return self.check_keywords(keywords)

    @property
    def last_update_date(self) -> date:
        s = self.data_items['Aktualizace']['value'].lower()
        if s == 'dnes':
            return date.today()
        elif s == 'včera':
            return date.today() - timedelta(1)
        else:
            return datetime.strptime(s, '%d.%m.%Y')
