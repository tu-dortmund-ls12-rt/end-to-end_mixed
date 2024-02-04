import time
import pickle
import os


def time_now():
    t = time.localtime()
    current_time = time.strftime("%H:%M:%S", t)
    return current_time


def check_or_make_directory(dirname):
    """check if the folder exists, otherwise create it"""
    if not os.path.exists(dirname):
        os.makedirs(dirname)
        print(f'Directory {dirname} created')


def write_data(filename, data):
    file = open(filename, 'wb')
    pickle.dump(data, file)
    file.close()
    print(f'Data written to {filename}')


def load_data(filename):
    file = open(filename, 'rb')
    data = pickle.load(file)
    file.close()
    print(f'Data loaded from {filename}')
    return data
