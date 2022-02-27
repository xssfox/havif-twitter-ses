import sys
sys.path.append("./lib")
import tweepy
import boto3
import tempfile
import os



import email
import email.policy
from email.message import EmailMessage
import json
import base64
import io

s3 = boto3.resource("s3")

def handler(event,context):
    print(json.dumps(event))
    auth = tweepy.OAuthHandler(os.environ['CLIENT_ID'],os.environ['CLIENT_SECRET'])
    auth.set_access_token(os.environ["ACCESS_KEY"], os.environ["ACCESS_SECRET"])
    api = tweepy.API(auth)

    for record in event["Records"]:
        ses_meta_data = json.loads(record["Sns"]["Message"])

        mail = s3.Object(ses_meta_data['receipt']['action']['bucketName'], ses_meta_data['receipt']['action']['objectKey'])
        mail = mail.get()['Body'].read()
        msg = email.message_from_bytes(mail, _class=EmailMessage, policy=email.policy.default)
        if os.environ('FROM_EMAIL') in msg['from'].lower() :
            tweet_message = msg['subject']
            print(f"set tweet message to : {tweet_message}")
            image_ids = []
    
            for email_message_attachment in msg.iter_attachments():
                image = base64.b64decode(email_message_attachment.get_payload())
                with tempfile.NamedTemporaryFile(suffix='.havif') as tf:
                    # get header
                    with open("header.bytes", "rb") as header_file:
                        header = header_file.read()
                    # put the header back on to make sure it still works
                    data = header
                    payload = image
                    length = len(payload)
                    data += payload
                    tf.write(data)

                    # Correct the size of the payload in the avif head
                    tf.seek(124) 
                    tf.write((length+2).to_bytes(4, byteorder='big'))
                    tf.seek(274)
                    tf.write((length+8+2).to_bytes(4, byteorder='big')) # not sure why plus 2?
                    tf.flush()

                    print(tf.name)
                    os.system(f"/opt/avifdec {tf.name} /tmp/output.png")
                    media = api.media_upload("/tmp/output.png")
                    image_ids.append(media.media_id)
                print("image uploaded")
                print(image_ids)
                        
            api.update_status(tweet_message,media_ids=image_ids)

if __name__ == "__main__":
    handler({
    "Records": [
    ]
}
,{})
