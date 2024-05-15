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


def begin(config: dict):
    '''
    Prepara os arquivos que serão usados pelo script
    :return: None
    '''
    # Função de preparação

    #./bodies
    if os.path.exists(f"{config['list_path']}/bodies"):
        if not os.path.exists(f"{config['list_path']}/bodies/bdlist"):
            open(f"{config['list_path']}/bodies/bdlist", "w+")

        if not os.path.exists(f"{config['list_path']}/bodies/bodies.json"):
            open(f"{config['list_path']}/bodies/bodies.json", "w+").write("{}")

        if not os.path.exists(f"{config['list_path']}/reasoning/reasonings.json"):
            open(f"{config['list_path']}/reasoning/reasonings.json", "w+").write("{}")
    else:
        os.mkdir(f"{config['list_path']}/bodies")
        open(f"{config['list_path']}/bodies/bdlist", "w+")
        open(f"{config['list_path']}/bodies/bodies.json", "w+").write("{}")

    # arquivo de log e id
    emptytxts = ["idlist", "log", "rid", "aid", "aarid", "jid", "cid", "keywords.txt"]
    for i in emptytxts:
        if not os.path.exists(f"{config['list_path']}/{i}"):
            open(f"{config['list_path']}/{i}", "w+")

    # Pastas vazias
    folders = ["runtime_info"]
    for i in folders:
        if not os.path.exists(f"{config['list_path']}/{i}"):
            os.mkdir(f"{config['list_path']}/{i}")
