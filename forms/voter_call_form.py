from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField
from wtforms.validators import DataRequired, Email, EqualTo, Regexp
from wtforms import TextAreaField


class ExampleForm(FlaskForm):
	name = StringField('Name', validators=[DataRequired()])
	email = StringField('Email', validators=[DataRequired(), Email()])
	password = PasswordField('Password', validators=[DataRequired()])
	confirm_password = PasswordField(
	 'Confirm Password', validators=[DataRequired(),
	                                 EqualTo('password')])
	submit = SubmitField('Submit')


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


class VoterCallForm(FlaskForm):
	voter_name = StringField('Voter Name', validators=[DataRequired()])
	voter_information = TextAreaField('Voter Information', validators=[DataRequired()])
	voter_phone_number = StringField('Phone Number',
	                                 validators=[PhoneNumberValidator()])
	race_name = StringField('Race Name', validators=[DataRequired()])
	race_information = TextAreaField('Race Information',
	                                 validators=[DataRequired()])
	candidate_name = StringField('Candidate Name', validators=[DataRequired()])
	candidate_information = TextAreaField('Candidate Information',
	                                    validators=[DataRequired()])
	race_date = DateField('Race Date', validators=[DataRequired()])
	submit = SubmitField('Submit')
