import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import markdown

def send_email(date_str, report_md):
    sender_email = os.environ.get("EMAIL_SENDER")
    app_password = os.environ.get("EMAIL_PASSWORD")
    recipients_env = os.environ.get("EMAIL_RECIPIENTS", "jtkim86@coway.com")
    recipients = [email.strip() for email in recipients_env.split(",")]
    
    if not sender_email or not app_password:
        print("Email credentials not found in environments. Skipping email sending.")
        return
        
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"📊 [AI 가전 뉴스룸] {date_str} 트렌드 브리핑"
    msg["From"] = sender_email
    msg["To"] = ", ".join(recipients)
    
    html_infographic = ""
    if "```html" in report_md:
        html_infographic = report_md.split("```html")[1].split("```")[0]
        report_md = report_md.replace(f"```html\n{html_infographic}\n```", "")
        
    # Convert remaining MD to HTML
    body_html = markdown.markdown(report_md)
    
    app_url = "https://homeappliances-ainews.streamlit.app/"
    
    email_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; background: #f0f2f5; margin: 0; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
            h2.title {{ text-align: center; color: #1a1a1a; border-bottom: 2px solid #007bff; padding-bottom: 15px; }}
            .btn-cta {{ display: block; width: 300px; margin: 30px auto; padding: 15px 0; background-color: #00f3ff; color: #0b0b1a !important; text-decoration: none; font-weight: 800; border-radius: 8px; text-align: center; font-size: 18px; box-shadow: 0 0 15px rgba(0, 243, 255, 0.5); }}
            .dashboard-preview {{ margin-bottom: 30px; border: 2px solid #ccc; padding: 15px; background: #0b0b1a; color: white; border-radius: 10px; overflow: hidden; }}
            .content {{ padding: 20px; background: #fafafa; border-radius: 8px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2 class="title">🚀 {date_str} 생성형 AI 가전/IT 정밀 브리핑</h2>
            
            <a href="{app_url}" class="btn-cta">🌐 웹사이트에서 원본 리포트 풀버전 열기</a>

            <!-- 인포그래픽 상단 배치 영역 -->
            <div class="dashboard-preview">
                {html_infographic}
            </div>
            
            <hr style="border:1px solid #ddd; margin: 30px 0;">
            
            <div class="content">
                {body_html}
            </div>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText("본 메일은 스마트폰 또는 PC의 이메일 앱에서 HTML 보기를 지원해야 정상적으로 표시됩니다.", "plain"))
    msg.attach(MIMEText(email_html, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipients, msg.as_string())
        print(f"Email sent successfully to {recipients}")
    except Exception as e:
        print(f"Failed to send email: {e}")
