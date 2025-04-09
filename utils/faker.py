import random
from mobile.db_connect import *
session = Session()

def generate_random_numeric_code(length=13):
    """Generate a random numeric barcode code."""
    return ''.join(random.choices('0123456789', k=length))

for _ in range(10000):
    fake_code = generate_random_numeric_code()
    new_barcode = Barcodes(code=fake_code, count=random.randint(1, 100), workspace_id=1)
    session.add(new_barcode)

    session.commit()
session.close()
