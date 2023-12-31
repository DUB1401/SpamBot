from apscheduler.schedulers.background import BackgroundScheduler
from dublib.Methods import ReadJSON, RemoveHTML, WriteJSON
from Source.Functions import EscapeCharacters
from telebot import types
from time import sleep

import telebot
import random
import enum
import os

# Типы ожидаемых сообщений.
class ExpectedMessageTypes(enum.Enum):
	
	#---> Статические свойства.
	#==========================================================================================#
	# Неопределённое сообщение.
	Undefined = "undefined"
	# Текст сообщения.
	Message = "message"
	# Изображение.
	Image = "image"
	# Список целей рассылки.
	Targets = "targets"

# Менеджер данных бота.
class BotManager:
	
	# Сохраняет настройки.
	def __SaveSettings(self):
		# Сохранение настроек.
		WriteJSON("Settings.json", self.__Settings)
	
	# Конструктор.
	def __init__(self, Settings: dict, Bot: telebot.TeleBot):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Планировщик задач.
		self.__Planner = BackgroundScheduler()
		# Текущий тип ожидаемого сообщения.
		self.__ExpectedType = ExpectedMessageTypes.Undefined
		# Словарь определений пользователь.
		self.__Users = ReadJSON("Data/Users.json")
		# Глобальные настройки.
		self.__Settings = Settings.copy()
		# Экземпляр бота.
		self.__Bot = Bot
		
	# Переключает сбор изображений.
	def collect(self, Status: bool):
		# Переключение сбора изображений.
		self.__Settings["collect-media"] = Status
		# Сохранение настроек.
		self.__SaveSettings()
		
	# Изменяет текст рассылки.
	def editMessage(self, Text: str) -> bool:
		# Состояние: корректин ли текст.
		IsCorrected = True
		# Максимальная длина сообщения.
		MaxLength = 1024 if self.__Settings["premium"] == False else 2048
		if len(os.listdir("Data")) == 0: MaxLength = 4096 
		
		# Если сообщение слишком длинное.
		if len(RemoveHTML(Text)) >= MaxLength:
			# Отключение бота.
			self.disable()
			# Переключение состояния.
			IsCorrected = False
			
		else:
			# Запись сообщения.
			self.__Settings["message"] = Text
			# Сохранение настроек.
			self.__SaveSettings()
			
		return IsCorrected
	
	# Возвращает количество вложений.
	def getAttachmentsCount(self) -> int:
		# Подсчёт количества файлов.
		Count = len(os.listdir("Attachments"))
		
		return Count
		
	# Возвращает словарь параметров бота.
	def getData(self) -> dict:
		return self.__Settings.copy()

	# Возвращает тип ожидаемого сообщения.
	def getExpectedType(self) -> ExpectedMessageTypes:
		return self.__ExpectedType
	
	# Регистрирует пользователя или обновляет его данные.
	def login(self, User: telebot.types.User, Admin: bool = False) -> bool:
		# Конвертирование ID пользователя.
		UserID = str(User.id) 
		# Буфер данных пользователей.
		Bufer = {
			"first-name": User.first_name,
			"last-name": User.last_name,
			"username": User.username,
			"premium": bool(User.is_premium),
			"admin": Admin
		}
		
		# Если пользователь определён.
		if UserID in self.__Users["users"].keys() and Admin == False:
			# Запись статуса администратора, подписки и активности.
			Bufer["admin"] = self.__Users["users"][UserID]["admin"]
			
		# Перезапись данных пользователя.
		self.__Users["users"][UserID] = Bufer	
		# Сохранение базы данных.
		WriteJSON("Data/Users.json", self.__Users)
		
		return Bufer["admin"]
			
	# Отправляет сообщение рассылки.
	def sendMessage(self, ChatID: int):
		# Список файлов.
		Files = os.listdir("Attachments")[:10]
		
		# Если есть вложения.
		if len(Files) > 0:
			# Список медиа вложений.
			Attachments = list()
			
			# Для каждого файла.
			for Index in range(0, len(Files)):
				
				# Дополнить вложения файлом.
				Attachments.append(
					types.InputMediaPhoto(
						open("Attachments/" + Files[Index], "rb"), 
						caption = self.__Settings["message"] if Index == 0 else "",
						parse_mode = "HTML"
					)
				)
				
			try:
				# Отправка медиа группы: приветствие нового подписчика.
				self.__Bot.send_media_group(
					ChatID,
					media = Attachments
				)
				
			except Exception as ExceptionData:
				# Вывод исключения.
				print(ExceptionData)
			
		else:

			# Если сообщение не пустое.
			if len(self.__Settings["message"]) > 0:
				
				try:
					# Отправка сообщения: приветствие нового подписчика.
					self.__Bot.send_message(
						ChatID,
						text = self.__Settings["message"],
						parse_mode = "HTML",
						disable_web_page_preview = True
					)
					
				except Exception as ExceptionData:
					# Вывод исключения.
					print(ExceptionData)

	# Задаёт тип ожидаемого сообщения.
	def setExpectedType(self, Type: ExpectedMessageTypes):
		self.__ExpectedType = Type