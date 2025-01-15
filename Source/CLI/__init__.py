from Source.Core.Accounts import Account, Manager
from Source.Core.Mailing import Mailer

from dublib.Exceptions.CLI import InvalidParameterType, NotEnoughParameters, TooManyParameters
from dublib.CLI.Terminalyzer import Command, ParametersTypes, ParsedCommandData, Terminalyzer
from dublib.CLI.TextStyler import Colors, Decorations, TextStyler
from dublib.TelebotUtils.Users import UserData, UsersManager
from dublib.Methods.Filesystem import WriteJSON
from dublib.Engine.Bus import ExecutionStatus
from dublib.Methods.System import Clear
from dublib.CLI import readline

from typing import Iterable
from time import sleep

import random
import shlex

class Interaction:
	"""Оболочка взаимодействия с пользователем посредством CLI."""

	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def accounts_commands(self) -> list[Command]:
		"""Список команд, применяемых к аккаунтам."""

		CommandsList = list()

		Com = Command("chid", "Задаёт новый ID для аккаунта.")
		ComPos = Com.create_position("NEW_ID", "Новый ID аккаунта.")
		ComPos.add_argument(ParametersTypes.Number)
		CommandsList.append(Com)

		Com = Command("delete", "Удаляет аккаунт из системы.")
		CommandsList.append(Com)

		Com = Command("deny", "Отзывает доступ к аккаунту у другого пользователя.")
		ComPos = Com.create_position("USER", "Идентиифкатор пользователя.")
		ComPos.add_argument(ParametersTypes.Number, "ID пользователя.")
		CommandsList.append(Com)

		Com = Command("disable", "Помечает аккаунт как запрещённый к использованию.")
		CommandsList.append(Com)

		Com = Command("enable", "Помечает аккаунт как разрешённый к использованию.")
		CommandsList.append(Com)

		Com = Command("join", "Отправляет запрос на вступление в чат.")
		ComPos = Com.create_position("CHAT", "Идентификатор чата.", important = True)
		ComPos.add_argument()
		CommandsList.append(Com)

		Com = Command("leave", "Выходит из чата.")
		ComPos = Com.create_position("CHAT", "Идентификатор чата.", important = True)
		ComPos.add_argument()
		CommandsList.append(Com)

		Com = Command("mail", "Использует выбранные аккаунты для рассылки сообщений.")
		CommandsList.append(Com)

		Com = Command("reconnect", "Выполняет переподключение аккаунта к системе.")
		CommandsList.append(Com)

		Com = Command("send", "Отправляет сообщение указанной цели.")
		ComPos = Com.create_position("TERGET", "Цель для отправки сообщения.")
		ComPos.add_argument(description = "Номер телефона или ник пользователя.")
		CommandsList.append(Com)

		Com = Command("share", "Делится аккаунтом с другим пользователем системы.")
		ComPos = Com.create_position("USER", "Идентиифкатор пользователя.")
		ComPos.add_argument(ParametersTypes.Number, "ID пользователя.")
		CommandsList.append(Com)
		
		return CommandsList

	@property
	def commands(self) -> list[Command]:
		"""Список всех команд оболочки."""

		CommandsList = list()

		Com = Command("clear", "Очистить консоль.")
		CommandsList.append(Com)

		Com = Command("delay", "Задаёт интервал в секундах между последовательными запросами.")
		ComPos = Com.create_position("SECONDS", "Длительность интервала.")
		ComPos.add_argument(ParametersTypes.All, "Целое или дробное положительное число.")
		ComPos.add_flag("p", "Выводит текущее значение.")
		CommandsList.append(Com)

		Com = Command("drop", "Сбрасывает выбранные аккаунты.")
		CommandsList.append(Com)

		Com = Command("exit", "Закрыть программу.")
		CommandsList.append(Com)

		Com = Command("list", "Выводит список аккаунтов.")
		ComPos = Com.create_position("SELECTOR", "Способ выборки.")
		ComPos.add_flag("a", "Только те, к которым вы имеете доступ.")
		ComPos.add_flag("e", "Только включённые.")
		ComPos.add_flag("b", "Только забаненные.")
		ComPos.add_flag("m", "Только имеющие мут.")
		ComPos.add_flag("d", "Только отключённые.")
		ComPos.add_flag("w", "Только готовые к работе.")
		CommandsList.append(Com)

		Com = Command("register", "Добавляет аккаунт в систему.")
		ComPos = Com.create_position("PHONE_NUMBER", "Номер телефона.")
		ComPos.add_argument(description = "Номер телефона.")
		ComPos = Com.create_position("API_ID", "ID API.")
		ComPos.add_argument(ParametersTypes.Number, "ID API.")
		ComPos = Com.create_position("API_HASH", "Хэш API.")
		ComPos.add_argument(description = "Хэш API.")
		CommandsList.append(Com)

		Com = Command("select", "Выбирает аккаунты для использования.")
		ComPos = Com.create_position("RANGE", "Диапазон выборки.")
		ComPos.add_argument(description = "Диапазон ID аккаунтов в формате \"1,4-7,9\". Для случайной выборки \"%5\", для выбора всех \"*\".")
		ComPos = Com.create_position("FILTERS", "Фильтры аккаунтов.")
		ComPos.add_flag("a", "Только те, к которым вы имеете доступ.")
		ComPos.add_flag("e", "Только включённые.")
		ComPos.add_flag("b", "Только забаненные.")
		ComPos.add_flag("m", "Только имеющие мут.")
		ComPos.add_flag("d", "Только отключённые.")
		ComPos.add_flag("w", "Только готовые к работе.")
		CommandsList.append(Com)

		return CommandsList + self.accounts_commands

	#==========================================================================================#
	# >>>>> ОБРАБОТЧИКИ ИНСТРУКЦИЙ ДЛЯ АККАУНТОВ <<<<< #
	#==========================================================================================#

	def __chid(self, command: Command, account: Account):
		Status = ExecutionStatus()
		NewID = command.arguments[0]

		if NewID not in [AccountData.id for AccountData in self.__Manager.accounts]: account.change_id(NewID)
		else: Status.push_error("Аккаунт с таким ID уже существует.")

		Status.print_messages()

	def __reconnect(self, command: Command, account: Account):
		Status = ExecutionStatus()
		Status.value = account.register(account.phone_number, account.api_id, account.api_hash)
		if Status.value: Status.push_message(f"Аккаунт #{account.id} успешно переподключен к системе.")
		else: Status.push_error(f"Не удалось переподключить аккаунт #{account.id} к системе.")
		Status.print_messages()

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#
			
	def __CheckAccountsSelected(self, single: bool = False) -> ExecutionStatus:
		"""
		Проверяет, выбраны ли аккаунты для работы.
			single – указывает, что требуется выбрать только один аккаунт.
		"""

		Status = ExecutionStatus()

		Status.set_value(len(self.__SelectedAccounts) == 1 if single else bool(self.__SelectedAccounts))

		if single and len(self.__SelectedAccounts) > 1: Status.push_error("Для этой операции можно выбрать только один аккаунт.")
		elif not len(self.__SelectedAccounts): Status.push_error("Не выбран ни один аккаунт.")

		return Status

	def __CheckUser(self, user_id: int | str) -> ExecutionStatus:
		"""
		Проверяет, есть ли пользователь в системе и не передан ли ID текущего пользователя.
			user_id – ID пользователя.
		"""

		user_id = int(user_id)
		Status = ExecutionStatus()
		
		try:
			if user_id == self.__User.id: raise ValueError
			self.__UsersManager.get_user(user_id)
			Status.set_value(True)

		except KeyError:
			Status.push_error(f"Пользователь {user_id} не найден в системе.")
			Status.set_value(False)

		except ValueError:
			Status.push_error("Вы являетесь владельцем аккаунта.")
			Status.set_value(False)
		
		return Status

	def __GenerateSelector(self) -> str:
		"""Генерирует селектор CLI."""

		Selected = ""
		if len(self.__SelectedAccounts) == 1: Selected = "#" + str(self.__SelectedAccounts[0].id) + " "
		elif len(self.__SelectedAccounts): Selected = "~" + str(len(self.__SelectedAccounts)) + " "
		Selector = f"spambot {Selected}> "

		return Selector

	def __FilterAccounts(self, command: ParsedCommandData, accounts: Iterable[Account]) -> tuple[Account]:
		"""
		Фильтрует аккаунты.
			command – команда с флагами фильтрации;\n
			accounts – последовательность аккаунтов.
		"""

		if command.check_flag("e"): accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.is_enabled, accounts))
		if command.check_flag("b"): accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.is_banned, accounts))
		if command.check_flag("m"): accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.is_muted, accounts))
		if command.check_flag("d"): accounts = tuple(filter(lambda CurrentAccount: not CurrentAccount.is_enabled, accounts))
		if command.check_flag("w"): accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.is_ready_to_work, accounts))
		if command.check_flag("a"): accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.check_access(self.__User.id), accounts))

		return accounts

	def __SelectRange(self, range_string: str):
		"""
		Выбирает аккаунты в определённом диапазоне.
			range_string – строка выборки.
		"""

		Ranges = range_string.split(",")
		ResultRange = list()

		UserAccounts = self.__Manager.get_user_accounts(self.__User.id)
		UserAccountsID = [CurrentAccount.id for CurrentAccount in UserAccounts]

		for Range in Ranges:

			if Range == "*":
				ResultRange = UserAccountsID

			elif "-" in Range:
				Start, End = map(int, Range.split("-"))
				ResultRange.extend(range(Start, End + 1))

			elif "%" in Range:
				Count = int(Range.lstrip("%"))
				RandomAccounts = random.choices(UserAccounts, k = Count)

				for CurrentAccount in RandomAccounts:
					if CurrentAccount.id not in ResultRange: ResultRange.append(CurrentAccount.id)

			elif Range.isdigit():
				ResultRange.append(int(Range))

		SelectedAccounts = list()

		for ID in ResultRange:
			if ID in UserAccountsID: SelectedAccounts.append(self.__Manager.get_account(ID))

		return tuple(SelectedAccounts)

	def __ProcessAccountsCommand(self, command: ParsedCommandData):
		"""
		Проводит обработку команды, работающей с аккаунтами.
			command – команда.
		"""

		Status = ExecutionStatus()

		if command.name == "chid":
			SelectionStatus = self.__CheckAccountsSelected(single = True)

			if SelectionStatus.value:
				self.__chid(command, self.__SelectedAccounts[0])
				self.__SelectedAccounts = tuple()
				Status.push_warning("Выбранные аккаунты сброшены.")

		elif command.name == "delete":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				DeletedAccountsCount = 0

				for CurrentAccount in self.__SelectedAccounts:
					DeletingStatus = self.__Manager.delete_account(CurrentAccount.id)
					if DeletingStatus: DeletedAccountsCount += 1
					else: DeletingStatus.print_messages()

				Status.push_message("Удалено аккаунтов:" + f" {DeletedAccountsCount}.")
				
				if DeletingStatus: 
					self.__SelectedAccounts = tuple()
					Status.push_warning("Выбранные аккаунты сброшены.")

		elif command.name == "deny":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				for CurrentAccount in self.__SelectedAccounts:
					UserID = command.arguments[0]
					CheckingStatus = self.__CheckUser(UserID)
					
					if CheckingStatus: CurrentAccount.deny(UserID)
					else: CheckingStatus.print_messages()

		elif command.name == "disable":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value: 
				for CurrentAccount in self.__SelectedAccounts: CurrentAccount.enable(False)

		elif command.name == "enable":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value: 
				for CurrentAccount in self.__SelectedAccounts: CurrentAccount.enable(True)

		elif command.name == "join":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:

				for CurrentAccount in self.__SelectedAccounts:
					CurrentAccount.join_chat(command.arguments[0]).print_messages()
					sleep(self.__Settings["delay"])

		elif command.name == "leave":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				for CurrentAccount in self.__SelectedAccounts:
					CurrentAccount.leave_chat(command.arguments[0]).print_messages()
					sleep(self.__Settings["delay"])

		elif command.name == "mail":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				MailerObject = Mailer()
				MailingStatus = MailerObject.start_mailing(self.__SelectedAccounts, self.__User, delay = self.__Settings["delay"])
				Status.merge(MailingStatus)

		elif command.name == "reconnect":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value: 
				for CurrentAccount in self.__SelectedAccounts: self.__reconnect(command, CurrentAccount)

		elif command.name == "share":
			SelectionStatus = self.__CheckAccountsSelected()
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				for CurrentAccount in self.__SelectedAccounts:
					UserID = command.arguments[0]
					CheckingStatus = self.__CheckUser(UserID)
					
					if CheckingStatus: CurrentAccount.share(UserID)
					else: CheckingStatus.print_messages()

		elif command.name == "send":
			SelectionStatus = self.__CheckAccountsSelected(single = True)
			Status.merge(SelectionStatus)

			if SelectionStatus.value:
				SendingStatus = self.__SelectedAccounts[0].send_message(command.arguments[0], self.__User)
				Status.merge(SendingStatus)

		Status.print_messages()

	def __ProcessCommand(self, command: ParsedCommandData):
		"""
		Проводит обработку команды.
			command – команда.
		"""

		Status = ExecutionStatus()

		if command.name in [CommandData.name for CommandData in self.accounts_commands]:
			self.__ProcessAccountsCommand(command)

		elif command.name == "clear":
			Clear()

		elif command.name == "delay":

			if command.check_flag("p"):
				print("Текущий интервал:", self.__Settings["delay"])

			else:
				try: self.__Settings["delay"] = float(command.arguments[0])
				except ValueError: Status.push_error("Некорректное значение интервала.")
				WriteJSON("Settings.json", self.__Settings)

		elif command.name == "drop":
			self.__SelectedAccounts = tuple()

		elif command.name == "exit": 
			exit(0)

		elif command.name == "list":
			Accounts = self.__Manager.accounts

			if not Accounts:
				RegisterBold = TextStyler("register").decorate.bold
				Status.push_message(f"В системе нет аккаунтов. Используйте {RegisterBold}, чтобы добавить новый.")
				Status.print_messages()
				return

			Accounts = self.__FilterAccounts(command, Accounts)

			if not Accounts:
				Status.push_message("По вашему запросу не найден ни один аккаунт.")
				Status.print_messages()
				return
			
			print("==========")

			for Account in Accounts:
				print(TextStyler("ID:").decorate.bold, Account.id)
				print(TextStyler("Phone number:").decorate.bold, Account.phone_number)
				IsPremium = TextStyler("true").colorize.bright_yellow if Account.is_premium else "false"
				print(TextStyler("Premium:").decorate.bold, IsPremium)
				print(TextStyler("Messages sended:").decorate.bold, Account.sended_messages_count)
				self.status("Access", Account.check_access(self.__User.id), end = " | ")
				self.status("Mute", Account.is_muted, reverse = True, end = " | ")
				self.status("Ban", Account.is_banned, reverse = True, end = " | ")
				self.status("Enabled", Account.is_enabled)
				if Account.comment: print(TextStyler("Comment:").decorate.bold, Account.comment)
				print("==========")

		elif command.name == "register":
			RegistrationStatus = self.__Manager.register(command.arguments[0], command.arguments[1], command.arguments[2], self.__User.id)
			if RegistrationStatus.value: Status.push_message(f"Аккаунт добавлен в систему под ID #{RegistrationStatus.value}.")
			elif RegistrationStatus.messages: Status.merge(RegistrationStatus, overwrite = False)
			else: Status.push_error("Не удалось зарегистрировать аккаунт.")

		elif command.name == "select":

			if not self.__Manager.accounts:
				RegisterBold = TextStyler("register").decorate.bold
				Status.push_message(f"В системе нет аккаунтов. Используйте {RegisterBold}, чтобы добавить новый.")
			
			else:
				if command.check_flag("all"): self.__SelectedAccounts = self.__Manager.accounts
				else: self.__SelectedAccounts = self.__SelectRange(command.arguments[0])
		
				for Flag in command.flags:
					if len(Flag) == 1:
						self.__SelectedAccounts = self.__FilterAccounts(command, self.__Manager.accounts)
						break

				Count = len(self.__SelectedAccounts)
				print(f"Выбрано аккаунтов: {Count}.")

		Status.print_messages()

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, settings: dict):
		"""
		Оболочка взаимодействия с пользователем посредством CLI.
			settings – глобальные настройки.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__Settings = settings.copy()

		self.__User: UserData = None
		self.__UsersManager: UsersManager = None
		self.__Manager: Manager = None
		self.__SelectedAccounts: tuple[Account] = tuple()

		self.__Analyzer = Terminalyzer()
		self.__Analyzer.enable_help()

		self.__Analyzer.help_translation.command_description = "Выводит список доступных команд. Для подробностей добавьте название команды в качестве аргумента."
		self.__Analyzer.help_translation.argument_description = "Название команды, для которой вы хотите получить расширенное описание."
		self.__Analyzer.help_translation.important_note = "Обязательные параметры помечены * знаком."

	def auth(self, user_key: int | None = None):
		"""
		Выполняет вход в аккаунт.
			user_key – ID пользователя Telegram для доступа к его данным, полученным через бота.
		"""

		self.__UsersManager = UsersManager("Data/Users")
		
		while not self.__User:

			try:
				UserID = input("Введите код доступа (ID пользователя Telegram):" + " ") if not user_key else user_key
				UserID = int(UserID)
				self.__User = self.__UsersManager.get_user(UserID)
				self.__Manager = Manager(self.__User)
				Username = TextStyler(self.__User.username).decorate.bold
				print("Добро пожаловать," + f" {Username}!\n")

			except KeyboardInterrupt:
				print("exit")
				exit(0)

			except ValueError:
				self.error("Введённые данные не являются числом.")
				user_key = None

			except KeyError:
				self.error("Пользователь с таким ID не найден в системе.")
				user_key = None

	def run(self):
		"""Запускает цикл ввода команд."""

		while True:
			Input = None

			try:
				Input = input(self.__GenerateSelector()).strip()

			except KeyboardInterrupt:
				print("exit")
				exit(0)
			
			if Input:
				self.__Analyzer.set_source(shlex.split(Input))

				try:
					ParsedCommand = self.__Analyzer.check_commands(self.commands)
					if ParsedCommand: self.__ProcessCommand(ParsedCommand)
					elif not Input.startswith("help"): self.error("Неизвестная команда.")

				except NotEnoughParameters: self.error("Недостаточно параметров.")
				except TooManyParameters: self.error("Слишком много параметров.")
				except InvalidParameterType: self.error("Неверный тип переданного параметра.")

	#==========================================================================================#
	# >>>>> ШАБЛОНЫ ВВОДА-ВЫВОДА <<<<< #
	#==========================================================================================#

	def error(self, text: str):
		"""
		Выводит в консоль ошибку.
			text – описание ошибки.
		"""

		print(TextStyler("[ERROR] " + text).colorize.red)

	def status(self, field: str, status: bool, reverse: bool = False, end: str | None = "\n"):
		"""
		Выводит в консоль статус поля.
			field – название поля;\n
			status – логический статус;\n
			reverse – инвертирует окраску;\n
			end – конец строки.
		"""

		if reverse: status = TextStyler("true").colorize.red if status else TextStyler("false").colorize.green
		else: status = TextStyler("true").colorize.green if status else TextStyler("false").colorize.red
		print(TextStyler(field + ":").decorate.bold, status, end = end)

	def title(self):
		"""Выводит заголовок CLI."""

		Clear()
		HelpBold = TextStyler("help").decorate.bold
		ExitBold = TextStyler("exit").decorate.bold
		print(TextStyler("SpamBot").decorate.bold)
		print(f"Если вам нужна помощь, введите команду {HelpBold}.")
		print(f"Для выхода выполните {ExitBold} или нажмите Ctrl + C.")
		print("Проект на GitHub:" + " ", end = "")
		TextStyler("https://github.com/DUB1401/SpamBot", text_color = Colors.Cyan, decorations = Decorations.Italic).print()
		print()