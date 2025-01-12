from Source.UI.Menu.Keyboards import ReplyKeyboards

from dublib.TelebotUtils.Users import UsersManager
from telebot import TeleBot, types

import shutil

class Decorators:
	"""Коллекция декораторов."""

	def reply_buttons(bot: TeleBot, users: UsersManager):
		"""
		Коллекция декораторов: Reply-кнопки.
			bot – бот Telegram;\n
			users – менеджер пользователей.
		"""

		@bot.message_handler(content_types = ["text"], regexp = "❓ Помощь")
		def Button(Message: types.Message):
			Text = "<i>Данный интерфейс служит лишь для удобной настройки рассылаемых сообщений. Для работы с программой используйте консольный режим.</i>" + "\n\n"
			Text += "<b>Как пользоваться рассылкой сообщений?</b>" + "\n\n"
			Text += "1. Нажмите кнопку <i>Сообщение</>. В открывшемся меню задайте текст и, если нужно, вложения, следуя инструкциям." + "\n\n"
			Text += "2. Нажмите кнопку <i>Выборка</i> и загрузите файл Excel с целями для рассылки." + "\n\n"
			Text += "3. Откройте консольный интерфейс, запустив главный файл <code>python main.py -c</code>. Введите ваш ключ (/start для повторного вывода)." + "\n\n"
			Text += "4. Подключите аккаунты Telegram командой <code>register</code> и используйте <code>mail</code> для начала рассылки." + "\n\n"
			Text += "Репозиторий <a href=\"https://github.com/DUB1401/SpamBot\">GitHub</a>."
			bot.send_message(
				chat_id = Message.chat.id,
				text = Text,
				parse_mode = "HTML",
				disable_web_page_preview = True
			)

		@bot.message_handler(content_types = ["text"], regexp = "❌ Закрыть")
		def Button(Message: types.Message):
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Всего доброго!",
				reply_markup = types.ReplyKeyboardRemove()
			)

		@bot.message_handler(content_types = ["text"], regexp = "↩️ Назад")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type(None)
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Перехожу в главное меню.",
				reply_markup = ReplyKeyboards.menu()
			)

		@bot.message_handler(content_types = ["text"], regexp = "✉️ Сообщение")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)

			bot.send_message(
				chat_id = Message.chat.id,
				text = "Панель редактирования сообщения.",
				reply_markup = ReplyKeyboards.message(User)
			)

		@bot.message_handler(content_types = ["text"], regexp = "🔎 Просмотр")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			
			if not User.get_property("message"):
				bot.send_message(
					chat_id = Message.chat.id,
					text = "Вы не задали текст сообщения."
				)
				return
			
			Text = User.get_property("message")
			Attachments = User.get_property("attachments")

			if Attachments:
				MediaGroup = list()
				
				for File in Attachments:
					Path = f"Data/Temp/{User.id}/Attachments/" + File["filename"]

					if File["type"] == "photo": 
						MediaGroup.append(types.InputMediaPhoto(open(Path, "rb"), caption = Text, parse_mode = "HTML"))
						Text = None

					elif File["type"] == "video": 
						MediaGroup.append(types.InputMediaPhoto(open(Path, "rb"), caption = Text, parse_mode = "HTML"))
						Text = None

				bot.send_media_group(
					chat_id = Message.chat.id,
					media = MediaGroup
				)

			else:
				bot.send_message(
					chat_id = Message.chat.id,
					text = Text,
					parse_mode = "HTML"
				)

		@bot.message_handler(content_types = ["text"], regexp = "✏️ Изменить текст")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("message")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Отправьте мне текст сообщения. Для пересылки поддерживаются все стили Telegram.",
				reply_markup = ReplyKeyboards.message(User)
			)

		@bot.message_handler(content_types = ["text"], regexp = "🏞️ Добавить вложение")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("attachment")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Выберите тип вложения.",
				reply_markup = ReplyKeyboards.media_select()
			)

		@bot.message_handler(content_types = ["text"], regexp = "🖼️ Изображение")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("image")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Пришлите мне изображение.",
				reply_markup = ReplyKeyboards.cancel()
			)

		@bot.message_handler(content_types = ["text"], regexp = "🎬 Видео")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("video")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Пришлите мне видео. Учтите, что ролики размером более 40 MB не будут доступны в предпросмотре сообщений из-за ограничений для бота.",
				reply_markup = ReplyKeyboards.cancel()
			)

		@bot.message_handler(content_types = ["text"], regexp = "🗑️ Удалить вложения")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_property("attachments", list())
			shutil.rmtree(f"Data/Temp/{User.id}/Attachments")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Вложения удалены.",
				reply_markup = ReplyKeyboards.message(User)
			)

		@bot.message_handler(content_types = ["text"], regexp = "👥 Выборка")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("targets")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Отправьте мне Excel-файл с вашей выборкой. Данные будут взяты из колонок <b>Username</b> и <b>Phone number</b>.",
				parse_mode = "HTML"
			)

		@bot.message_handler(content_types = ["text"], regexp = "🚫 Отменить редактирование")
		def Button(Message: types.Message):
			User = users.auth(Message.from_user)
			User.set_expected_type("targets")
			bot.send_message(
				chat_id = Message.chat.id,
				text = "Редактирование отменено.",
				reply_markup = ReplyKeyboards.message(User)
			)