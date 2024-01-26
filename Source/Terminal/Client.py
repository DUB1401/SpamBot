import zmq

# requests-подобная эмуляция ответа.
class ResponseZMQ:
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Код ответа.
		self.status_code = None
		# Текст ответа.
		self.text = None

# Клиент обработчика терминала.
class TerminalClinet:
	
	# Обрабатывает сообщение.
	def __ProcessMessage(self, Message: str) -> ResponseZMQ:
		# Контейнер ответа.
		Response = ResponseZMQ()
		# Парсинг данных.
		CodeMessage = Message.split(";")[0]
		TextMessage = Message.replace(CodeMessage + ";msg=", "")
		CodeMessage = int(CodeMessage.replace("code=", ""))
		# Простановка значений.
		Response.status_code = CodeMessage
		Response.text = TextMessage

		return Response

	# Конструктор.
	def __init__(self, Settings: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Сокет.
		self.__Socket = None
		
		# Инициализация сокета.
		Context = zmq.Context()
		self.__Socket = Context.socket(zmq.REQ)
		self.__Socket.connect("tcp://localhost:" + str(Settings["port"]))	
		
	# Отправляет сообщение и возвращает статус общения.
	def send(self, String: str) -> ResponseZMQ:
		# Отправка строки.
		self.__Socket.send_string(String)
		# Получение ответа.
		Message = self.__Socket.recv().decode()
		# Парсинг ответа.
		Response = self.__ProcessMessage(Message)
		
		return Response