import pickle
from sreality_data import Advertisment

if __name__ == '__main__':
    url = input('insert wrongly processed url')
    print('saving...')
    Advertisment(url).save()