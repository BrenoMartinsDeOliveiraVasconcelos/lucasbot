'''
Stores initialization functions
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

import os


def begin():
    '''
    Prepara os arquivos que serão usados pelo script
    :return: None
    '''
    # Função de preparação
    files = ["number_comments.json"]
    if os.path.exists("./data"):
        # Ok, vamos checar se existe os arquivos necessários
        for i in files:
            if not os.path.exists(f"./data/{i}"):
                open(f"./data/{i}", "w+").write("{}")
    else:
        os.mkdir("./data")
        for i in files:
            open(f"./data/{i}", "w+").write("{}")

    #./bodies
    if os.path.exists("./bodies"):
        if not os.path.exists("./bodies/bdlist"):
            open("./bodies/bdlist", "w+")

        if not os.path.exists("./bodies/bodies.json"):
            open("./bodies/bodies.json", "w+").write("{}")
    else:
        os.mkdir("./bodies")
        open("./bodies/bdlist", "w+")
        open("./bodies/bodies.json", "w+").write("{}")

    # arquivo de log e id
    emptytxts = ["idlist", "log", "rid", "aid", "aarid"]
    for i in emptytxts:
        if not os.path.exists(f"./{i}"):
            open(f"./{i}", "w+")

    # Pastas vazias
    folders = ["runtime_info"]
    for i in folders:
        if not os.path.exists(f'./{i}'):
            os.mkdir(f"./{i}")
