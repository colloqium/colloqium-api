import time
from sqlalchemy.exc import OperationalError
from models.sender import PhoneNumber
from tools.utility import format_phone_number



def get_phone_number_from_db(phone_number: str) -> PhoneNumber:
    #create a phone number object from the form data
    full_phone_number = format_phone_number(phone_number)
    
    
   # Find the index of the last 10 digits of the phone number
    last_10_digits_index = len(phone_number) - 10

    # Extract the last 10 digits of the phone number
    phone_number_after_code = full_phone_number[last_10_digits_index:]

    # Extract the country code from the beginning of the phone number
    country_code = full_phone_number[:last_10_digits_index]

    phone_number = PhoneNumber.query.filter_by(
        country_code=country_code,
        phone_number_after_code=phone_number_after_code
    ).first()

    return phone_number

def check_db_connection(db, max_attempts=5, delay=30):
    try:
        db.engine.execute('SELECT 1')  # simple query to check the connection
        return True
    except OperationalError:
        print(f"Database connection failed. Attempt {i+1}/{max_attempts}. Retrying in {delay} seconds...")
    return False


from models.sender import PhoneNumber
from tools.utility import format_phone_number