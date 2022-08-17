import os
from pathlib import Path
from datetime import datetime

def logg(head = 'INFO', body = 'Start program'):
    if not os.path.isdir("data"):
        os.mkdir("data")
    log_path=Path('data', 'log.txt')
    log_time=datetime.now().strftime("%Y-%m-%d | %H:%M:%S | ")
    with open(log_path,'a') as log:
        text= f'{(head + ":"):55}{log_time:50}{body}\n'
        log.write(text)