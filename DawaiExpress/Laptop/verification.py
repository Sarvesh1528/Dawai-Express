import smtplib, os
from email.mime.text import MIMEText
from dotenv import load_dotenv, find_dotenv
from email.mime.multipart import MIMEMultipart
from Mail import Mail

load_dotenv(find_dotenv("secrets.env"))
Sender_Password = os.environ.get("EMAIL_PWD")
Sender_Email = os.environ.get("SENDER_EMAIL")

tls_Port = 587
smtp_server = 'smtp.gmail.com'

def send_mail(patName,Receiver_Email,context,quantity=None):
    # aes_password = os.environ.get("AES_PWD")
    try: 
        smtp = smtplib.SMTP(smtp_server, tls_Port) 
        smtp.starttls() 
        smtp.login(Sender_Email,Sender_Password)
        
        message = MIMEMultipart("alternative")

        content = ""
        if context == "regular":
            content = Mail.regularMsg["mailBody"].format(name=patName,quantity=quantity)
            message["Subject"] = Mail.regularMsg["subject"].format(name=patName)
        print("Mail body:", Mail.regularMsg["mailBody"])
        print("Mail subject:", Mail.regularMsg["subject"])

        message["From"] = Sender_Email
        message["To"] = Receiver_Email

        part1 = MIMEText(content, "html")

        message.attach(part1)

        smtp.sendmail(Sender_Email, Receiver_Email, str(message)) 

        smtp.quit() 
        print("Email sent successfully!") 
        return True

    except Exception as excp:   
        print("Something went wrong....",excp)
        return False

# send_mail("patient1", "manjrekarsudesh15@gmail.com", "regular", quantity="all medicines")