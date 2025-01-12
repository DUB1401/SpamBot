from Source.UI.Menu import Decorators, ReplyKeyboards
from Source.Core.Mailing import Mailer
from Source.CLI import Interaction

from dublib.CLI.Terminalyzer import Command, ParametersTypes, Terminalyzer
from dublib.Methods.Filesystem import MakeRootDirectories, ReadJSON
from dublib.Methods.System import CheckPythonMinimalVersion, Clear
from dublib.TelebotUtils.Users import UsersManager
from telebot import TeleBot, types

import requests
import os

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ <<<<< #
#==========================================================================================#

CheckPythonMinimalVersion(3, 10)
MakeRootDirectories(["Data/Sessions"])
Settings = ReadJSON("Settings.json")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

Com = Command("run")
ComPos = Com.create_position("MODE", "Режим запуска SpamBot.")
Com.add_flag("s", "Запускает бота-редактора Telegram.")
Com.add_flag("c", "Запускает CLI.")
Com.add_key("key", ParametersTypes.Number, "Указывает ключ пользователя для автоматического входа.")

Analyzer = Terminalyzer()
Analyzer.enable_help(True)
ParsedCommand = Analyzer.check_commands(Com)
Users = UsersManager("Data/Users")

#==========================================================================================#
# >>>>> ЗАПУСК CLI-РЕЖИМА <<<<< #
#==========================================================================================#

if not ParsedCommand or ParsedCommand.check_flag("c"):
	UserKey = None
	if ParsedCommand: UserKey = ParsedCommand.get_key_value("key")
	InteractionObject = Interaction(Settings)
	InteractionObject.title()
	InteractionObject.auth(UserKey)
	InteractionObject.run()

#==========================================================================================#
# >>>>> ЗАПУСК БОТА <<<<< #
#==========================================================================================#

Clear()
Bot = TeleBot(Settings["token"])

@Bot.message_handler(commands = ["start"])
def BotProcessCommand(Message: types.Message):
	User = Users.auth(Message.from_user)
	User.set_property("message", None, force = False)
	User.set_property("attachment", None, force = False)

	if User.has_permissions("admin"):
		Bot.send_message(
			chat_id = Message.chat.id,
			text = f"🔒 Доступ к функциям <b>разрешён</b>. Ваш ключ: <code>{User.id}</code>.",
			parse_mode = "HTML",
			reply_markup = ReplyKeyboards.menu()
		)

	elif Message.text.endswith(Settings["password"]):
		Bot.send_message(
			chat_id = Message.chat.id,
			text = f"🔒 Пароль принят. Доступ к функциям <b>разрешён</b>. Ваш ключ: <code>{User.id}</code>.",
			parse_mode = "HTML",
			reply_markup = ReplyKeyboards.menu()
		)
		User.add_permissions("admin")
		
	else:
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "🔒 Доступ к функциям <b>запрещён</b>. Запросите пароль у администратора.",
			parse_mode = "HTML"
		)

Decorators.reply_buttons(Bot, Users)

@Bot.message_handler(content_types = ["text"])
def BotProcessText(Message: types.Message):
	User = Users.auth(Message.from_user)

	if User.expected_type == "message":
		User.set_property("message", Message.html_text)
		User.set_expected_type(None)
		Bot.send_message(
			chat_id = Message.chat.id,
			text = "Текст сохранён."
		)

@Bot.message_handler(content_types = ["photo"])
def BotProcessText(Message: types.Message):
	User = Users.auth(Message.from_user)

	if User.expected_type == "image":
		User.set_expected_type(None)
		Bot.send_chat_action(Message.chat.id, "typing")

		try:
			Photo = Message.photo[-1]
			FileInfo = Bot.get_file(Photo.file_id)
			Filename = FileInfo.file_path.split("/")[-1]
			FileURL = f"https://api.telegram.org/file/bot{Bot.token}/{FileInfo.file_path}"
			FileDirectory = f"Data/Temp/{User.id}/Attachments"
			if not os.path.exists(FileDirectory): os.makedirs(FileDirectory)
			with open(f"{FileDirectory}/{Filename}", "wb") as FileWriter: FileWriter.write(requests.get(FileURL).content)

			Attachments: list[dict] = User.get_property("attachments")
			Attachments.append({"filename": Filename, "type": "photo"})
			User.set_property("attachments", Attachments)

			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Изображение добавлено в сообщение.",
				reply_markup = ReplyKeyboards.message(User)
			)

		except:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Не удаётся использовать это изображение для рассылки."
			)

@Bot.message_handler(content_types = ["video"])
def BotProcessText(Message: types.Message):
	User = Users.auth(Message.from_user)

	if User.expected_type == "video":
		User.set_expected_type(None)
		Bot.send_chat_action(Message.chat.id, "typing")

		try:
			Video = Message.video
			FileInfo = Bot.get_file(Video.file_id)
			Filename = FileInfo.file_path.split("/")[-1]
			FileURL = f"https://api.telegram.org/file/bot{Bot.token}/{FileInfo.file_path}"
			FileDirectory = f"Data/Temp/{User.id}/Attachments"
			if not os.path.exists(FileDirectory): os.makedirs(FileDirectory)
			with open(f"{FileDirectory}/{Filename}", "wb") as FileWriter: FileWriter.write(requests.get(FileURL).content)

			Attachments: list[dict] = User.get_property("attachments")
			Attachments.append({"filename": Filename, "type": "video"})
			User.set_property("attachments", Attachments)

			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Видео добавлено в сообщение.",
				reply_markup = ReplyKeyboards.message(User)
			)

		except:
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "Не удаётся использовать это видео для рассылки."
			)

@Bot.message_handler(content_types = ["document"])
def BotProcessText(Message: types.Message):
	User = Users.auth(Message.from_user)

	if User.expected_type == "targets":
		User.set_expected_type(None)

		try:
			Document = Message.document
			FileInfo = Bot.get_file(Document.file_id)
			FileURL = f"https://api.telegram.org/file/bot{Bot.token}/{FileInfo.file_path}"
			FileDirectory = f"Data/Temp/{User.id}"
			if not os.path.exists(FileDirectory): os.makedirs(FileDirectory)
			with open(f"{FileDirectory}/targets.xlsx", "wb") as FileWriter: FileWriter.write(requests.get(FileURL).content)
			Mailer().parse_targets_from_excel(User)
			Bot.send_message(chat_id = Message.chat.id, text = "Выборка сохранена.")

		except ZeroDivisionError:
			Bot.send_message(chat_id = Message.chat.id, text = "Не удалось изъять выборку из данного файла.")

Bot.infinity_polling()