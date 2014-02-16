# Download the twilio-python library from http://twilio.com/docs/libraries
from twilio.rest import TwilioRestClient
import string
import random
 
# Find these values at https://twilio.com/user/account
account_sid = "AC35caff0e983a8ec210175ac2e3448b4d"
auth_token = "7c90741d85e33d02ccae26a1e8cf9888"
client = TwilioRestClient(account_sid, auth_token)

#this is the number that the user types in to identify them
user_number="+16107452210"
#randomally generated verification code
code=string.ascii_lowercase+string.digits
verification_code=''.join(random.choice(code) for i in range(8))
#this is the SMS message we are going to send
message="What's up? Enter %s on the sign up page to verify your Can't Pickup account! Thanks :)"%(verification_code)
 
message = client.messages.create(to=user_number, from_="+17575172492",
                                     body=message)
