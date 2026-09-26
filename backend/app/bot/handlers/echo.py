"""Эхо на любой текст — последний роутер, ловит всё, что не поймали другие."""

from maxapi import F, Router
from maxapi.types import MessageCreated

router = Router(router_id="echo")


@router.message_created(F.message.body.text)
async def echo(event: MessageCreated) -> None:
    await event.message.answer(f"Ты написал: {event.message.body.text}")
