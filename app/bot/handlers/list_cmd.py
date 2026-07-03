"""My list handlers."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.keyboards.inline import tracking_list_keyboard
from app.bot.texts.i18n import I18n
from app.services.tracking_service import TrackingService
from app.services.user_service import UserService
from app.utils.pagination import paginate

router = Router(name="list")


async def show_list(event: Message | CallbackQuery, session: AsyncSession, page: int = 1) -> None:
    user_service = UserService(session)
    if isinstance(event, CallbackQuery):
        user = await user_service.get_or_create_from_telegram(event.from_user.id)
    else:
        user = await user_service.get_or_create_from_telegram(event.from_user.id)  # type: ignore[union-attr]

    i18n = I18n(user.language)
    tracking_service = TrackingService(session)
    trackings = await tracking_service.get_user_list(user)

    if not trackings:
        msg = i18n.t("list_empty")
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(msg)  # type: ignore[union-attr]
        else:
            await event.answer(msg)
        return

    page_obj = paginate(trackings, page=page, per_page=5)
    lines = [i18n.t("my_list", count=len(trackings))]
    for t in page_obj.items:
        lines.append(tracking_service.format_tracking_item(t, user))
        lines.append("—")

    text = "\n\n".join(lines)
    keyboard = tracking_list_keyboard(
        list(page_obj.items), page_obj.page, page_obj.total_pages, i18n
    )

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)  # type: ignore[union-attr]
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.message(Command("minhalista", "mylist"))
async def cmd_my_list(message: Message, session: AsyncSession) -> None:
    await show_list(message, session)


@router.callback_query(F.data.startswith("list_page:"))
async def on_list_page(callback: CallbackQuery, session: AsyncSession) -> None:
    page = int(callback.data.split(":")[1])  # type: ignore[union-attr]
    await show_list(callback, session, page=page)
    await callback.answer()