from telethon.errors import AuthKeyUnregisteredError, FloodWaitError, PeerFloodError, PhoneNumberBannedError, SessionRevokedError, UserDeactivatedBanError, UserNotParticipantError, RPCError
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from dublib.Methods.Filesystem import ReadJSON, WriteJSON
from dublib.TelebotUtils.Users import UserData
from dublib.Engine.Bus import ExecutionStatus
from telethon.sync import TelegramClient
from telebot import types

import shutil
import os

class Account:
	"""Аккаунт Telegram."""
	
	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def api_id(self) -> int:
		"""ID API аккаунта."""

		return self.__Data["api_id"]
	
	@property
	def api_hash(self) -> int:
		"""Хэш API аккаунта."""
		
		return self.__Data["api_hash"]

	@property
	def comment(self) -> str | None:
		"""Комментарий."""
		
		return self.__Data["comment"]

	@property
	def id(self) -> int:
		"""ID аккаунта."""

		return self.__ID

	@property
	def is_banned(self) -> bool:
		"""Состояние: заблокирован ли аккаунт."""
		
		return self.__Data["banned"]
	
	@property
	def is_enabled(self) -> bool:
		"""Состояние: разрешено ли использование аккаунта."""
		
		return self.__Data["enabled"]
	
	@property
	def is_muted(self) -> bool:
		"""Состояние: запрещено ли аккаунту отправлять сообщения."""
		
		return self.__Data["muted"]

	@property
	def is_premium(self) -> bool:
		"""Состояние: имеет ли аккаунт Premium подписку."""
		
		return self.__Data["premium"]

	@property
	def owner(self) -> int:
		"""ID владельца аккаунта."""

		return self.__Data["owner"]

	@property
	def phone_number(self) -> str:
		"""Номер телефона аккаунта."""
		
		return self.__Data["phone_number"]
	
	@property
	def sended_messages_count(self) -> int:
		"""Количество отправленных с этого аккаунта сообщений с момента регистрации в системе."""

		return self.__Data["sended"]
	
	@property
	def shared(self) -> tuple[int]:
		"""Последовательность ID пользователей, которым разрешена работа с аккаунтом."""

		return tuple(self.__Data["shared"])

	#==========================================================================================#
	# >>>>> ДОПОЛНИТЕЛЬНЫЕ СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def client(self) -> TelegramClient | None:
		"""Клиент Telethon."""
		
		return self.__Client

	@property
	def has_session(self) -> bool:
		"""Состояние: задана ли активная сессия для аккаунта."""
		
		return os.path.exists(f"{self.__Path}/telethon.session")

	@property
	def is_ready_to_work(self) -> bool:
		"""Состояние: готов ли аккаунт к работе."""
		
		return not self.__Data["banned"] and not self.__Data["muted"] and self.__Data["enabled"]

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __ReadAttachments(self, user: UserData) -> tuple[bytes] | None:
		"""
		Считывает бинарно вложения.
			user – данные пользователя-инициатора.
		"""

		Attachments = user.get_property("attachments")
		BinaryFiles = list()

		for File in Attachments:
			Path = f"Data/Temp/{user.id}/Attachments/" + File["filename"]
			BinaryFiles.append(open(Path, "rb"))

		return tuple(BinaryFiles) if BinaryFiles else None

	def __ReadData(self) -> dict:
		"""Считывает данные аккаунта или создаёт новый файл JSON."""

		Data = {
			"owner": None,
			"shared_with": [],
			"phone_number": None,
			"premium": False,
			"api_id": None,
			"api_hash": None,
			"sended": 0,
			"muted": False,
			"banned": False,
			"enabled": True,
			"comment": None
		}
		PathJSON = f"{self.__Path}/data.json"

		if not os.path.exists(PathJSON):
			if not os.path.exists(self.__Path): os.makedirs(self.__Path)
			WriteJSON(PathJSON, Data)
			return Data
		
		else: return ReadJSON(PathJSON)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, id: int):
		"""
		Аккаунт Telegram.
			id – идентификатор аккаунта.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__ID = id

		self.__Path = f"Data/Sessions/{id}"
		self.__Data = self.__ReadData()

		self.__Client: TelegramClient = None

	def change_id(self, new_id: int):
		"""
		Изменяет ID аккаунта в системе.
			new_id – новый ID.
		"""

		self.close_session()
		self.__ID = new_id
		NewPath = f"Data/Sessions/{new_id}"
		os.rename(self.__Path, NewPath)
		self.__Path = NewPath

	def check_access(self, user_id: int):
		"""
		Проверяет, доступен ли данный аккаунт пользователю.
			user_id – ID пользователя.
		"""

		return user_id == self.__Data["owner"] or user_id in self.__Data["shared_with"]

	def close_session(self):
		"""Закрывает сессию."""

		if self.__Client: self.__Client.disconnect()
		self.__Client = None

	def delete(self):
		"""Удаляет данные аккаунта."""

		self.close_session()
		shutil.rmtree(self.__Path)

	def deny(self, user_id: int):
		"""
		Запрещает использование аккаунта другому пользователю.
			user_id – ID пользователя.
		"""

		if user_id in self.__Data["shared_with"]: 
			self.__Data["shared_with"].remove(user_id)
			self.save()

	def enable(self, status: bool):
		"""
		Задаёт разрешение для использования аккаунта.
			status – статус разрешения.
		"""

		self.__Data["enabled"] = status
		self.save()

	def get_data(self) -> dict:
		"""Возвращает копию словаря данных аккаунта."""

		return self.__Data.copy()

	def register(self, phone_number: str, api_id: int, api_hash: str) -> bool:
		"""
		Регистрирует сессию аккаунта.
			phone_number – номер телефона;\n
			api_id – ID API аккаунта;\n
			api_hash – хэш API аккаунта.
		"""

		self.__Data["api_id"] = api_id
		self.__Data["api_hash"] = api_hash
		self.__Data["phone_number"] = phone_number
		self.save()
		self.start_session()

		if not self.__Client.is_user_authorized():
			self.__Client.send_code_request(phone_number)
			self.__Client.sign_in(phone_number, input("Введите код безопасности:" + " "))

		IsRegistered = self.__Client.is_user_authorized()
		self.close_session()

		return IsRegistered
	
	def save(self):
		"""Сохраняет данные аккаунта."""

		WriteJSON(f"{self.__Path}/data.json", self.__Data)
	
	def set_owner(self, owner: int):
		"""
		Задаёт владельца аккаунта.
			owner – ID владельца.
		"""

		self.__Data["owner"] = owner
		self.save()

	def share(self, user_id: int):
		"""
		Разрешает использование аккаунта другому пользователю.
			user_id – ID пользователя.
		"""

		if user_id not in self.__Data["shared_with"]: 
			self.__Data["shared_with"].append(user_id)
			self.save()

	def start_session(self):
		"""Запускает сессию."""

		try:
			self.__Client = TelegramClient(f"{self.__Path}/telethon.session", self.api_id, self.api_hash, system_version = "4.16.30-vxCUSTOM")
			self.__Client.connect()

		except: pass

	#==========================================================================================#
	# >>>>> МЕТОДЫ ОБРАЩЕНИЯ К TELEGRAM <<<<< #
	#==========================================================================================#

	def check_mute(self) -> ExecutionStatus:
		"""Проверяет, может ли аккаунт писать сообщения неконтактам."""

		Status = ExecutionStatus()
		Status.set_value(True)

		try:
			self.__Client.send_message("@SpamBot", "/start")
			Message: types.Message

			for Message in self.__Client.iter_messages("@SpamBot", from_user = "@SpamBot"):
				if Message.text.startswith("Ваш аккаунт свободен") or Message.text.startswith("Good news, no limits"): Status.set_value(False)

			if Status.value != self.is_muted:
				self.__Data["muted"] = Status.value
				self.save()

		except: Status.push_error(f"Не удалось проверить наличие мута на аккаунте #{self.__ID}.")

		return Status

	def join_chat(self, chat: int | str) -> ExecutionStatus:
		"""
		Отправляет запрос на вступление в чат.
			chat – идентификатор чата или его ID.
		"""

		Status = ExecutionStatus()

		try:
			self.start_session()
			self.__Client(JoinChannelRequest(chat))
			self.close_session()
			Status.value = True
			Status.push_message(f"Аккаунт #{self.__ID} отправил запрос на вступление в чат.")

		except: Status.push_error("Не удалось отправить запрос на вступление в чат.")

		return Status

	def leave_chat(self, chat: int | str) -> ExecutionStatus:
		"""
		Покидает чат.
			chat – идентификатор чата или его ID.
		"""

		Status = ExecutionStatus()
		Status.set_value(False)

		try:
			self.start_session()
			self.__Client(LeaveChannelRequest(chat))
			self.close_session()
			Status.value = True
			Status.push_message(f"Аккаунт #{self.__ID} отправил запрос на выход из чата.")

		except UserNotParticipantError: Status.push_message(f"Аккаунт #{self.__ID} не состоит в чате.")
		except: Status.push_error("Не удалось отправить запрос на выход из чата.")

		return Status

	def send_message(self, target: str, user: UserData) -> ExecutionStatus:
		"""
		Отправляет сообщение.
			target – ник пользователя, бота или идентификатор чата;\n
			user – данные пользователя, запускающего отправку.
		"""

		Status = ExecutionStatus()
		Status.set_value(False)
		target = target.lstrip("@")

		try:
			self.start_session()
			self.__Client.send_message(
				entity = target,
				message = user.get_property("message"),
				file = self.__ReadAttachments(user),
				parse_mode = "HTML"
			)
			self.close_session()

			self.__Data["sended"] += 1
			self.save()
			Status.push_message(f"Сообщение от аккаунта #{self.__ID} отправлено: {target}.")
			Status.set_code(0)
			Status.set_value(True)

		except RPCError:
			Status.set_code(1)
			Status.push_message(f"Пользователь {target} запретил себе писать. Пропущен.")

		except (AuthKeyUnregisteredError, SessionRevokedError):
			self.__Data["enabled"] = False
			self.save()
			Status.push_warning(f"Аккаунт #{self.__ID} требует авторизации. Отключён.")
			Status.set_code(2)

		except (FloodWaitError, PeerFloodError):
			self.__Data["muted"] = True
			self.save()
			Status.push_error(f"Аккаунт #{self.__ID} замучен.")
			Status.set_code(3)

		except (PhoneNumberBannedError, UserDeactivatedBanError):
			self.__Data["banned"] = True
			self.save()
			Status.push_error(f"Аккаунт #{self.__ID} забанен.")
			Status.set_code(4)

		except Exception as ExceptionData:
			Status.push_error(f"Неизвестная ошибка при отправке сообщения: {ExceptionData}")
			Status.set_code(-1)

		return Status

class Manager:
	"""Менеджер аккаунтов."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def accounts(self) -> tuple[Account]:
		"""Кортеж аккаунтов."""

		return tuple(self.__Accounts.values())
	
	@property
	def accounts_id(self) -> tuple[int]:
		"""Кортеж ID аккаунтов."""

		return tuple(self.__Accounts.keys())

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __GenerateID(self) -> int:
			"""Генерирует новый ID сессии."""

			AccountsID = tuple(self.__Accounts.keys())
			NewID = 1
			
			if AccountsID:
				
				for Index in range(1, max(AccountsID) + 2):
					
					if Index not in AccountsID:
						NewID = Index
						break
			
			return NewID

	def __LoadAccountsData(self):
		"""Загружает данные аккаунтов."""

		for ID in os.listdir("Data/Sessions"):
			ID = int(ID)
			self.__Accounts[ID] = Account(ID)

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, user: UserData):
		"""
		Модуль управления рассылкой.
			user – данные пользователя.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__User: UserData = user

		self.__Accounts: dict[int, Account] = dict()

		self.__LoadAccountsData()

	def delete_account(self, account_id: int) -> ExecutionStatus:
		"""
		Удаляет аккаунт из системы.
			account_id – ID аккаунта.
		"""

		Status = ExecutionStatus()

		if self.__User.id == self.__Accounts[account_id].owner:
			self.__Accounts[account_id].delete()
			del self.__Accounts[account_id]
			Status.value = True

		else:
			Status.push_error(f"Недостаточно прав для удаления аккаунта #{account_id}.")
			Status.value = False

		return Status

	def get_account(self, account_id: int) -> Account | None:
		"""
		Возвращает аккаунт.
			account_id – ID аккаунта.
		"""
		
		return self.__Accounts[account_id]
	
	def get_user_accounts(self, user_id: int) -> tuple[Account]:
		"""
		Возвращает последовательность аккаунтов, к которым у пользователя есть доступ.
			user_id – ID пользователя.
		"""
		
		return tuple(filter(lambda CurrentAccount: CurrentAccount.check_access(user_id), self.__Accounts.values()))

	def register(self, phone_number: str, api_id: int, api_hash: str, owner: int) -> ExecutionStatus:
		"""
		Регистрирует новый аккаунт в системе SpamBot.
			phone_number – номер телефона;\n
			api_id – ID API аккаунта;\n
			api_hash – хэш API аккаунта;\n
			owner – ID владельца.
		"""

		Status = ExecutionStatus()

		if not phone_number.startswith("+"): phone_number = "+" + phone_number

		if phone_number in [CurrentAccount.phone_number for CurrentAccount in self.__Accounts.values()]:
			Status.push_warning("Аккаунт с таким номером телефона уже существует в системе.")
			return Status

		NewID = self.__GenerateID()
		self.__Accounts[NewID] = Account(NewID)
		
		if self.__Accounts[NewID].register(phone_number, api_id, api_hash):
			self.__Accounts[NewID].set_owner(owner)
			Status.value = NewID
		
		return Status