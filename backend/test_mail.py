import smtplib
from email.mime.text import MIMEText
msg = MIMEText("Teste", "plain")
msg["From"] = "Agendamento Qualivida <naorespondases@saude.pe.gov.br>"
msg["To"] = "williams.sobrinho@saude.local" # local user
msg["Subject"] = "Teste"
try:
    server = smtplib.SMTP("antispamout.ati.pe.gov.br", 587)
    server.starttls()
    server.login("dgiis.ses", "$35dG!1s")
    server.sendmail("naorespondases@saude.pe.gov.br", "williams.sobrinho@saude.local", msg.as_string())
    server.quit()
    print("OK")
except Exception as e:
    print(e)
