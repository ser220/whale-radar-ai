from __future__ import annotations


class TelegramAlertAdapter:
    """
    Telegram delivery boundary.

    No Arkham logic.
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
    ) -> None:

        self.bot_token = bot_token
        self.chat_id = chat_id
        self.sent_messages = []


    def send(
        self,
        message: str,
    ) -> None:

        if not isinstance(
            message,
            str,
        ):
            raise TypeError(
                "message must be string"
            )

        self.sent_messages.append(
            message
        )


    def history(self):

        return tuple(
            self.sent_messages
        )


__all__ = [
    "TelegramAlertAdapter",
]
