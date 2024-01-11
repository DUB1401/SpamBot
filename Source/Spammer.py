from dublib.Methods import ReadJSON, RemoveFolderContent, WriteJSON
from dublib.StyledPrinter import StyledPrinter, Styles
from Source.Functions import CompareDates
from telethon.sync import TelegramClient
from time import sleep

import dateparser
import datetime
import telethon
import random
import shutil
import os

# Генератор спама.
class Spammer:
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ ЧТЕНИЯ СВОЙСТВ <<<<< #
	#==========================================================================================#
	
	# Возвращает список аккаунтов.
	@property
	def accounts(self) -> list[dict]:
		return self.__Accounts["accounts"]
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	# Генерирует ID задачи согласно настройкам.
	def __GenerateID(self) -> int:
		# Последний ID.
		LastID = self.__Accounts["last-id"]
		# Новый ID.
		ID = LastID + 1
		
		# Для каждого значения ID до последнего.
		for Index in range(1, LastID + 1):
			
			# Если ID не занят.
			if Index not in self.__GetAccountsID():
				# Присваивание нового ID.
				ID = Index
				# Остановка цикла.
				break
			
		return ID

	# Возвращает описание аккаунта.
	def __GetAccountByID(self, AccountID: int) -> dict | None:
		# Описание аккаунта.
		Description = None
		
		# Для каждого аккаунта.
		for Account in self.__Accounts["accounts"]:
			
			# Если ID совпал.
			if Account["id"] == AccountID:
				# Запись описания.
				Description = Account
				# Прерывание цикла.
				break
		
		return Description

	# Возвращает список ID подключённых аккаунтов.
	def __GetAccountsID(self, OnlyActive: bool = False) -> list[int]:
		# Список ID аккаунтов.
		AccountsID = list()
		
		# Для каждого аккаунта.
		for Account in self.__Accounts["accounts"]: 
			
			# Если нужно получить только активные аккаунты.
			if OnlyActive == True and Account["active"] == True and Account["mute"] == False:
				# Записать ID.
				AccountsID.append(Account["id"])
				
			# Если нужно получить только все аккаунты.
			elif OnlyActive == False:
				# Записать ID.
				AccountsID.append(Account["id"])
		
		return AccountsID
	
	# Возвращает дату из комментария аккаунта.
	def __GetDate(self, AccountID: int) -> datetime.datetime | None:
		# Получение аккаунта.
		Account = self.__GetAccountByID(AccountID)
		# Дата.
		Date = None
		
		# Если комментарий присутствует.
		if Account["comment"] != None:
			# Получение даты.
			Date = dateparser.parse(Account["comment"].split("=")[-1])
			
		return Date
	
	# Подготавилвает аккаунт к работе.
	def __InitializeAccount(self, AccountID: int):
		# Удаление старых файлов сессии.
		if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
		# Копирование новых файлов сессии.
		shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session", "SpamBot.session")
		if os.path.exists(f"Data/Sessions/{AccountID}/SpamBot.session-journal"): shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session-journal", "SpamBot.session-journal")
		# Получение описания аккаунта.
		AccountData = self.__GetAccountByID(AccountID)
		# Создание клиента и подключение.
		self.__CurrentClient = TelegramClient("SpamBot", AccountData["api-id"], AccountData["api-hash"])
		self.__CurrentClient.connect()

	# Сохраняет файл аккаунтов.
	def __SaveAccounts(self):
		# Перезапись максимального ID.
		self.__Accounts["last-id"] = max(self.__GetAccountsID())
		# Запись в файл.
		WriteJSON("Data/Accounts.json", self.__Accounts)
		
	# Сохраняет файлы сессии.
	def __SaveSession(self, AccountID: int):
		
		# Если целевая папка существует.
		if os.path.exists(f"Data/Sessions/{AccountID}"):
			# Удаление содержимого.
			RemoveFolderContent(f"Data/Sessions/{AccountID}")

		else:
			# Создание папки.
			os.mkdir(f"Data/Sessions/{AccountID}")

		# Копирование новой сессии.
		shutil.copyfile("SpamBot.session", f"Data/Sessions/{AccountID}/SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): shutil.copyfile("SpamBot.session-journal", f"Data/Sessions/{AccountID}/SpamBot.session-journal")
		
	# Выгружает текущий аккаунт из работы.
	def __UnloadAccount(self, AccountID: int):
		# Удаление старых файлов сессии.
		self.__SaveSession(AccountID)
		# Отключение и обнуление клиента.
		self.__CurrentClient.disconnect()
		self.__CurrentClient = None
		# Удаление старых файлов сессии.
		if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
			
	# Конструктор.
	def __init__(self, Settings: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Аккаунты.
		self.__Accounts = ReadJSON("Data/Accounts.json")
		# Текущий клиент.
		self.__CurrentClient = None
		# Буфер клиента.
		self.__Client = None
		
	# Проверяет, замучен ли аккаунт.
	def checkAccountMute(self, AccountID: int, Logging: bool = True) -> bool:
		# Результат отправки сообщения.
		Result = None
		# Статус мута.
		MuteStatus = True
		# Дата размута.
		UnmuteComment = self.__GetDate(AccountID)
		
		# Если нет комментария о муте.
		if UnmuteComment == None:
			# Отправка сообщения спам-боту.
			Result = self.send("@SpamBot", AccountID, Text = "/start", Logging = False, Unload = False, Unmute = False)
			
		# Если есть комментарий о муте и дата мута не истекла.
		elif CompareDates(datetime.datetime.utcnow(), UnmuteComment) == False and Logging == False:
			# Преобразование часового пояса.
			UnmuteComment = str(UnmuteComment).replace(":00+00:00", " UTC")
			# Вывод в консоль: на аккаунте мут.
			print(f"Account muted until {UnmuteComment}.")
			
		# Если дата мута исткела.
		elif CompareDates(datetime.datetime.now(), UnmuteComment) == True:
			# Отправка сообщения спам-боту.
			Result = self.send("@SpamBot", AccountID, Text = "/start", Logging = False, Unload = False, Unmute = False)
		
		# Если сообщение успешно отправлно.
		if Result == 0:
			
			# Поиск первого сообщения.
			for Message in self.__CurrentClient.iter_messages("@SpamBot", from_user = "@SpamBot"):
				# Проверка отсутствия мута.
				if Message.text.startswith("Ваш аккаунт свободен"): MuteStatus = False
				if Message.text.startswith("Good news, no limits"): MuteStatus = False
				
				# Если требуется вывести состояние мута в консоль.
				if MuteStatus == True:
					# Удаление начала абзаца.
					Text = Message.text.replace("Your account will be automatically released on ", "")
					Text = Text.replace("Ограничения будут автоматически сняты ", "")
					# Получение последнего абзаца.
					LastParagraph = Text.split("\n\n")[-1]
					# Дата размута.
					UnmuteDate = LastParagraph.split("UTC")[0]
					# Вывод в консоль: на аккаунте мут.
					if Logging == False: print(f"Account muted until {UnmuteDate} UTC.")
					# Обновление статуса аккаунта.
					self.updateAccount(AccountID, "mute", True, Autosave = False)
					self.updateAccount(AccountID, "comment", f"mute={UnmuteDate}UTC")
				
				else:
					# Вывод в консоль: на аккаунте нет мута.
					if Logging == False: print("Account not muted.")
					# Вывод в консоль: аккаунт размучен.
					if Logging == True: print(f"Account {AccountID} unmuted.")
					# Обновление статуса аккаунта.
					self.updateAccount(AccountID, "mute", False, Autosave = False)
					self.updateAccount(AccountID, "comment", None)
					
				# Остановка цикла.
				break
		
		elif Result != None:
			# Вывод в консоль: ошибка проверки мута.
			if Logging == True: StyledPrinter(f"[ERROR] Unable to request mute status from @SpamBot.", TextColor = Styles.Color.Red)
			
		# Выгрузка аккаунта.
		if self.__CurrentClient != None: self.__UnloadAccount(AccountID)
		
		return MuteStatus

	# Регистрирует новый аккаунт.
	def register(self, ApiID: int | str, ApiHash: str, PhoneNumber: str, Code: str | None = None) -> bool:
		# Состояние: авторизован ли пользователь.
		IsAuth = False
		
		# Если клиент не инициализирован.
		if self.__Client == None:
			# Удаление старых файлов сессии.
			if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
			if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
			
			# Создание клиента и подключение.
			self.__Client = TelegramClient("SpamBot", int(ApiID), ApiHash)
			self.__Client.connect()
			
		# Авторизация.
		if Code != None: self.__Client.sign_in(PhoneNumber, Code)
			
		# Если аккаунт не авторизован.
		if self.__Client.is_user_authorized() == False:
			# Отправка кода 2FA.
			self.__Client.send_code_request(PhoneNumber)
				
		else:
			# Переключение состояния.
			IsAuth = True
			# ID аккаунта.
			ID = self.__GenerateID()
			# Структура пользователя.
			UserStruct = self.__Client.get_me()
			# Буфер аккаунта.
			Bufer = {
				"id": ID,
				"phone-number": PhoneNumber,
				"premium": UserStruct.premium,
				"api-id": ApiID,
				"api-hash": ApiHash,
				"mute": False,
				"active": True,
				"comment": None
			}
			# Запись данных аккаунта.
			self.__Accounts["accounts"].append(Bufer)
			# Сохранение сессии и описания аккаунта.
			self.__SaveSession(ID)
			self.__SaveAccounts()
			# Отключение и обнуление клиента.
			self.__Client.disconnect()
			self.__Client = None
				
		return IsAuth
	
	# Отправляет сообщение.
	def send(self, Username: str, AccountID: int | None = None, Text: str | None = None, Logging: bool = True, Unload: bool = True, Unmute: bool = True) -> int:
		# Код исполнения.
		ExecutionCode = -1
		# ID текущего аккаунта.
		CurrentAccountID = None
				
		# Пока код выполнения не в диапазоне.
		while ExecutionCode not in [0, 1]:
			
			# Если включено автоматическое снятие мута.
			if Unmute == True:
			
				# Для каждого аккаунта.
				for CurrentUnmuteAccountID in self.__GetAccountsID():
					# Текущий аккаунт.
					CurrentAccount = self.__GetAccountByID(CurrentUnmuteAccountID)
					# Если аккаунт замучен, проверить актуальность мута.
					if CurrentAccount["mute"] == True: self.checkAccountMute(CurrentUnmuteAccountID) 

			try:
				# Выбор ID клиента.
				CurrentAccountID = random.choice(self.__GetAccountsID(True)) if AccountID == None else AccountID
				# Подготовка клиента к работе.
				self.__InitializeAccount(CurrentAccountID)
				# Если ник не начинается с @, добавить.
				if Username.startswith("@") == False and Username.startswith("+") == False: Username = "@" + Username
				# Отправка сообщения.
				self.__CurrentClient.send_message(
					entity = Username,
					message = self.__Settings["message"] if Text == None else Text,
					parse_mode = "HTML" 
				)
				# Изменение кода исполнения.
				ExecutionCode = 0
				# Вывод в консоль: успешная отправка.
				if Logging: print(f"[INFO] User: {Username}. Mailed.")
				
			except IndexError as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 1
				# Вывод в консоль: не осталось рабочих аккаунтов.
				if Logging: StyledPrinter(f"[ERROR] There are no working accounts left. Stopped.", TextColor = Styles.Color.Red)
			
			except telethon.errors.rpcerrorlist.PeerFloodError:
				# Изменение кода исполнения.
				ExecutionCode = 2
				# Вывод в консоль: неспецифическая ошибка.
				if Logging: StyledPrinter(f"[ERROR] Account {CurrentAccountID} muted.", TextColor = Styles.Color.Red)
				# Проверка мута аккаунта.
				self.updateAccount(CurrentAccountID, "mute", True)
		
			except Exception as ExceptionData:
				# Вывод в консоль: исключение.
				print(ExceptionData)
				# Блокировка аккаунта.
				self.updateAccount(CurrentAccountID, "active", False)
				# Вывод в консоль: неспецифическая ошибка.
				if Logging: StyledPrinter(f"[WARNING] User: {Username}. Unable to send message.", TextColor = Styles.Color.Yellow)
				# Остановка цикла.
				break
			
			# Выгрузка аккаунта.
			if ExecutionCode != 1 and Unload == True: self.__UnloadAccount(CurrentAccountID)
			
		return ExecutionCode
	
	# Запускает рассылку.
	def startMailing(self, Logging: bool = True):
		# Чтение JSON целей.
		Targets = ReadJSON("Data/Targets.json")
		# Список ников пользователей.
		Usernames = list()
		
		# Для каждой цели.
		for Target in Targets["targets"]:
			
			# Если указан ник.
			if Target["active"] == True:
				
				# Если для цели определён ник.
				if Target["username"] != None:
					# Запись ника.
					Usernames.append(Target["username"])
					
				# Если для цели определён номер телефона.
				elif Target["phone-number"] != None:
					# Запись номера телефона.
					Usernames.append(Target["username"])
				
		# Для каждого ника.
		for User in Usernames:
			# Попытка отправки сообщения.
			self.send(User, Logging)
			# Выжидание интервала.
			sleep(self.__Settings["delay"])
	
	# Удаляет данные аккаунта.
	def unregister(self, AccountID: int) -> bool:
		# Состояние: успешно ли удаление.
		IsRemoved = False
		# Список ID аккаунтов.
		AccountsID = self.__GetAccountsID()
		
		try:
			# Определение порядкового индекса аккаунта в списке.
			Index = AccountsID.index(AccountID)
			# Удаление данных аккаунта.
			self.__Accounts["accounts"].pop(Index)
			
			# Если папка сессии для аккаунта существует.
			if os.path.exists(f"Data/Sessions/{AccountID}"):
				# Удаление данных сессии.
				RemoveFolderContent(f"Data/Sessions/{AccountID}")
				os.rmdir(f"Data/Sessions/{AccountID}")
				
			# Сохранение описания аккаунтов.
			self.__SaveAccounts()
			# Переключение состояния.
			IsRemoved = True
			
		except:
			pass
		
		return IsRemoved
	
	# Обновляет значение поля аккаунта.
	def updateAccount(self, AccountID: int | None, Key: str, Value: any, Autosave: bool = True) -> bool:
		# Состояние: успешно ли изменение статуса.
		IsSuccess = False
		
		# Если указано изменить описание всех аккаунтов.
		if AccountID == None:
			# Получение ID всех аккаунтов.
			AccountID = self.__GetAccountsID()
			
		else:
			# Конвертирование ID в список.
			AccountID = [AccountID]
		
		# Для каждого выбранного аккаунта.
		for CurrentAccount in AccountID:
		
			# Для каждого аккаунта в списке.
			for Index in range(0, len(self.__Accounts["accounts"])):
			
				# Если свопал ID.
				if self.__Accounts["accounts"][Index]["id"] == CurrentAccount:
					# Активация аккаунта.
					self.__Accounts["accounts"][Index][Key] = Value
					# Сохранение описаний аккаунтов.
					if Autosave == True: self.__SaveAccounts()
					
			# Переключение статуса.
			IsSuccess = True
		
		return IsSuccess