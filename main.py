import openpyxl as opx
from sreality_data import Advertisment
from excel_utils import first_available_row
from enum import Enum

DATA_SHEET_PATH = 'data_FINAL_IQ_2021_Adam.xlsx'
ATTRIBUTES = (
    'size_m2',
    'rent_czk',
    'price_czk',
    'provision',
    'rooms_num',
    'kitchen',
    'construction',
    'condition',
    'reconstruction',
    'ownership',
    'floors_num',
    'floor',
    'balcony_num',
    'cellar',
    'heating',
    'elevator',
    'insulation',
    'last_update_date'
)
COLUMN_MAP = {attr: i + 3 for i, attr in enumerate(ATTRIBUTES)}

def main():
    url = input('Insert the advertisement URL:\n')
    #url = 'https://www.sreality.cz/detail/prodej/byt/1+kk/praha-zizkov-biskupcova/3890874972#img=0&fullscreen=false'
    ad = Advertisment(url)
    wb = opx.load_workbook(DATA_SHEET_PATH)
    ws = wb['data']
    row = {}
    for attr, col in COLUMN_MAP.items():
        try:
            val = getattr(ad, attr)
            if val is not None:
                if isinstance(val, bool):
                    val = int(val)
                elif isinstance(val, Enum):
                    val = val.value
                row[col] = val
        except Exception as e:
            print(f'Exception while processing {attr}:')
            print(e)
            print('saving ad...')
            ad.save()
    row_idx = first_available_row(ws)
    for col, val in row.items():
        ws.cell(row_idx, col, val)
    wb.save(DATA_SHEET_PATH)
    print('ad successfully saved')

if __name__ == '__main__':
    main()
    

    

