'''
This file has some functions used by the main process
Copyright (C) 2023  Breno Martins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
import datetime
import io
import json

config = json.load(open("config.json", "r"))


# Função que escreve no arquivo de log
def logit(msg):
    open("log", "a").write(msg + "\n")


# Função principal de logging
def logger(tp, sub_id="", ex="", num="", reason="", bprint=False, com_id=""):
    current_time = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S") # Pega a hora atual pra por no log
    msg = ""

    # Altera a string de mensagem do log a depender do tipo de chamada de função
    if tp == 0:
        msg = f"Comentário enviado em {sub_id}"
    elif tp == 1:
        msg = f"Comentário editado em {sub_id}"
    elif tp == 2 or tp == 5:
        msg = f"{ex}"
        if tp == 5:
            print(f"ERRO ({current_time}): {ex}")

        if bprint:
            print(ex)
    elif tp == 3:
        msg = f"Número {num} ({sub_id})"
    elif tp == 4:
        msg = f"{sub_id} foi removido. MOTIVO: {reason}"
    elif tp == 6:
        msg = f"Comentário denunciado: {ex} em {sub_id}/{com_id}"

    msg = f"[{current_time}] "+msg
    if config["info"]["debug"]:
        print(msg)

    logit(msg)


def log_runtime(func, a: float, b: float):
    # Abrir o arquivo da função para armazenar o tempo de runtime
    try:
        funct_file = open(f"./runtime_info/{func.__name__}", "a")
    except FileNotFoundError:
        funct_file = open(f"./runtime_info/{func.__name__}", "w+")

    difference_runtime = b - a
    # O resultado da diferença entre as timestamps em milisegundos ACIMA.

    # colocar o tempo em minutos
    funct_file.write(f"[{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}] Runtime: {(difference_runtime/60)} minutos. \n")


def getfiletext(file: io.TextIOWrapper) -> list:
    '''
    Consegue o texto de um arquivo e retorna cada linha formatada numa lista
    :param file: Classe da função open()
    :return: Lista de strings
    '''

    indx = -1
    text = file.readlines()
    for line in text:
        indx += 1
        text[indx] = line.strip()

    indx = 0
    for line in text:
        text[indx] = line.removesuffix("\n")
        indx = 0

    return text
