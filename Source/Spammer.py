from dublib.Methods import ReadJSON, RemoveFolderContent, WriteJSON
from telethon.sync import TelegramClient

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
			if OnlyActive == True and Account["active"] == True:
				# Записать ID.
				AccountsID.append(Account["id"])
				
			# Если нужно получить только все аккаунты.
			elif OnlyActive == False:
				# Записать ID.
				AccountsID.append(Account["id"])
			
		return AccountsID
	
	# Подготавилвает аккаунт к работе.
	def __InitializeAccount(self, AccountID: int):
		# Удаление старых файлов сессии.
		if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
		# Копирование новых файлов сессии.
		shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session", "SpamBot.session")
		shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session-journal", "SpamBot.session-journal")
		# Получение описания аккаунта.
		AccountData = self.__GetAccountByID(AccountID)
		# Создание клиента и подключение.
		self.__CurrentClient = TelegramClient("SpamBot", AccountData["api-id"], AccountData["api-hash"])
		self.__CurrentClient.connect()
		
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
		shutil.copyfile("SpamBot.session-journal", f"Data/Sessions/{AccountID}/SpamBot.session-journal")
			
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
			# Буфер аккаунта.
			Bufer = {
				"id": ID,
				"phone-number": PhoneNumber,
				"api-id": ApiID,
				"api-hash": ApiHash,
				"active": True
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
	def send(self, Username: str) -> int:
		# Код исполнения.
		ExecutionCode = 0
		
		try:
			# Выбор ID клиента.
			AccountID = random.choice(self.__GetAccountsID(True))
			# Подготовка клиента к работе.
			self.__InitializeAccount(AccountID)
			# Если ник не начинается с @, добавить.
			if Username.startswith("@") == False: Username = "@" + Username
			# Отправка сообщения.
			self.__CurrentClient.send_message(
				entity = Username,
				message = self.__Settings["message"],
				parse_mode = "HTML" 
			)
			# Выгрузка аккаунта.
			self.__UnloadAccount(AccountID)
			
		except IndexError as ExceptionData:
			# Изменение кода исполнения.
			ExecutionCode = 1
		
		except Exception as ExceptionData:
			# Вывод в консоль: исключение.
			print(ExceptionData)
			# Блокировка аккаунта.
			self.setAccountStatus(AccountID, False)		
			
		return ExecutionCode
	
	# Задаёт статус аккаунта.
	def setAccountStatus(self, AccountID: int | None, Status: bool) -> bool:
		# Состояние: успешно ли изменение статуса.
		IsSuccess = False
		
		# Если указано изменить статус всех аккаунтов.
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
					self.__Accounts["accounts"][Index]["active"] = Status
					# Сохранение описаний аккаунтов.
					self.__SaveAccounts()
					
			# Переключение статуса.
			IsSuccess = True
		
		return IsSuccess
	
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