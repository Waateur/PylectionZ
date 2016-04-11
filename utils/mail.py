import smtplib
import sys
# Import the email modules we'll need
from email.mime.text import MIMEText


def send_mail(content,source,dest,server,login,password,title="Voici votre code personnel" ):
    msg = MIMEText(content,'plain', 'utf-8')
    f_title = "[Election NP] %s" %title
    msg['Subject'] = f_title
    msg['From'] = source
    msg['To'] = dest
    s= smtplib.SMTP_SSL(server)
    s.set_debuglevel(0)
    s.connect(server, 465)
    s.login(login, password)
    return_info =s.sendmail(msg['From'], [msg["To"]], msg.as_string())
    s.quit()
    return return_info

if __name__ == "__main__":
    import sys
    send_me_mail(sys.argv[1],sys.argv[1])
