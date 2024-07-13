from contextlib import contextmanager
import threading

# Define a lock for each product
product_locks = {}

class LockException(Exception):
    pass

@contextmanager
def acquire_lock(product_id):
    if product_id not in product_locks:
        product_locks[product_id] = threading.Lock()
    
    lock = product_locks[product_id]
    lock_acquired = lock.acquire(timeout=5)


    if not lock_acquired:
        raise LockException("Update is locked, please try again later.")
    try:
        yield
    finally:
        lock.release()
