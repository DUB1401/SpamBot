import zmq

# requests-�������� �������� ������.
class ResponseZMQ:
	
	# �����������.
	def __init__(self):
		
		#---> ��������� ������������ �������.
		#==========================================================================================#
		# ��� ������.
		self.status_code = None
		# ����� ������.
		self.text = None

# ������ ����������� ���������.
class TerminalClinet:
	
	# ������������ ���������.
	def __ProcessMessage(self, Message: str) -> ResponseZMQ:
		# ��������� ������.
		Response = ResponseZMQ()
		# ������� ������.
		CodeMessage = Message.split(";")[0]
		TextMessage = Message.replace(CodeMessage + ";msg=", "")
		CodeMessage = int(CodeMessage.replace("code=", ""))
		# ����������� ��������.
		Response.status_code = CodeMessage
		Response.text = TextMessage

		return Response

	# �����������.
	def __init__(self, Settings: dict):
		
		#---> ��������� ������������ �������.
		#==========================================================================================#
		# ���������� ���������.
		self.__Settings = Settings.copy()
		# �����.
		self.__Socket = None
		
		# ������������� ������.
		Context = zmq.Context()
		self.__Socket = Context.socket(zmq.REQ)
		self.__Socket.connect("tcp://localhost:" + str(Settings["port"]))	
		
	# ���������� ��������� � ���������� ������ �������.
	def send(self, String: str) -> ResponseZMQ:
		# �������� ������.
		self.__Socket.send_string(String)
		# ��������� ������.
		Message = self.__Socket.recv().decode()
		# ������� ������.
		Response = self.__ProcessMessage(Message)
		
		return Response