from models.models import PhoneNumber
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