from Source.Core.Accounts import Account

from dublib.Methods.Filesystem import ListDir, ReadJSON, WriteJSON
from dublib.TelebotUtils.Users import UserData
from dublib.Engine.Bus import ExecutionStatus
from typing import Iterable
from time import sleep

import pandas
import random
import os

class Target:
	"""Цель рассылки."""
	
	#==========================================================================================#
	# >>>>> СВОЙСТВА <<<<< #
	#==========================================================================================#

	@property
	def id(self) -> int:
		"""ID цели."""

		return self.__Data["id"]
	
	@property
	def is_active(self) -> bool:
		"""Состояние: активен ли аккаунт цели."""
		
		return self.__Data["active"]
	
	@property
	def is_mailed(self) -> bool:
		"""Состояние: отправлено ли сообщение."""
		
		return self.__Data["mailed"]

	@property
	def is_premium(self) -> bool:
		"""Состояние: имеет ли цель Premium подписку."""
		
		return self.__Data["premium"]
	
	@property
	def phone_number(self) -> str:
		"""Номер телефона цели."""
		
		return self.__Data["phone_number"]
	
	@property
	def username(self) -> str:
		"""Ник цели."""
		
		return self.__TargetName

	#==========================================================================================#
	# >>>>> ПРИВАТНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __ReadData(self) -> dict:
		"""Считывает данные цели."""

		Template = {
			"id": None,
			"phone_number": None,
			"premium": None,
			"mailed": False,
			"active": True
		}

		if not os.path.exists(self.__Directory): os.makedirs(self.__Directory)
		if os.path.exists(self.__Path):
			Data = ReadJSON(self.__Path)

			for Key in Data.keys():
				if Key in Template: Template[Key] = Data[Key]

		return Template

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def __init__(self, target_name: str, user: UserData):
		"""
		Цель рассылки.
			target_name – ник цели;\n
			user – данные пользователя-инициатора.
		"""

		#---> Генерация динамических атрибутов.
		#==========================================================================================#
		self.__TargetName = target_name.lstrip("@")
		self.__User = user

		self.__Directory = f"Data/Targets/{self.__User.id}"
		self.__Path = f"{self.__Directory}/{self.__TargetName}.json"

		self.__Data = self.__ReadData()
		
	def delete(self):
		"""Удаляет данные цели."""

		os.remove(self.__Path)

	def set_phone_number(self, phone_number: int | str | None):
		"""
		Задаёт номер телефона.
			phone_number – номер телефона.
		"""

		if phone_number:
			phone_number = "+" + str(phone_number).lstrip("+")
			self.__Data["phone_number"] = phone_number
			self.save()

	def set_active_status(self, status: bool):
		"""
		Задаёт состояние активности аккаунта.
			status – статус.
		"""

		self.__Data["active"] = status
		self.save()

	def set_sending_status(self, status: bool):
		"""
		Задаёт статус отправки сообщения в текущей рассылке.
			status – статус.
		"""

		self.__Data["sended"] = status
		self.save()

	def save(self):
		"""Сохраняет данные цели."""

		WriteJSON(self.__Path, self.__Data)

class Mailer:
	"""Оператор рассылки."""

	#==========================================================================================#
	# >>>>> ПУБЛИЧНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	def read_targets(self, user: UserData) -> list[Target]:
		"""
		Считывает данные целей.
			user – данные пользователя-инициатора.
		"""

		Targets: list[Target] = list()
		Files = ListDir(f"Data/Targets/{user.id}")
		Files = tuple(filter(lambda File: File.endswith(".json"), Files))

		for File in Files:
			TargetName = File[:-5]
			Targets.append(Target(TargetName, user))

		return Targets

	def start_mailing(self, accounts: Iterable[Account], user: UserData, delay: float | int = 1) -> ExecutionStatus:
		"""
		Запускает рассылку сообщений.
			accounts – множество используемых для рассылки аккаунтов;\n
			user – данные пользователя-инициатора;\n
			delay – интервал между запросами.
		"""

		Status = ExecutionStatus()
		Status.value = 0

		if not user.get_property("message"):
			Status.push_error("Не задано сообщение для рассылки.")
			return Status

		for CurrentTarget in self.read_targets(user):
			if CurrentTarget.is_mailed or not CurrentTarget.is_active: continue

			accounts = tuple(filter(lambda CurrentAccount: CurrentAccount.is_ready_to_work, accounts))

			if not accounts:
				Status.push_error("Не осталось рабочих аккаунтов. Рассылка остановлена.")
				break
			
			CurrentAccount: Account = random.choice(accounts)
			SendingStatus = CurrentAccount.send_message(CurrentTarget.username, user)

			if SendingStatus.code == 0:
				CurrentTarget.set_sending_status(True)
				Status.value += 1

			elif SendingStatus.code == 1:
				CurrentTarget.set_active_status(False)

			SendingStatus.print_messages()
			sleep(delay)

		Status.push_message(f"Рассылка завершена. Сообщений отправлено: {Status.value}.")

		return Status
	
	def parse_targets_from_excel(self, user: UserData):
		"""
		Парсит цели для рассылки из Excel файла.
			user – данные пользователя-инициатора.
		"""
			
		Excel = pandas.read_excel(f"Data/Temp/{user.id}/targets.xlsx")
		Data = pandas.DataFrame(Excel, columns = ["ID", "Username", "Phone number", "Номер телефона:"])
		UsersID = Data["ID"].tolist()
		Usernames = Data["Username"].tolist()
		# Русское название колонки используется для совместимости с Legacy-таблицами.
		Phones = Data["Phone number"].tolist() + Data["Номер телефона:"].tolist()
			
		for Index in range(0, len(Usernames)):
			NoneValues = ("nan", "None", "NaN")
			if str(UsersID[Index]) in NoneValues: UsersID[Index] = None
			if str(Usernames[Index]) in NoneValues: Usernames[Index] = None
			if str(Phones[Index]) in NoneValues: Phones[Index] = None
			else: Phones[Index] = "+" + str(Phones[Index]).lstrip("+")

			if Usernames[Index]:
				TargetBufer = Target(Usernames[Index], user)
				TargetBufer.set_phone_number(Phones[Index])
				TargetBufer.save()