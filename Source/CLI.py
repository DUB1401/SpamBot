from dublib.Methods import Cls, RemoveRecurringSubstrings
from Source.Spammer import Spammer
from dublib.StyledPrinter import *
from threading import Event
from io import StringIO

import datetime
import sys
import zmq

# Список команд.
HELP_COMMANDS = [
	"cls".ljust(16) + "Clears terminal output.",	
	"disable".ljust(16) + "Prohibits app from using account for mailing.",	
	"enable".ljust(16) + "Allows app to use account for mailing.",	
	"exit".ljust(16) + "Exit app.",	
	"help".ljust(16) + "Types help data.",	
	"list".ljust(16) + "Types list of registered accounts.",
	"reconnect".ljust(16) + "Recconect account to app.",
	"register".ljust(16) + "Register new Telegram account in app.",
	"send".ljust(16) + "Sends message to @username or by user link.",
	"set".ljust(16) + "Sets setting value.",
	"start".ljust(16) + "Starting spam mailing.",
	"unregister".ljust(16) + "Logout and remove account data."
]

# Список аргументов команд.
HELP_ARGUMENTS = {
	"disable": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database or \"*\" for all accounts selection."
	},
	"enable": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database or \"*\" for all accounts selection."
	},
	"help": {
		"COMMAND": "Name of command, in which you need help."
	},
	"reconnect": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database."
	},
	"register": {
		"PHONE_NUMBER*": "Mobile phone number in the international format.",
		"API_ID*": "ID of API for account.",
		"API_HASH*": "Hash of API for account."
	},
	"send": {
		"USERNAME*": "Name or link of Telegram user."
	},
	"set": {
		"KEY*": "Settings key: delay.",
		"VALUE*": "Settings value."
	},
	"unregister": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database."
	}
}

# Обработчик треминальных команд.
class CLI:
	
	#==========================================================================================#
	# >>>>> ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Имплементирует методы ввода.
	def __input(self, Decoration: str) -> str:
		# Буфер чтения.
		Bufer = None
		
		# Если используется сервер.
		if self.__IsServer == True:
			# Отправка запроса на ввод.
			self.__Socket.send_string("code=1;msg=" + Decoration)
			# Ожидание сообщения.
			Bufer = self.__Socket.recv().decode()
		
		else:
			# Стандартное чтение.
			Bufer = input(Decoration)
			
		return Bufer
	
	#==========================================================================================#
	# >>>>> КОНСОЛЬНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Очистка консоли.
	def __cls(self):
		# Очистка консоли.
		Cls()
		# Вывод в консоль: заголовок интерпретатора.
		print(f"SpamBot {self.__Version}\nGitHub: https://github.com/DUB1401/SpamBot\nCopyright © DUB1401. 2022-" + str(datetime.datetime.now().year) + ".")
		
	# Проверяет наличие мута у аккаунта.
	def __check(self, Command: list[str]):
		# Проверка наличия мута у аккаунта.
		self.__Spammer.checkAccountMute(int(Command[1]), Logging = False)

	# Деактивация аккаунта.
	def __disable(self, Command: list[str]):
		# Если указана звёздочка, выбрать все аккаунты, иначе конвертировать ID в целое число.
		Command[1] = None if Command[1] == "*" else int(Command[1])
		# Попытка активации аккаунта.
		Result = self.__Spammer.updateAccount(Command[1], "active", False)
		# Если деактивация не выполнена, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", TextColor = Styles.Color.Red)
	
	# Активация аккаунта.
	def __enable(self, Command: list[str]):
		# Если указана звёздочка, выбрать все аккаунты, иначе конвертировать ID в целое число.
		Command[1] = None if Command[1] == "*" else int(Command[1])
		# Попытка активации аккаунта.
		Result = self.__Spammer.updateAccount(Command[1], "active", True)
		# Если активация не выполнена, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", TextColor = Styles.Color.Red)

	# Вывод помощи.
	def __help(self, Command: list[str]):
		
		# Если не указана конкретная команда.
		if len(Command) == 1:
			# Вывод в консоль: режим доступа к аргументам.
			print("To get help on a specific command use \"help [COMMAND]\".")
		
			# Для каждой строки помощи.
			for Index in range(0, len(HELP_COMMANDS)):
				# Вывод в консоль: строка помощи.
				print(HELP_COMMANDS[Index])
				
		else:
			
			# Если команда имеет описание.
			if Command[1] in HELP_ARGUMENTS.keys():
				
				# Для каждого аргумента команды.
				for Argument in HELP_ARGUMENTS[Command[1]].keys():
					# Вывод в консоль: описание аргумента.
					print(" - ", Argument.ljust(16), HELP_ARGUMENTS[Command[1]][Argument])
				
			else:
				# Вывод в консоль: команда не имеет описания или не существует.
				print("Command haven't description or not found.")

	# Вывод списка аккаунтов.
	def __list(self):
		# Список аккаунтов.
		Accounts = self.__Spammer.accounts
		
		# Если есть аккаунты.
		if len(Accounts) > 0:
			# Вывод в консоль: разделитель.
			print("==============================")
		
		else:
			# Вывод в консоль: нет аккаунтов.
			print("Telegram accounts aren't registered. Use \"register\" to add new account.")

		# Для каждого аккаунта.
		for Account in Accounts:
			# Вывод в консоль: описание.
			print("ID:", Account["id"])
			print("Phone number:", Account["phone-number"])
			print("Mute: ", end = "")
			
			# Если аккаунт имеет мут.
			if Account["mute"] == True: 
				# Вывод статуса мута.
				StyledPrinter("True", TextColor = Styles.Color.Red)
				
			else:
				# Вывод статуса мута.
				StyledPrinter("False", TextColor = Styles.Color.Green)
				
			# Вывод в консоль: есть ли бан.
			print("Ban: ", end = "")
			
			# Если аккаунт имеет мут.
			if Account["ban"] == True: 
				# Вывод статуса мута.
				StyledPrinter("True", TextColor = Styles.Color.Red)
				
			else:
				# Вывод статуса мута.
				StyledPrinter("False", TextColor = Styles.Color.Green)

			# Вывод в консоль: активность аккаунта.
			print("Active: ", end = "")
			
			# Если аккаунт активен.
			if Account["active"] == True: 
				# Вывод статуса.
				StyledPrinter("True", TextColor = Styles.Color.Green)
				
			else:
				# Вывод статуса.
				StyledPrinter("False", TextColor = Styles.Color.Red)
			
			# Вывод в консоль: разделитель.
			print("==============================")
			
	# Переподключение аккаунта.
	def __reconnect(self, Command: list[str]):
		# Данные аккаунта.
		Account = self.__Spammer.getAccountByID(int(Command[1]))
		# Регистрация без кода.
		Result = self.__Spammer.register(Account["phone-number"], Account["api-id"], Account["api-hash"], AccountID = int(Command[1]))
		# Если вход не произведён, произвести с кодом.
		if Result == False: Result = self.__Spammer.register(Account["phone-number"], Account["api-id"], Account["api-hash"], self.__input("Enter security code: "), AccountID = int(Command[1]))

		# Если регистрация успешна.
		if Result == True: 
			# Вывод в консоль: аккаунт успешно добавлен.
			print("Telegram account successfully reconnected to app.")
						
		else:
			# Вывод в консоль: аккаунт успешно добавлен.
			StyledPrinter("[ERROR] Unable to reconnect account.", TextColor = Styles.Color.Red)
			
	# Регистрация аккаунта.
	def __register(self, Command: list[str]):
		# Регистрация без кода.
		Result = self.__Spammer.register(Command[1], Command[2], Command[3])
		# Если вход не произведён, произвести с кодом.
		if Result == False: Result = self.__Spammer.register(Command[1], Command[2], Command[3], self.__input("Enter security code: "))

		# Если регистрация успешна.
		if Result == True: 
			# Вывод в консоль: аккаунт успешно добавлен.
			print("Telegram account successfully registered in the app.")
						
		else:
			# Вывод в консоль: аккаунт успешно добавлен.
			StyledPrinter("[ERROR] Unable to register account.", TextColor = Styles.Color.Red)
			
	# Отправка сообщения.
	def __send(self, Command: list[str]):
		# Попытка отправки сообщения.
		self.__Spammer.send(Command[1].replace("https://t.me/", ""))
		
	# Установка значения настройки.
	def __set(self, Command: list[str]):
		# Результат выполнения.
		Result = None
		
		# Если ключ определён.
		if Command[1] == "password":
			# Установка значения.
			Result = self.__Spammer.set(Command[1], Command[2])

		# Если ключ определён.
		if Command[1] == "delay":
			# Установка значения.
			Result = self.__Spammer.set(Command[1], int(Command[2]))
			
		# Если команда не выполнена.
		if Result in [None, False]: print(f"Unsupported key: \"{Command[1]}\".")

	# Запуск рассылки.
	def __start(self):
		# Запуск рассылки.
		self.__Spammer.startMailing()

	# Удаляет данные аккаунта.
	def __unregister(self, Command: list[str]):
		# Попытка удаления аккаунта.
		Result = self.__Spammer.unregister(int(Command[1]))
		# Если удаление не выполнено, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", TextColor = Styles.Color.Red)
		
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#
			
	# Конструктор.
	def __init__(self, Settings: dict, Version: str, Clear: bool = True, Server: bool = False):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Обработчик спам-рассылки.
		self.__Spammer = Spammer(Settings)
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Версия.
		self.__Version = Version
		# Состояние: используется ли сервер.
		self.__IsServer = Server
		
		# Очистка консоли.
		if Clear == True: self.__cls()
		# Если используется сервер, вывести сообщение.
		if Clear == True and Server == True: print("\nRunning server on tcp://localhost:" + str(self.__Settings["port"]) + "...")
		
	# Обрабатывает команду.
	def processCommand(self, Command: str):
		# Разбиение команды по пробелам.
		Command = Command.split(" ")
		
		try:
			
			# Проверка команды.
			match Command[0]:
				
				# Очистка консоли.
				case "cls": self.__cls()
				
				# Проверяет наличие мута у аккаунта.
				case "check": self.__check(Command)
				
				# Деактивация аккаунта.
				case "disable": self.__disable(Command)
				
				# Активация аккаунта.
				case "enable": self.__enable(Command)
				
				# Выход.
				case "exit": exit(0)
				
				# Вывод помощи.
				case "help": self.__help(Command)
				
				# Список аккаунтов.
				case "list": self.__list()
				
				# Регистрация аккаунта.
				case "register": self.__register(Command)
				
				# Регистрация аккаунта.
				case "reconnect": self.__reconnect(Command)

				# Отправка сообщения.
				case "send": self.__send(Command)
				
				# Установка значения настройки.
				case "set": self.__set(Command)
				
				# Запуск рассылки.
				case "start": self.__start()
				
				# Удаляет данные аккаунта.
				case "unregister": self.__unregister(Command)
				
				# Пустая команда.
				case "": pass

				# Команда не распознана.
				case _: print("Unknown command. Type \"help\" for more information.")

		except Exception as ExceptionData:
			# Описание ошибки.
			ErrorDescription = RemoveRecurringSubstrings("Runtime error: " + str(ExceptionData), " ")
			# Вывод в консоль: ошибка во время выполнения.
			StyledPrinter(ErrorDescription, TextColor = Styles.Color.Red, Newline = False)
			
	# Запускает цикл обработки терминала.
	def runLoop(self):
		# Ввод.
		Input = None
	
		# Постоянно.
		while True:
			# Запрос ввода команды.
			Input = input("> ")
			# Обработка команды.
			self.processCommand(Input)		
			
	# Запускает сервер обработки терминала.
	def runServer(self):
		# Инициализация сокета.
		Context = zmq.Context()
		self.__Socket = Context.socket(zmq.REP)
		self.__Socket.bind("tcp://127.0.0.1:" + str(self.__Settings["port"]))
		
		# Постоянно.
		while True:
				
			try:
				# Буфер консольного вывода.
				Bufer = StringIO()
				# Установка буфера.
				sys.stdout = Bufer
				# Ожидание сообщения.
				RequestData = self.__Socket.recv().decode()
			
				# Если сработало событие.
				if RequestData == "exit":
					# Отправка ответа.
					self.__Socket.send_string("code=-1;msg=exit")
					# Освобождение порта.
					self.__Socket.unbind("tcp://127.0.0.1:" + str(self.__Settings["port"]))
					# Остановка цикла.
					break
			
				# Обработка запроса.
				self.processCommand(RequestData)
				# Отправка ответа.
				self.__Socket.send_string("code=0;msg=" + Bufer.getvalue().strip())
		
			except Exception:
				pass