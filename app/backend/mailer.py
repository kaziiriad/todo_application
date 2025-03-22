from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os


mail_config = ConnectionConfig(
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "your-email@example.com"),
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "your-password"),
    MAIL_FROM = os.getenv("MAIL_FROM", "your-email@example.com"),
    MAIL_PORT = int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_TLS = True,
    MAIL_SSL = False
)

# Frontend URL for links
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")


async def send_invite_email(email: str, room_name: str, invite_code: str):
    """
    Send an invitation email to join a task room.
    
    Args:
        email: Recipient email address
        room_name: Name of the room
        invite_code: Invite code for the room
    """
    message = MessageSchema(
        subject=f"Invitation to join task room: {room_name}",
        recipients=[email],
        body=f"""
        You've been invited to join the task room "{room_name}"!
        
        Click the link below to join:
        {FRONTEND_URL}/join-room?invite_code={invite_code}
        
        This link will take you to the login page if you're not already logged in.
        """
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)


async def send_magic_link_email(email: str, token: str):
    """
    Send a magic link email for authentication.
    
    Args:
        email: Recipient email address
        token: Authentication token
    """
    message = MessageSchema(
        subject="Your login link for Task Manager",
        recipients=[email],
        body=f"""
        Hello!
        
        Click the link below to log in to your Task Manager account:
        {FRONTEND_URL}/auth/verify?token={token}
        
        This link will expire in 15 minutes and can only be used once.
        
        If you didn't request this link, you can safely ignore this email.
        """
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)
