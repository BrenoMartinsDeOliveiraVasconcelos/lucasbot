'''
This file has some functions used by the main process
Copyright (C) 2024  Breno Martins

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
import os
import time
import mysql.connector
import shutil
import re

try:
    config_path = open("./config_path.txt").readlines()[0].replace("\n", "")
except FileNotFoundError:
    try:
        print("Arquivo 'config_path.txt' não encontrado. Será criado o arquivo, por favor edite colocando o caminho do arquivo de configuração.")
        open("./config_path.txt", "w+").write("")
        exit(-1)
    except PermissionError:
        print("Permissão negada ao criar o arquivo.")
        exit(-1)
except PermissionError:
    print("Permissão de leitura ao arquivo config_path.txt negada! Não é possível prosseguir")
    exit(-1)

try:
    config = json.load(open(f'{config_path}/config.json', 'r'))  # Configurações do bot
    reasons = json.load(open(f"{config['config']}/reasons.json", "r"))  # Motivos para punição automatizada
    boot = True
except FileNotFoundError:
    print(f"Arquivos de configuração não encontrados... Eles realmente existem? Criando com base no modelo! Edite os arquivo em {config_path}!")
    models = "./__MODElS__"

    if os.path.exists(models):
        try:
            for file in os.listdir(models):
                shutil.copy(os.path.join(models, file), config_path)
        except PermissionError:
            print("Permissão negada! Abortando.")
            exit(-1)
    else:
        print("Pasta de modelos não encontrada não encontrada! Abortando.")
        exit(-1)
except PermissionError:
    print("Permissão negada ao ler os arquivos de configuração. Não será possível prosseguir.")
    exit(-1)


# Função que escreve no arquivo de log
def logit(msg):
    open(f"{config['list_path']}/log", "a").write(msg + "\n")


# Função principal de logging
def logger(tp, sub_id="", ex="", num="", reason="", bprint=False, com_id=""):
    current_time = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S") # Pega a hora atual pra por no log
    msg = ""

    # Altera a string de mensagem do log a depender do tipo de chamada de função
    if tp == 0:
        msg = f"Comentário enviado em {sub_id}"
    elif tp == 1:
        msg = f"Comentário editado em {sub_id}"
    elif tp == 2 or tp == 5 or tp == 7:
        msg = f"{ex}"
        if tp == 5:
            print(f"ERRO ({current_time}): {ex}")

            time.sleep(1)
        if bprint:
            print(ex)
    elif tp == 3:
        msg = f"Número {num} ({sub_id})"
    elif tp == 4:
        msg = f"{sub_id} foi removido. MOTIVO: {reason}"
    elif tp == 6:
        msg = f"Comentário denunciado: {ex} em {sub_id}/{com_id}"

    msg = f"[{current_time}] "+msg
    if config["debug"]["log_verbose"]:
        print(msg)

    if tp != 7:
        logit(msg)


def log_runtime(func, a: float, b: float):
    # Abrir o arquivo da função para armazenar o tempo de runtime
    try:
        funct_file = open(f"{config['list_path']}/runtime_info/{func.__name__}", "a")
    except FileNotFoundError:
        funct_file = open(f"{config['list_path']}/runtime_info/{func.__name__}", "w+")

    difference_runtime = b - a
    # O resultado da diferença entre as timestamps em milisegundos ACIMA.

    # colocar o tempo em minutos
    funct_file.write(f"[{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}] Runtime: {(difference_runtime/60)} minutos. \n")


def getfiletext(file: io.TextIOWrapper) -> list:
    """
    Gets text from a file and returns each formatted line in a list
    :param file: Open file object
    :return: List of strings
    """
    # Read all lines at once and process them
    text = [line.strip().removesuffix('\n') for line in file.readlines()]
    return text


def clear_console() -> None:
    os.system("cls" if os.name=="nt" else "clear")


def wait(exdigit: int) -> None:
    '''
    Para o programa até parar em um milisegundo terminado em um número específico
    :param exdigit: int
    :return: None
    '''
    if exdigit < 0 or exdigit > 59:
        raise ValueError("O dígito de espera deve estar entre 0 e 59.")
    elif exdigit == 0:
        return None
    
    while True:
        second = int(datetime.datetime.now().second)
        if second % exdigit == 0:
            logger(tp=7, ex=f"Rodado em {second}!")
            break
        else:
            time.sleep(0.1)  # Aguarda 100 milissegundos

    
    return None


def db_connect(args):
    try:
        sql = mysql.connector.connect(
            host=config["db"]["host"],
            user=config["db"]["user"],
            password=args.p,
            database=config["db"]["database"]
        )
    except mysql.connector.ProgrammingError:
        print("Permissão negada ao conectar ao banco de dados mysql.")
        exit()
    except mysql.connector.Error as e:
        print(f"Erro: {e}")
        exit()

    return sql


def match(regex_type: str, text: str) -> bool:
    """
    Match text against predefined regex patterns
    :param regex_type: Type of regex to use ('age' or 'gender')
    :param text: Text to match against
    :return: Boolean indicating if there's a match
    """
    
    with open(f"{config_path}/regexes.txt", "r", encoding='utf-8') as f:
        regexes = getfiletext(f)
    
    if regex_type == "age":
        regx = regexes[0]
    elif regex_type == "gender":
        regx = regexes[1]
    else:
        raise ValueError(f"Unknown regex type: {regex_type}")
    
    # Use re.search instead of re.match to find pattern anywhere in string
    result = re.search(regx, text, flags=re.M|re.I)
    if result is not None:
        result = True
    else:
        result = False


    return result

