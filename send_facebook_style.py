#!/usr/bin/env python3
"""
Send Facebook-style confirmation email with tracking link
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import argparse
from jinja2 import Template

def send_facebook_style_email(
    recipient_email,
    user_name,
    confirm_url,
    sender_email="security@facebookmail.com",
    custom_date=None
):
    """
    Send Facebook-style confirmation email
    
    Args:
        recipient_email: Email address to send to
        user_name: Name of the recipient
        confirm_url: URL for the confirmation button (Railway tracking link)
        sender_email: Email to send from
        custom_date: Optional custom date string
    """
    
    # Read HTML template
    with open('templates/facebook_style_email.html', 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Render template with variables
    template = Template(template_content)
    html_content = template.render(
        user_name=user_name,
        confirm_url=confirm_url,
        recipient_email=recipient_email
    )
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'{user_name}, confirm your email address'
    msg['From'] = f'Facebook <{sender_email}>'
    msg['To'] = recipient_email
    
    # Set custom date if provided
    if custom_date:
        msg['Date'] = custom_date
    
    # Plain text version (fallback)
    text_content = f"""
Hi {user_name},

We got your request to add this email address to your account.

Confirm your email by visiting this link:
{confirm_url}

Don't share this confirmation with anyone.

Thanks,
Facebook Security

---
This message was sent to {recipient_email}
© Facebook. Meta Platforms, Inc.
"""
    
    # Attach both versions
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')
    
    msg.attach(part1)
    msg.attach(part2)
    
    # Send email
    print(f"📧 Sending Facebook-style email to {recipient_email}...")
    print(f"🔗 Confirmation URL: {confirm_url}")
    
    try:
        # Get MX record for recipient
        import dns.resolver
        domain = recipient_email.split('@')[1]
        mx_records = dns.resolver.resolve(domain, 'MX')
        mx_server = str(mx_records[0].exchange).rstrip('.')
        
        print(f"📬 MX server: {mx_server}")
        
        # Connect and send
        with smtplib.SMTP(mx_server, 25, timeout=30) as server:
            server.send_message(msg)
        
        print("✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Send Facebook-style confirmation email')
    parser.add_argument('--to', required=True, help='Recipient email address')
    parser.add_argument('--name', required=True, help='Recipient name')
    parser.add_argument('--url', required=True, help='Confirmation URL (Railway tracking link)')
    parser.add_argument('--from', dest='sender', default='security@facebookmail.com', 
                       help='Sender email (default: security@facebookmail.com)')
    parser.add_argument('--date', help='Custom date string (e.g., "Mon, 1 Jan 2024 12:00:00 +0000")')
    
    args = parser.parse_args()
    
    send_facebook_style_email(
        recipient_email=args.to,
        user_name=args.name,
        confirm_url=args.url,
        sender_email=args.sender,
        custom_date=args.date
    )

if __name__ == '__main__':
    main()
