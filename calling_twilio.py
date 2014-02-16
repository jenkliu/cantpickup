#what happens when someone calls the Twilio number

#if the user is busy then the call will be forwarded to a voice recording
#and then later a voicemail (where they can leave a message)

#if they are free it will forward to their real phone number


from flask import Flask, request, redirect
import twilio.twiml
import smtplib
from twilio.rest import TwilioRestClient


#isBusy is a varible defined by searching throught their google calendar
isBusy=True

#mp3File is the recorded file for a specific calendar
mp3File=None

#phoneNumber is the real phone number of the user
phoneNumber=None

account_sid = "AC5be69d79e258b0a161aeb97886f1c6e9"
auth_token = "5560401279ab0478e76e820c76cacc35"
client = TwilioRestClient(account_sid, auth_token)

app = Flask(__name__)

if isBusy:
    @app.route("/", methods=['GET', 'POST'])
    def unavailable():

        resp = twilio.twiml.Response()
        # Play an MP3
        resp.say('what do you want from me?')
        #resp.play(mp3File)
        resp.say("Record your message after the tone.")
        resp.record(maxLength="30", action="/handle-recording")

        #resp.say("Goodbye.")

        return str(resp)

elif not isBusy:
    @app.route("/", methods=['GET', 'POST'])
    def available():

        resp = twilio.twiml.Response()
        # Dial - connect that number to the incoming caller.
        resp.dial(phoneNumber)
        # If the dial fails:
        resp.say("The call failed, or the remote party hung up. Goodbye.")

        return str(resp)

@app.route("/handle-recording", methods=['GET', 'POST'])
def handle_recording():
    """Play back the caller's recording."""
    resp = twilio.twiml.Response()
    recording_url = request.values.get("RecordingUrl", None)
    resp.say(recording_url)
    print recording_url
    print type(recording_url)
    message = client.messages.create(to="+14349609765", from_="+15402239053",
                                    body=recording_url)
    
    resp.say("Thanks for message; listen to what you recorded.")
    resp.play(recording_url)
    resp.say("Goodbye.")
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
