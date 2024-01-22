from dublib.Methods import CheckPythonMinimalVersion, MakeRootDirectories, ReadJSON, RemoveFolderContent, RemoveRecurringSubstrings, RemoveRegexSubstring
from dublib.StyledPrinter import *
from dublib.Terminalyzer import *
from Source.BotManager import *
from Source.Functions import *
from Source.CLI import CLI
from telebot import types
from io import StringIO
				
import telebot
import sys

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

# Проверка поддержки используемой версии Python.
CheckPythonMinimalVersion(3, 10)
# Создание папок в корневой директории.
MakeRootDirectories(["Attachments", "Data/Sessions"])
# Глобальные определения.
VERSION = "1.0.0"

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Чтение настроек.
Settings = ReadJSON("Settings.json")
# Если токен не указан, выбросить исключение.
if type(Settings["token"]) != str or Settings["token"].strip() == "": raise Exception("Invalid Telegram bot token.")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

# Список описаний обрабатываемых команд.
CommandsList = list()

# Создание команды: execute.
COM_execute = Command("execute")
COM_execute.addArgument(ArgumentType.All, Important = True)
CommandsList.append(COM_execute)

# Создание команды: run.
COM_run = Command("run")
CommandsList.append(COM_run)

# Инициализация обработчика консольных аргументов.
CAC = Terminalyzer()
# Получение информации о проверке команд. 
CommandDataStruct = CAC.checkCommands(CommandsList)

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

# Обработка команды: execute.
if CommandDataStruct != None and "execute" == CommandDataStruct.Name:
	# Запуск обработчика консольных команд.
	CLI(Settings, VERSION, False).processCommand(CommandDataStruct.Arguments[0].replace("+", " "))
	
# Обработка команды: run.
elif CommandDataStruct != None and "run" == CommandDataStruct.Name:
	# Запуск обработчика консольных команд.
	CLI(Settings, VERSION).runLoop()
	
# Запуск Telegram бота.
else:
	
	# Токен для работы определенного бота телегамм.
	Bot = telebot.TeleBot(Settings["token"])
	# Менеджер данных бота.
	BotProcessor = BotManager(Settings, Bot)
	# Установка ожидаемого типа значения.
	if Settings["statuses"]["collect-media"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Image)
	if Settings["statuses"]["targeting"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Targets)
	if Settings["statuses"]["terminal"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Terminal)
	
	# Обработка команды: start.
	@Bot.message_handler(commands = ["start"])
	def Command(Message: types.Message):
		# Авторизация пользователя.
		Admin = BotProcessor.login(Message.from_user)
	
		# Если пользователь является администратором.
		if Admin == True:
			# Отправка сообщения: меню администратора.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *разрешён*\n\n_Панель администрирования открыта\._",
				parse_mode = "MarkdownV2",
				reply_markup = BuildAdminMenu(BotProcessor)
			)
			
		else:
			# Отправка сообщения: права администратора невалидны.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *запрещён*",
				parse_mode = "MarkdownV2"
			)
		
	# Обработка команды: unattach.
	@Bot.message_handler(commands=["unattach"])
	def Command(Message: types.Message):
	
		# Если пользователь уже администратор.
		if BotProcessor.login(Message.from_user) == True:
			# Удаление текущих вложений.
			RemoveFolderContent("Attachments")
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
			# Отправка сообщения: приветствие.
			Bot.send_message(
				Message.chat.id,
				"🖼️ *Добавление вложений*\n\nВсе вложения удалены\.",
				parse_mode = "MarkdownV2",
				disable_web_page_preview = True,
				reply_markup = BuildAdminMenu(BotProcessor)
			)
		
	# Обработка текстовых сообщений.
	@Bot.message_handler(content_types = ["text"])
	def TextMessage(Message: types.Message):
		# Авторизация пользователя.
		Admin = BotProcessor.login(Message.from_user)
		# Ожидаемый тип значения.
		ExcpectedValue = BotProcessor.getExpectedType()
		
		# Если пользователь является администратором.
		if Admin == True:
			
			# Тип сообщения: текст.
			if ExcpectedValue == ExpectedMessageTypes.Message:
				# Сохранение нового текста.
				Result = BotProcessor.editMessage(Message.html_text)
				# Комментарий.			
				Comment = "Текст сообщения изменён\." if Result == True else EscapeCharacters("Сообщение слишком длинное! Telegram устанавливает следующие лимиты:\n\n4096 символов – обычное сообщение;\n2048 символов – сообщение с вложениями (Premium);\n1024 символа – сообщение с вложениями.")
				# Отправка сообщения: редактирование приветствия завершено.
				Bot.send_message(
					Message.chat.id,
					"✍ *Редактирование сообщения*\n\n" + Comment,
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True,
					reply_markup = BuildAdminMenu(BotProcessor)
				)
				# Установка ожидаемого типа сообщения.
				BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: консольная команда.
			if ExcpectedValue == ExpectedMessageTypes.Terminal and "📟" not in Message.text:
				# Приведение текста сообщения к нужному формату.
				MessageBufer = RemoveRecurringSubstrings(Message.text.lower(), " ")
				
				#==========================================================================================#
				# >>>>> DEPRECATED <<<<< #
				#==========================================================================================#

				# Если для выполнения команды не требуется Telethon и команда поддерживает трансляцию.
				if MessageBufer not in ["reconnect", "register", "send", "start"] and MessageBufer not in ["cls", "exit"]:
					# Буфер консольного вывода.
					Bufer = StringIO()
					# Установка буфера.
					sys.stdout = Bufer
					# Запуск обработчика команды.
					CLI(Settings, VERSION, False).processCommand(MessageBufer)
					# Вывод.
					Output = Bufer.getvalue()
					# Очистка стилей.
					Output = RemoveRegexSubstring(Output, "\[\d{1,2}m")
					
					# Если выполняется команда помощи.
					if "help" in MessageBufer:
						# Форматирование вывода.
						Output = Output.replace("  ", "\n")
						Output = RemoveRecurringSubstrings(Output, "\n")
						Output = Output.replace("\n ", "\n")
						Output = Output.replace("-", "")
						Output = Output.split("\n")
						
						# Для каждой строки.
						for Index in range(0, len(Output)): 
							# Если строка в нижнем регистре, выделить её курсивом.
							if Output[Index].islower() == True: Output[Index] = "\n> " + Output[Index]
							
						# Объединение строк.
						Output = "\n".join(Output)

					# Отправка сообщения: вывод терминала.
					if Output != "": Bot.send_message(
						Message.chat.id,
						EscapeCharacters(Output),
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
						
				# Если команду невозможно выполнить.
				elif MessageBufer in ["cls", "exit"]:
					# Отправка сообщения: команда не поддерживается.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nКоманда не поддерживает трансляцию через бота\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
						
				else:
					# Отправка сообщения: команда не поддерживается.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nВыполнение данной команды требует асинхронного исполнения модуля библиотеки [Telethon](https://github.com/LonamiWebs/Telethon) и потому не может быть запущено\. Используйте протокол SSH для прямого доступа к терминалу сервера\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)

			# Тип сообщения: неопределённый.
			if ExcpectedValue == ExpectedMessageTypes.Undefined:
				
				# Редактирование поста.
				if Message.text == "✍ Редактировать":
					# Отправка сообщения: редактирование приветствия.
					Bot.send_message(
						Message.chat.id,
						"✍ *Редактирование сообщение*\n\nОтправьте мне текст нового сообщения\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Message)
				
				# Добавление вложений.
				if Message.text == "🖼️ Медиа":
					# Запуск коллекционирования.
					BotProcessor.collect(True)
					# Отправка сообщения: добавление вложений.
					Bot.send_message(
						Message.chat.id,
						"🖼️ *Добавление вложений*\n\nОтправляйте мне изображения, которые необходимо прикрепить к сообщению, или выполните команду /unattach для удаления всех вложений\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Image)
					
				# Предпросмотр сообщения.
				if Message.text == "🔍 Предпросмотр":
					# Отправка сообщения: предпросмотр сообщения.
					BotProcessor.sendMessage(Message.chat.id)
					
				# Отправка списка целей.
				if Message.text == "👥 Аудитория":
					# Включение терминала.
					BotProcessor.waitAuditorium(True)
					# Отправка сообщения: редактирование приветствия.
					Bot.send_message(
						Message.chat.id,
						"*👥 Список целей*\n\nОтправьте мне таблицу Excel от @botparser\_bot\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Targets)
					
				# Включение терминала.
				if Message.text == "📟 Терминал":
					# Включение терминала.
					BotProcessor.useTerminal(True)
					# Отправка сообщения: запуск терминала.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nЗапущен консольный интерфейс\. Все символы будут автоматически приведены к нижнему регистру\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Terminal)
					
				# Вывод помощи.
				if Message.text == "❓ Помощь":
					# Отправка сообщения: помощь.
					Bot.send_message(
						Message.chat.id,
						"*❓ Помощь*\n\nЗадайте список пользователей для рассылки, настройте сообщение и вложения и откройте терминал, чтобы продолжить работу\. Дополнительные сведения о взаимодействии с консолью доступны внутри неё при выполнении команды *help*\.\n\nОтправьте /unattach, чтобы удалить все вложения\.\n\nПодробнее на [GitHub](https://github.com/DUB1401/SpamBot)\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					
			# Тип сообщения: команда остановки сбора вложения.
			if ExcpectedValue in [ExpectedMessageTypes.Image, ExpectedMessageTypes.Undefined]:
				
				# Остановка добавления вложений.
				if Message.text == "🖼️ Медиа (остановить)":
					# Запуск коллекционирования.
					BotProcessor.collect(False)
					# Количество вложений.
					AttachmentsCount = BotProcessor.getAttachmentsCount()
					# Отправка сообщения: добавление вложений.
					Bot.send_message(
						Message.chat.id,
						f"*🖼️ Добавление вложений*\n\nКоличество вложений: {AttachmentsCount}\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: отмена выбора аудитории.
			if ExcpectedValue in [ExpectedMessageTypes.Targets, ExpectedMessageTypes.Undefined]:
				
				# Отключение терминала.
				if Message.text == "👥 Отменить":
					# Включение терминала.
					BotProcessor.waitAuditorium(False)
					# Отправка сообщения: отмена процедуры.
					Bot.send_message(
						Message.chat.id,
						"*👥 Аудитория*\n\nВыбор целевой аудитории отменён\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: закрытие терминала.
			if ExcpectedValue in [ExpectedMessageTypes.Terminal, ExpectedMessageTypes.Undefined]:
				
				# Отключение терминала.
				if Message.text == "📟 Закрыть":
					# Отключение терминала.
					BotProcessor.useTerminal(False)
					# Отправка сообщения: терминал недоступен.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nОболочка консольного интерфейса закрыта\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
							
		# Если введён верный пароль.
		elif Message.text == Settings["password"]: 
			# Выдача прав администратора.
			Admin = BotProcessor.login(Message.from_user, Admin = True)
			# Отправка сообщения: меню администратора.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *разрешён*\n\n_Панель администрирования открыта\._",
				parse_mode = "MarkdownV2",
				reply_markup = BuildAdminMenu(BotProcessor)
			)
				
	# Обработка изображений (со сжатием).					
	@Bot.message_handler(content_types=["photo"])
	def MediaAttachments(Message: types.Message):
		# Ожидаемый тип значения.
		ExcpectedValue = BotProcessor.getExpectedType()
		
		# Тип сообщения: вложение.
		if ExcpectedValue == ExpectedMessageTypes.Image:
			# Сохранение изображения.
			DownloadImage(Settings["token"], Bot, Message.photo[-1].file_id)
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined) 

	# Обработка изображений (без сжатия) и документов.					
	@Bot.message_handler(content_types=["document"])
	def MediaAttachments(Message: types.Message):
		# Ожидаемый тип значения.
		ExpectedValue = BotProcessor.getExpectedType()
	
		# Тип сообщения: вложение.
		if ExpectedValue == ExpectedMessageTypes.Image:
			# Сохранение изображения.
			DownloadImage(Settings["token"], Bot, Message.document.file_id)
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
			
		# Тип сообщения: список целей.
		if ExpectedValue == ExpectedMessageTypes.Targets:
			# Отправка сообщения: файл загружается.
			SendedMessage = Bot.send_message(
				chat_id = Message.chat.id,
				text = "*👥 Список целей*\n\nФайл загружается\.\.\.",
				parse_mode = "MarkdownV2"
			)
			# Загрузка документа.
			DownloadDoc(Settings["token"], Bot, Message.document.file_id)
			
			# Если преобразование успешно.
			if ConvertExcelToJSON() == True:
				# Редактирование сообщения: файл принят.
				Bot.edit_message_text(
					text = "*👥 Список целей*\n\nФайл загружен и обработан\.",
					chat_id = SendedMessage.chat.id,
					message_id = SendedMessage.message_id,
					parse_mode = "MarkdownV2"
				)
				
			else:
				# Редактирование сообщения: файл принят.
				Bot.edit_message_text(
					text = "*👥 Список целей*\n\nНе удалось обработать файл\.",
					chat_id = SendedMessage.chat.id,
					message_id = SendedMessage.message_id,
					parse_mode = "MarkdownV2"
				)
				
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
		
	# Запуск обработки запросов Telegram.
	Bot.infinity_polling(allowed_updates = telebot.util.update_types)