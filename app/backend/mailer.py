from fastapi_mail import FastMail, MessageSchema, ConnectionConfig


mail_config = ConnectionConfig(
    MAIL_USERNAME = "your-email@example.com",
    MAIL_PASSWORD = "your-password",
    MAIL_FROM = "your-email@example.com",
    MAIL_PORT = 587,
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_TLS = True,
    MAIL_SSL = False
)


async def send_invite_email(email: str, room_name: str, invite_code: str):
    message = MessageSchema(
        subject=f"Invitation to join task room: {room_name}",
        recipients=[email],
        body=f"""
        You've been invited to join the task room "{room_name}"!
        Click the link below to join:
        http://yourdomain.com/join-room?invite_code={invite_code}&email={email}
        """
    )

    fm = FastMail(mail_config)
    await fm.send_message(message)
