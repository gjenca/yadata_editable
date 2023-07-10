#coding: utf-8
from io import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import charset as Charset
from email.generator import Generator
import smtplib


def send(from_,to,cc,subject,message,html):

    recipients_to=to.split()
    recipients_cc=cc.split()

    # Default encoding mode set to Quoted Printable. Acts globally!
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')
     
    # 'alternative’ MIME type – HTML and plain text bundled in one e-mail message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "%s" % Header(subject, 'utf-8')
    # Only descriptive part of recipient and sender shall be encoded, not the email address
    msg['From'] = from_
    msg['To'] = ",".join(recipients_to)
    msg['Cc'] = ",".join(recipients_cc)
     
    textpart = MIMEText(message, 'plain', 'UTF-8')
    htmlpart = MIMEText(html, 'html', 'UTF-8')
    msg.attach(htmlpart)
    msg.attach(textpart)
     
    # Create a generator and flatten message object to 'file’
    str_io = StringIO()
    g = Generator(str_io, False)
    g.flatten(msg)
    # str_io.getvalue() contains ready to sent message
     
    # Optionally - send it – using python's smtplib
    # or just use Django's
    s = smtplib.SMTP()
    s.connect()
    s.ehlo()
    s.sendmail("",recipients_to+recipients_cc, str_io.getvalue())
    s.quit()
