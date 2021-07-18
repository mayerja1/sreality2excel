import openpyxl as opx
from openpyxl.worksheet.worksheet import Worksheet
from itertools import count

def first_available_row(ws: Worksheet) -> int:
    for i in count(1):
        if ws[f'T{i}'].value is None:
            return i