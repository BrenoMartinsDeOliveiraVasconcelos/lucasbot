'''
Stores initialization functions
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

import os

first_run = False

def begin(config: dict) -> None:
    '''
    Prepara os arquivos que serão usados pelo script
    :return: None
    '''
    # Função de preparação

    #./bodies

    try:
        if not os.path.exists(f"{config['list_path']}/reasoning/reasonings.json"):
            open(f"{config['list_path']}/reasoning/reasonings.json", "w+").write("{}")

        # arquivo de log e id
        emptytxts = ["idlist", "log", "rid", "aid", "aarid", "jid", "cid", "keywords.txt", "pids"]
        for i in emptytxts:
            if not os.path.exists(f"{config['list_path']}/{i}"):
                first_run = True
                open(f"{config['list_path']}/{i}", "w+")

        # Pastas vazias
        folders = ["runtime_info"]
        for i in folders:
            if not os.path.exists(f"{config['list_path']}/{i}"):
                first_run = True
                os.mkdir(f"{config['list_path']}/{i}")
    except PermissionError:
        print("O diretóŕio em list_path é inacessível para o usuário executando o script. Edite o arquivo config.json ou conceda as devidas permissões.")
        exit(-1)
    except FileNotFoundError:
        print(f"O diretório especificado {config['list_path']} não existe. Edite o arquivo config.json ou crie-o.")
        exit(-1)
