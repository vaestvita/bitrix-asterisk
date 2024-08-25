import logging
import os
import redis

r = redis.Redis(host='localhost', port=6379, db=1)

def setup_logger(linked_id):
    log_dir = 'events'
    log_filename = f'{log_dir}/{linked_id}.txt'
    
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    if r.exists(f'logger:{linked_id}'):
        logger = logging.getLogger(linked_id)
    else:
        logger = logging.getLogger(linked_id)
        logger.setLevel(logging.INFO)
        
        file_handler = logging.FileHandler(log_filename)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        
        r.set(f'logger:{linked_id}', log_filename)
    
    return logger