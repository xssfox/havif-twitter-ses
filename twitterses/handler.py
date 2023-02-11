import sys
sys.path.append("./lib")
from mastodon import Mastodon

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
    mastodon = Mastodon(
        client_id = os.environ["M_CLIENT_ID"],
        client_secret = os.environ["M_CLIENT_SECRET"],
        api_base_url = os.environ["M_URL"],
        access_token = os.environ["M_ACCESS_TOKEN"]
    )

    for record in event["Records"]:
        ses_meta_data = json.loads(record["Sns"]["Message"])

        mail = s3.Object(ses_meta_data['receipt']['action']['bucketName'], ses_meta_data['receipt']['action']['objectKey'])
        mail = mail.get()['Body'].read()
        msg = email.message_from_bytes(mail, _class=EmailMessage, policy=email.policy.default)
        if os.environ['FROM_EMAIL'] in msg['from'].lower() :
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
                    x = image[0:2]
                    y = image[2:4]
                    data = header
                    payload = image[4:]
                    length = len(payload)
                    data += payload
                    tf.write(data)

                    # Correct the size of the payload in the avif head
                    tf.seek(124) 
                    tf.write((length+2).to_bytes(4, byteorder='big'))
                    tf.seek(274)
                    tf.write((length+8+2).to_bytes(4, byteorder='big')) # not sure why plus 2?
                    tf.seek(198)
                    tf.write(x)
                    tf.seek(202)
                    tf.write(y)
                    tf.flush()

                    print(tf.name)
                    os.system(f"/opt/avifdec {tf.name} /tmp/output.png")
                    media = mastodon.media_post("/tmp/output.png", "image/png", description="Image uploaded via HF winlink")
                    image_ids = [media["id"]]
                print("image uploaded")
                print(image_ids)
                        
            mastodon.status_post(tweet_message,media_ids=image_ids)

if __name__ == "__main__":
    handler({
    "Records": [
    ]
}
,{})
