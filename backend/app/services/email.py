"""
Resend email client for report delivery.
Falls back to console logging when RESEND_API_KEY is not configured.
"""

import logging
from app.config import settings

logger = logging.getLogger(__name__)


def send_report_email(
    subject: str,
    markdown_content: str,
    recipient: str = None,
) -> bool:
    """
    Send the generated report via Resend.
    If RESEND_API_KEY is not configured, logs the email to console.
    """
    to_email = recipient or settings.DELIVERY_EMAIL

    if not settings.RESEND_API_KEY:
        logger.info("── MOCK EMAIL DISPATCH ──────────────────────────")
        logger.info(f"  To:      {to_email}")
        logger.info(f"  Subject: {subject}")
        logger.info(f"  Content: {len(markdown_content)} chars")
        logger.info("  Configure RESEND_API_KEY in .env for real emails.")
        logger.info("─────────────────────────────────────────────────")
        return True

    try:
        import resend

        resend.api_key = settings.RESEND_API_KEY

        html_content = f"""
        <html>
            <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                         line-height: 1.6; color: #1f2937; background-color: #f9fafb; 
                         padding: 20px;">
                <div style="max-width: 700px; margin: 0 auto; background-color: #ffffff; 
                            padding: 30px; border-radius: 12px; 
                            border: 1px solid #e5e7eb; 
                            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
                        <div style="width: 40px; height: 40px; border-radius: 10px; 
                                    background: linear-gradient(135deg, #3b82f6, #8b5cf6); 
                                    display: flex; align-items: center; justify-content: center;">
                            <span style="color: white; font-size: 20px;">🛡️</span>
                        </div>
                        <div>
                            <h1 style="color: #1e3a8a; margin: 0; font-size: 22px;">
                                Business Intelligence Sentinel
                            </h1>
                            <p style="color: #6b7280; font-size: 13px; margin: 0;">
                                Automated Market Intelligence Report
                            </p>
                        </div>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 20px 0;" />
                    <div style="font-size: 15px; color: #374151; white-space: pre-wrap;">
                        {markdown_content}
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e5e7eb; margin: 25px 0;" />
                    <p style="font-size: 12px; color: #9ca3af; text-align: center; margin: 0;">
                        Sent by Business Intelligence Sentinel · 
                        Manage watchlists in your dashboard
                    </p>
                </div>
            </body>
        </html>
        """

        logger.info(f"Sending report email to {to_email}...")
        response = resend.Emails.send({
            "from": "Sentinel <onboarding@resend.dev>",
            "to": [to_email],
            "subject": subject,
            "html": html_content,
        })

        response_id = response.get("id") if isinstance(response, dict) else "sent"
        logger.info(f"✅ Email sent. ID: {response_id}")
        return True

    except Exception as e:
        logger.error(f"❌ Email send failed: {e}")
        return False
