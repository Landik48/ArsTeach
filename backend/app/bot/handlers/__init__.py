"""Роутеры бота.

Каждый файл — отдельный Router, как в aiogram. Порядок в списке важен:
апдейт получает первый подходящий хендлер, поэтому «ловушка всего» (echo)
подключается последней.
"""

from app.bot.handlers import echo, start

routers = [start.router, echo.router]
