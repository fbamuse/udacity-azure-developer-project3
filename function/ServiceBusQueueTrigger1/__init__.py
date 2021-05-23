import logging
from typing import Counter
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def main(msg: func.ServiceBusMessage):
    try:
        # TODO: Get notification message and subject from database using the notification_id

        notification_id = int(msg.get_body().decode('utf-8'))
        #notification_id = msg.get_body()
        logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)

        # TODO: Get connection to database
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT message, subject FROM notification where id = %s',(notification_id,))
        (massage,subject) = cur.fetchone()
        logging.info('massage: %s',massage)
        logging.info('subject: %s',subject)

        # TODO: Get attendees email and name
        count=0
        cur.execute('SELECT email, first_name, last_name FROM attendee')

        # TODO: Loop through each attendee and send an email with a personalized subject
        for row in cur:
            email=row[0]
            first_name=row[1]
            body= "Hi {}, {}".format(first_name,massage)
            logging.info('mail to : %s',first_name)
            rc = send_email(email, subject, body)
            if rc == 0:
                count +=1
            
        # TODO: Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        notification_status = 'Notified {} attendees'.format(count)
        update_query = cur.execute("UPDATE notification SET status = '{}', completed_date = '{}' WHERE id = {};".format(notification_status, datetime.utcnow(), notification_id))
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:

        logging.error(error)
    finally:
       # TODO: Close connectio
        conn.close()
def send_email(email, subject, body):
    if  os.environ.get('SENDGRID_API_KEY'):
        message = Mail(
            from_email=os.environ.get('ADMIN_EMAIL_ADDRESS'),
            to_emails=email,
            subject=subject,
            plain_text_content=body)
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        try:
            response = sg.send(message)
            logging.info('senndmail code : %s', response.status_code)
            return 0
        except Exception as e:
            logging.error('senndmail error : %s', email)

def get_connection():
    #dsn = os.environ.get('DATABASE_URL')
    POSTGRES_USER   = os.environ.get('POSTGRES_USER')
    POSTGRES_PW     = os.environ.get('POSTGRES_PW')
    POSTGRES_URL    = os.environ.get('POSTGRES_URL')
    POSTGRES_DB     = os.environ.get('POSTGRES_DB')
    connection      = psycopg2.connect(host=POSTGRES_URL,database = POSTGRES_DB, user = POSTGRES_USER, password=POSTGRES_PW)
    return connection