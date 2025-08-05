# from flask_mail import Mail, Message
# from flask import current_app
# import os

# class EmailService:
#     def __init__(self, mail: Mail):
#         self.mail = mail
    
#     def send_report_email(self, recipient_email: str, report_path: str, subject: str):
#         """Send report via email"""
#         try:
#             if not all([
#                 current_app.config.get('MAIL_USERNAME'),
#                 current_app.config.get('MAIL_PASSWORD'),
#                 current_app.config.get('MAIL_SERVER')
#             ]):
#                 print("Email configuration not complete. Skipping email send.")
#                 return False
            
#             msg = Message(
#                 subject=f'AutoTestify - {subject}',
#                 recipients=[recipient_email],
#                 sender=current_app.config.get('MAIL_DEFAULT_SENDER')
#             )
            
#             msg.body = f"""
#             Hello,

#             Your AutoTestify analysis report is ready!

#             Please find the detailed report attached to this email.

#             Report Details:
#             - Analysis Type: {subject}
#             - Generated: {os.path.getctime(report_path)}
#             - File Size: {os.path.getsize(report_path)} bytes

#             Thank you for using AutoTestify!

#             Best regards,
#             AutoTestify Team
#             """
            
#             msg.html = f"""
#             <html>
#             <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#                 <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
#                     <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
#                         <h1 style="margin: 0; font-size: 28px;">AutoTestify</h1>
#                         <p style="margin: 10px 0 0 0; font-size: 16px;">Your Analysis Report is Ready!</p>
#                     </div>
                    
#                     <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
#                         <h2 style="color: #495057; margin-top: 0;">Hello!</h2>
                        
#                         <p>Your AutoTestify analysis has been completed successfully. Please find the detailed report attached to this email.</p>
                        
#                         <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; margin: 20px 0;">
#                             <h3 style="margin-top: 0; color: #28a745;">Report Details</h3>
#                             <ul style="list-style-type: none; padding: 0;">
#                                 <li style="padding: 5px 0;"><strong>Analysis Type:</strong> {subject}</li>
#                                 <li style="padding: 5px 0;"><strong>Generated:</strong> Just now</li>
#                                 <li style="padding: 5px 0;"><strong>Format:</strong> HTML Report</li>
#                             </ul>
#                         </div>
                        
#                         <p>The report includes comprehensive analysis, visual charts, and actionable recommendations to improve your code quality and API performance.</p>
                        
#                         <div style="text-align: center; margin: 30px 0;">
#                             <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; border-radius: 25px; display: inline-block;">
#                                 <strong>Thank you for using AutoTestify!</strong>
#                             </div>
#                         </div>
                        
#                         <p style="color: #6c757d; font-size: 14px; margin-bottom: 0;">
#                             Best regards,<br>
#                             <strong>AutoTestify Team</strong>
#                         </p>
#                     </div>
#                 </div>
#             </body>
#             </html>
#             """
            
#             # Attach report file
#             with current_app.open_resource(report_path) as fp:
#                 msg.attach(
#                     filename=os.path.basename(report_path),
#                     content_type='text/html',
#                     data=fp.read()
#                 )
            
#             self.mail.send(msg)
#             return True
            
#         except Exception as e:
#             print(f"Error sending email: {str(e)}")
#             return False

import requests
import os

class EmailService:
    def __init__(self, config):
        self.api_key = config.get('MAILJET_API_KEY')
        self.api_secret = config.get('MAILJET_API_SECRET')
        self.sender_email = config.get('MAILJET_SENDER_EMAIL')
        self.sender_name = config.get('MAILJET_SENDER_NAME', 'AutoTestify')

    def send_report_email(self, recipient_email: str, report_path: str, subject: str):
        """Send report via Mailjet"""
        try:
            # Ensure Mailjet config is set
            if not all([self.api_key, self.api_secret, self.sender_email]):
                print("❌ Mailjet configuration is missing.")
                return False

            # Validate report path
            if not os.path.exists(report_path):
                print("❌ Report file does not exist.")
                return False

            # Read HTML report content
            with open(report_path, 'r', encoding='utf-8') as fp:
                report_html = fp.read()

            # Prepare Mailjet message payload
            payload = {
                'Messages': [
                    {
                        "From": {
                            "Email": self.sender_email,
                            "Name": self.sender_name
                        },
                        "To": [{"Email": recipient_email}],
                        "Subject": f"AutoTestify - {subject}",
                        "TextPart": (
                            "Hello,\n\n"
                            "Your AutoTestify analysis report is ready.\n\n"
                            "Please check the attached report for full details.\n\n"
                            "Thank you,\nAutoTestify Team"
                        ),
                        "HTMLPart": report_html
                    }
                ]
            }

            # Make API request
            response = requests.post(
                "https://api.mailjet.com/v3.1/send",
                auth=(self.api_key, self.api_secret),
                json=payload
            )

            # Check response
            if response.status_code == 200:
                print("✅ Email sent successfully via Mailjet!")
                return True
            else:
                print(f"❌ Failed to send email via Mailjet: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"❌ Exception while sending email: {str(e)}")
            return False

