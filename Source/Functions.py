﻿from dublib.Methods import WriteJSON
from telebot import types

import requests
import telebot
import pandas
import os

# Создаёт разметку меню администратора.
def BuildAdminMenu(BotProcessor: any) -> types.ReplyKeyboardMarkup:
	# Статус коллекционирования.
	Collect = "" if BotProcessor.getData()["collect-media"] == False else " (остановить)"
	
	# Меню администратора.
	Menu = types.ReplyKeyboardMarkup(resize_keyboard = True)
	# Генерация кнопок.
	Edit = types.KeyboardButton("✍ Редактировать")
	Add = types.KeyboardButton("🖼️ Медиа" + Collect)
	Preview = types.KeyboardButton("🔍 Предпросмотр")
	Targets = types.KeyboardButton("👥 Список целей")
	# Добавление кнопок в меню.
	Menu.add(Edit, Add, Preview, Targets, row_width = 2)
	
	return Menu

# Преобразует файл Excel в JSON.
def ConvertExcelToJSON() -> bool:
	# Состояние: успешно ли преобразование.
	IsSuccess = False
		
	# Если файл существует.
	if os.path.exists("Data/Targets.xlsx") == True:
		# Словарь целей.
		Targets = {
			"targets": list()	
		}
			
		try:
			# Чтение файла.
			Excel = pandas.read_excel("Data/Targets.xlsx")
			# Получение данных.
			Data = pandas.DataFrame(Excel, columns = ["Username", "User ID"])
			# Список ников.
			Usernames = Data["Username"].tolist()
			# ID пользователей.
			UsersID = Data["User ID"].tolist()
				
			# Для каждого ника.
			for Index in range(0, len(Usernames)):
				# Если ник отсутствует, преобразовать в нужный формат.
				if str(Usernames[Index]) == "nan": Usernames[Index] = None
				# Буфер пользователя.
				Bufer = {
					"id": UsersID[Index],
					"username": Usernames[Index],
					"active": True
				}
				# Запись буфера.
				Targets["targets"].append(Bufer)
					
			# Сохранение файла целей.
			WriteJSON("Data/Targets.json", Targets)
			# Переключение состояния.
			IsSuccess = True
				
		except Exception as ExceptionData:
			# Вывод в консоль: исключение.
			print(ExceptionData)

	return IsSuccess

# Загружает документ.
def DownloadDoc(Token: str, Bot: telebot.TeleBot, FileID: int) -> bool:
	# Состояние: успешна ли загрузка.
	IsSuccess = False
	# Получение сведений о файле.
	FileInfo = Bot.get_file(FileID) 
	# Получение типа файла.
	FileType = FileInfo.file_path.split('.')[-1]
	# Загрузка файла.
	Response = requests.get("https://api.telegram.org/file/bot" + Token + f"/{FileInfo.file_path}")
	
	# Если запрос успешен.
	if Response.status_code == 200:
		
		# Открытие потока записи.
		with open(f"Data/Targets.{FileType}", "wb") as FileWriter:
			# Запись файла.
			FileWriter.write(Response.content)
			# Переключение статуса.
			IsSuccess = True		
		
	return IsSuccess

# Загружает изображение.
def DownloadImage(Token: str, Bot: telebot.TeleBot, FileID: int) -> bool:
	# Состояние: успешна ли загрузка.
	IsSuccess = False
	# Получение сведений о файле.
	FileInfo = Bot.get_file(FileID) 
	# Получение имени файла.
	Filename = FileInfo.file_path.split('/')[-1]
	# Список расширений изображений.
	ImagesTypes = ["jpeg", "jpg", "png", "gif"]
	
	# Если вложение имеет расширение изображения.
	if Filename.split('.')[-1] in ImagesTypes:

		# Загрузка файла.
		Response = requests.get("https://api.telegram.org/file/bot" + Token + f"/{FileInfo.file_path}")
	
		# Если запрос успешен.
		if Response.status_code == 200:
		
			# Открытие потока записи.
			with open(f"Attachments/{Filename}", "wb") as FileWriter:
				# Запись файла.
				FileWriter.write(Response.content)
				# Переключение статуса.
				IsSuccess = True		
		
	return IsSuccess

# Экранирует символы при использовании MarkdownV2 разметки.
def EscapeCharacters(Post: str) -> str:
	# Список экранируемых символов. _ * [ ] ( ) ~ ` > # + - = | { } . !
	CharactersList = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']

	# Экранировать каждый символ из списка.
	for Character in CharactersList:
		Post = Post.replace(Character, "\\" + Character)

	return Post