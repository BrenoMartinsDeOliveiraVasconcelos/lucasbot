'''
This file is a standalone manager for the bot
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

import psutil
import os
import sys
import json
import tools
import time

def main(args: list, config: dict) -> int:
    # Se o número de argumentos for menor que 2, vai dar erro
    if len(args) <= 1:
        return -1

    # Se o argumento for de memória, vai fazer o calculo da memória
    if args[1] in ["memory", "m", "-m", "--memory"]:
        pids = tools.getfiletext(open(f'{config["list_path"]}/pids', "r"))
        
        pids = [int(x) for x in pids]

        pids.insert(0, os.getpid())
        while True:
            time.sleep(0.5)

            tools.clear_console()
            mem = 0
            perc = 0
            index = 0
            cputotal = 0
            r = 0
            all_processes = psutil.process_iter()

            for process in all_processes:
                if process.pid in pids:
                    perc += process.memory_percent()
                    memory_info = process.memory_info()
                    mem_qnt = memory_info.rss / 1024 / 1024
                    mem += mem_qnt
                    cpu = process.cpu_percent()
                    cputotal += cpu
                    
                    print(f"{process.pid}: {mem_qnt:.0f} mb, {cpu:.2f}% CPU")

                    if r > 0:
                        index += 1
                    
                    r += 1

            print(f"Total: {mem:.0f} mb ({perc:.2f}%), {cputotal:.2f}% CPU")
    
    # Reiniciar/matar o processo principal
    else:
        return -1


if __name__ == '__main__':
    config = json.load(open(f"{open('./config_path.txt').readlines()[0]}/config.json", "r"))
    code = main(sys.argv, config)

    if code == -1: # -1 é quando não tem argumentos
        print(f"Nenhum argumento válido! ", end="")

    print(f"Código: {code}")

