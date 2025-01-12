from dublib.TelebotUtils.Users import UserData
from telebot import types

class ReplyKeyboards:
	"""Генератор Reply-интерфейса."""

	def cancel() -> types.ReplyKeyboardMarkup:
		"""Строит кнопочный интерфейс: отмена."""

		Menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
		Back = types.KeyboardButton("↩️ Назад")
		Menu.add(Back, row_width = 2)

		return Menu

	def menu() -> types.ReplyKeyboardMarkup:
		"""Строит кнопочный интерфейс: панель управления."""

		Menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
		Mail = types.KeyboardButton("✉️ Сообщение")
		Targets = types.KeyboardButton("👥 Выборка")
		Menu.add(Mail, Targets, row_width = 2)
		Help = types.KeyboardButton("❓ Помощь")
		Close = types.KeyboardButton("❌ Закрыть")
		Menu.add(Help, Close, row_width = 2)

		return Menu
	
	def media_select() -> types.ReplyKeyboardMarkup:
		"""Строит кнопочный интерфейс: выбор типа вложения."""

		Menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
		Image = types.KeyboardButton("🖼️ Изображение")
		Video = types.KeyboardButton("🎬 Видео")
		Back = types.KeyboardButton("↩️ Назад")
		Menu.add(Image, Video, Back, row_width = 2)

		return Menu
	
	def message(user: UserData) -> types.ReplyKeyboardMarkup:
		"""
		Строит кнопочный интерфейс: панель управления.
			user – данные пользователя.
		"""

		Menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
		View = types.KeyboardButton("🔎 Просмотр")
		EditText = types.KeyboardButton("🚫 Отменить редактирование") if user.expected_type == "message" else types.KeyboardButton("✏️ Изменить текст")
		Menu.add(View, EditText, row_width = 1)

		AttachmentsCount = len(user.get_property("attachments"))

		if AttachmentsCount < 10:
			RemoveMedia = types.KeyboardButton("🏞️ Добавить вложение") 
			Menu.add(RemoveMedia, row_width = 1)

		if AttachmentsCount > 0:
			AddMedia = types.KeyboardButton("🗑️ Удалить вложения") 
			Menu.add(AddMedia, row_width = 1)

		Back = types.KeyboardButton("↩️ Назад")
		Menu.add(Back, row_width = 1)

		return Menu