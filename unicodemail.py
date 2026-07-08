#coding: utf-8
import os
import mimetypes
from io import StringIO
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.header import Header
from email import charset as Charset
from email import encoders
from email.generator import Generator
import smtplib


def _attach_file(msg, attachment):
    """Attach a file to msg.

    `attachment` is either a path to a file on disk, or a
    (filename, data, [mimetype]) tuple with `data` as bytes.
    """
    if isinstance(attachment, (tuple, list)):
        filename, data = attachment[0], attachment[1]
        mimetype = attachment[2] if len(attachment) > 2 else None
    else:
        filename = os.path.basename(attachment)
        with open(attachment, 'rb') as f:
            data = f.read()
        mimetype = None

    if mimetype is None:
        mimetype, _ = mimetypes.guess_type(filename)
        mimetype = mimetype or 'application/octet-stream'
    maintype, subtype = mimetype.split('/', 1)

    part = MIMEBase(maintype, subtype)
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=filename)
    msg.attach(part)


def send(from_,to,cc,subject,message,html,attachments=None):

    recipients_to=to.split()
    recipients_cc=cc.split()

    # Default encoding mode set to Quoted Printable. Acts globally!
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')

    # 'mixed' MIME type – allows attachments alongside the alternative body
    msg = MIMEMultipart('mixed')
    msg['Subject'] = "%s" % Header(subject, 'utf-8')
    # Only descriptive part of recipient and sender shall be encoded, not the email address
    msg['From'] = from_
    msg['To'] = ",".join(recipients_to)
    msg['Cc'] = ",".join(recipients_cc)

    # 'alternative' MIME type – HTML and plain text bundled in one e-mail message
    body = MIMEMultipart('alternative')
    textpart = MIMEText(message, 'plain', 'UTF-8')
    htmlpart = MIMEText(html, 'html', 'UTF-8')
    body.attach(htmlpart)
    body.attach(textpart)
    msg.attach(body)

    for attachment in attachments or []:
        _attach_file(msg, attachment)

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
