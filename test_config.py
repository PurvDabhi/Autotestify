from config import Config

print("GitHub Token:", Config.GITHUB_TOKEN[:6] + "..." if Config.GITHUB_TOKEN else "Not loaded")
print("Mail Sender:", Config.MAIL_DEFAULT_SENDER)
print("TLS:", Config.MAIL_USE_TLS)