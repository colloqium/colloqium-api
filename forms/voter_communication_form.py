from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DateField, SelectField
from wtforms.validators import DataRequired, Regexp
from wtforms import TextAreaField


# Define a custom validator for phone numbers that match "+17066641258"
class PhoneNumberValidator(Regexp):

    def __init__(self):
        super().__init__(
            # The regular expression to match phone numbers
            r'^\+[1-9]\d{10}$',
            # The error message to display if the phone number is invalid
            message=
            'The phone number must be in the format +######### with the country code included'
        )


class VoterCommunicationForm(FlaskForm):
    voter_name = StringField('Voter Name', validators=[DataRequired()])
    voter_information = TextAreaField('Voter Information',
                                      validators=[DataRequired()])
    voter_phone_number = StringField('Phone Number',
                                     validators=[PhoneNumberValidator()])
    race_name = StringField('Race Name', validators=[DataRequired()])
    race_information = TextAreaField('Race Information',
                                     validators=[DataRequired()])
    candidate_name = StringField('Candidate Name', validators=[DataRequired()])
    candidate_information = TextAreaField('Candidate Information',
                                          validators=[DataRequired()])
    race_date = DateField('Race Date', validators=[DataRequired()])
    communication_type = SelectField('Communication Type',
                                     choices=[('call', 'Call'),
                                              ('text', 'Text')])
    submit = SubmitField('Submit')