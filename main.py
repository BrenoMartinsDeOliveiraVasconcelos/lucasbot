'''
This file is the main file
Copyright (C) 2023  Breno Martins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,nnnnnnnnnnnnn
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import praw
import json
import tools
import multiprocessing
import shutil
import time
import datetime
import traceback
import random
import os
import psutil

import preparation as prep

# Timestamp do inicio do programa
start = datetime.datetime.now().timestamp()

# Carregamento dos arquivos json de configuração
config = json.load(open('config.json', 'r')) # Configurações do bot
api = json.load(open("api.json", "r")) # Configurações da API
splashes = json.load(open('splashes.json', 'r')) # Mensagens localizadas no final do comentário do bot
reasons = json.load(open("reasons.json", "r")) # Motivos para punição automatizada

# Entrar no reddit
reddit = praw.Reddit(
    user_agent=api["useragent"],
    client_id=api["clientid"],
    client_secret=api["clientsecret"],
    username=api["username"],
    password=api["password"]
)


# Função da thread principal
def runtime():
    # Parte do meio do comentário
    botxt = f"\n\n# {config['upper_text']}\n\nVou contar as respostas que as pessoas dão nesse post! Pra ser contado, " \
            f"responda com essas siglas o post:\n\n"

    # Verifica quais são os votos no arquivo de configuração e adiciona no corpo do comentário
    votxt = ["", "", ""]
    for k, v in config["flairs"].items():
        votxt[v[1]] += f"{k} - {v[2]}\n\n"

    # Adiciona também os votos especiais...
    botxt += votxt[0] + "**Votos especiais**\n\n" + votxt[1] + "\n\n"
    botxt += "##Nota: Pode demorar cerca de 5 minutos para atualizar!\n\n"

    reddit.validate_on_submit = True
    
    # Loop principal da função 
    while True:
        try:
            # Texto placeholder para a parte que diz o veredito atual
            ftxt = f"# Veredito atual:" \
                   f" Não processado ainda\n\n"
            subcount = 0 # Número da submissão atual
            submissons = reddit.subreddit(config["subreddit"]).new(limit=int(config["submissions"])) # Pega X submissões do feed do subreddit
            atime = datetime.datetime.now().timestamp() # Essa parte serve para o cálculo do tempo que roddou a função

            # Loop para iterar nas submissões
            for submission in submissons:
                flairchanges = []
                edits = []
                adds = []

                subcount += 1
                timestmp = datetime.datetime.now().timestamp() - config["break_time"] # Calcula o quaõ velho o post tem que ser para ser ignorado

                if submission.created_utc <= timestmp:
                    break # quebra o loop se o tempo de agora - x dias for maior que o tempo que criado.

                joke = random.choice(splashes) # Escolhe qual a mensagem vai ficar no final
                etxt = f"""
                                
*{joke}* 
*{config['info']['name']} v{config['info']['version']} - by [{config['info']['creator']}](https://www.reddit.com/u/{config['info']['creator']}).*
*Veja meu código fonte: [Código fonte]({config['info']['github']}).*""" # A parte final do comentário

                # Gera o dicionário que contêm os votos
                assholecount = {}
                for flair in config["flairs"].keys():
                    if flair not in config["flairs_ignore"]:
                        assholecount[flair] = 0

                # Pega a lista de ids usando a função getflietext()
                sublist = tools.getfiletext(open("idlist", "r"))

                indx = -1
                bdlist = open("bodies/bdlist", "r").readlines()
                for sub in bdlist:
                    indx += 1
                    bdlist[indx] = sub.strip()
                indx = -1
                # abrir a lista de corpos já salvos ou não
                bodylist = json.load(open("./bodies/bodies.json", "r"))
                try:
                    bodylist[f"{submission.id}"]
                except KeyError:
                    bodylist[f"{submission.id}"] = submission.selftext

                bodies_json = json.dumps(bodylist, indent=4)

                # Salva as alterações no arquivo de corpos
                open("./bodies/bodies.json", "w+").write(bodies_json)
                if submission.id not in sublist: # Se a submissão não tiver nos ids
                    submission.reply(body="Justifique o motivo de você achar ser o babaca respondendo ao bot em até 1 hora. Falhar nisso causará remoção.\n\n>!NOEDIT!<")
                    botcomment = submission.reply(body=ftxt + botxt + etxt) # Responde a publicação com a soma das partes como placeholder
                    tools.logger(0, sub_id=submission.id)
                    botcomment.mod.distinguish(sticky=True) # Marca o comentário como MOD e o fixa
                    botcomment.mod.approve() # Aprova o comentário
                    sublist.append(submission.id) # Coloca o post na lista de ids
                    submission.flair.select(config["flairs"]["NOT_CLASSIFIED"][0]) # Seleciona a flair de não classificado aind
                    with open('idlist', 'a') as f:
                        f.write(submission.id + '\n') # Grava a nova lista de ids
                submission.comment_sort = 'new' # Filtra os comentários por novos
                submission.comments.replace_more(limit=None)
                comments = submission.comments.list() # E por fim pegas os comentários para calcular o julgamento
                
                # Variáveis para o cálculo
                highest = 0
                key = ''
                users = []
                total = 0
                judgment = ""
                percent = 0
                rates = [x for x in assholecount.keys()]
                judges = config["vote_name"]
                num_coms = 0

                # Número de comentários
                for com in comments:
                    num_coms += 1

                # Loop para iterar nos comentários
                for comment in comments:
                    try:
                        if comment.author != api["username"] and comment.author not in users \
                                and comment.author != submission.author: # Se o votante não for o autor, não tiver sido contado já ou não for o bot...
                            comment_body = comment.body.split(' ') # O corpo do comentário é divido em palavras
                            indx = -1

                            rate = [] # Lista de palvras strippadas
                            # Para palavra no comentário...
                            for sub in comment_body:
                                sub = sub.strip() # Méteodo strip na palavra....
                                replaces = ["!", "?", ".", ",", ":", "(", ")", "[", "]", "{", "}", "-",
                                            "+", "/", "\\", "'", '"', '~', "\n", "\n\n"]
                                for c in replaces:
                                    sub = sub.replace(c, "") # Remove caractéres especiais
        
                                rate.append(sub)

                            indx = -1
                            for w in rate: # Para w na lista de palvras estripadas...
                                indx += 1
                                rate[indx] = w.upper() # Coloca a palavra EM MAIUSCULO
                            
                            # Da lista de votos possíveis, se um deles tiver ali, adiciona mais um no número de votos
                            for r in rates:
                                if r in rate:
                                    assholecount[r] += 1
                                    break
                            
                            total = 0
                            # Para k e v na lista de votos
                            for k, v in assholecount.items():
                                total += v # Adiciona mais um no total
                                if v >= highest: # E vê qual o maior 
                                    highest = v
                                    key = k
                            try:
                                percent = highest / total # Caclula qual a poercentagem
                            except ZeroDivisionError:
                                percent = 1.00

                            # Calcula o julgamento
                            ind = rates.index(key)
                            judgment = judges[ind]

                            if percent < 0.50: # Se a porcentagem for menor quee 50%, nenhum teve a maioria
                                judgment = "Nenhum voto atingiu a maioria"
                                votetxt = f"{total} votos contados ao total"
                            else:
                                votetxt = f"{percent * 100:.2f}% de {total} votos" # Se não, atingiu

                            # Agora, se o total for igual a zero não foi avaliado ainda =)
                            if total == 0:
                                judgment = "Não avaliado"
                                votetxt = f"{total} votos contados ao total"
                            ftxt = f"### " \
                                    f"{judgment} ({votetxt})"
                            users.append(comment.author)
                    except Exception:
                        tools.logger(5, ex=traceback.format_exc())

                # Calcula todas as porcentagens
                percents = {}
                for k, v in assholecount.items():
                    try:
                        percents[k] = f"{(int(v) / total) * 100:.2f}"
                    except ZeroDivisionError:
                        percents[k] = f"0.00"
                tools.logger(2, ex="Submissão analizada!")

                # A tabelinha
                votxt = f"""
# Tabela de votos
Voto | Quantidade | %
:--:|:--:|:--:
"""

                assholes = 0 # Número de votos babacas
                commoners = 0 # Número de votos "comuns"
                total_ac = 0 # Total de votos babacas e comuns
                # Calcula os babacas e põe informações na tabela
                for k, v in assholecount.items():
                    votxt += f"{k} | {v} | {percents[k]}%\n"
                    if total >= 1:
                        if k in config["asshole"] or k in config['not_asshole']:
                            total_ac += v

                # Pega a porcentagem de votos babacas e votos não babacas
                if total_ac >= 1:
                    for k, v in assholecount.items():
                        if k in config["asshole"]:
                            assholes += (v/total_ac)*100
                        elif k in config["not_asshole"]:
                            commoners += (v/total_ac)*100

                points = int(((assholes - commoners) + 100) * 5) # Por fim, calculado os pontos de babaquice
                names = ["Extremamente baixo", "Muito baixo", "Baixo", "Médio-baixo", "Médio-alto", "Alto", "Muito alto", "Extremamente alto"]
                
                # Jeito gambiarrento de calcular os níveis sem criar uma torre de ifs...
                levels = []
                for y in range(0, 8):
                    for _ in range(0, 126):
                        levels.append(names[y])

                # Pega o nível da lista de níveis
                levels.append(names[-1])
                level = levels[points]

                # Adiciona no corpo do texto
                ftxt += f"\n# Nível de babaquice: {points/10:.0f}% ({level})"
                timeval = "\n\nÚltima análise feita em: " \
                   f"{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n " # Última analise...
                etxt = votxt + timeval + etxt # Junta várias partes do corpo do comentário
                if percent >= 0.5 and total > 0:
                    submission.flair.select(config["flairs"][key][0]) # Seleciona a flair se tiver uma maioria.
                    if key in ["FANFIC", "OT"]: # Se o voto mais top tiver em um desses dois ai...
                        removes = open('rid', "r").readlines() # Checa a lista de remoções

                        indx = -1
                        for sub in removes:
                            indx += 1
                            removes[indx] = sub.strip()

                        if submission.id not in removes and total > 1: # Se a submissão não tiver na lista de remoção e o total for maior que 1 (a lista ainda nn foi gravada)
                            
                            # Remove a submissão e adiciona lista de remoções
                            reason = reasons["FAKE_OT"]
                            submission.mod.remove(mod_note=f"{reason['note']}", spam=False)
                            submission.reply(body=f"{reason['body']}")
                            tools.logger(tp=4, sub_id=submission.id, reason="VIolação")
                            open("rid", "a").write(f"{submission.id}\n")
                # Se a porcaentagem está fora da média, seleciona a flair de fora da média
                elif percent < 0.5 and total > 0:
                    submission.flair.select(config["flairs"]["INCONCLUSIVE"][0])
                elif total == 0: # Se o total for exatamente zero, a de não disponível
                    submission.flair.select(config["flairs"]["NOT_AVALIABLE"][0])
                flairchanges += f"\n* Flair de https://www.reddit.com/{submission.id} é '{judgment}'"
                tools.logger(2, ex=f"Flair editada em {submission.id}")

                notInBody = False
                if submission.id not in bdlist: # Se a bumissão não tiver na lista de corpos...
                    notInBody = True
                    open('./bodies/bdlist', "a").write(f"{submission.id}\n")

                body_obj = bodylist[f"{submission.id}"].split("\n\n") # Pega o corpo do comentário
                index = 0
                for line in body_obj:
                    body_obj[index] = ">" + line + "\n\n" # Formata certinho
                    index += 1

                body_obj = ''.join(body_obj)
                bodytxt = f"\n\n# Texto original\n\n{body_obj}\n\n>!NOEDIT!<" # Adiciona o header

                # Adiciona a justificativa no corpo do bot
                ebotxt = botxt
                ebotxt += f"\n\n# O motivo do op se achar babaca é:\n"
                try:
                    reasoning = json.load(open("reasoning/reasonings.json", "r"))
                    areason = reasoning[submission.id]
                except KeyError:
                    areason = "Não justificado."
                for line in areason.split("\n"):
                    ebotxt += f"*{line}*\n\n"

                for com in comments:
                    if com.author == f"{api['username']}":
                        bd = com.body.split("\n")
                        fullbody = ftxt + ebotxt + etxt # Cola as partes do comentário
                        if notInBody:
                            com.reply(body=bodytxt) # Se ainda não tiver o texto original, o comenta
                        if ">!NOEDIT!<" not in bd: # Se não tiver ">!NOEDIT!<"
                            com.edit(
                                body=fullbody) # Edita o comentário do placar
                            tools.logger(1, sub_id=submission.id)
                            edits += f"\n* Comentário do bot editado em https://www.reddit.com/{submission.id}\n"
                ftxt = f"# Veredito atual:" \
                        f" Não disponível \n\nÚltima atualização feita em: " \
                        f"{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n "

            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(runtime, atime, btime) # Coloca o runtime total da função
        except Exception as e:
            tools.logger(5, ex=traceback.format_exc())

# Função de backup
def backup():
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            folder = f"{config['backup']}/{datetime.datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}" # Pega a pasta para salvar o backup
            src = "." # O source é a pasta atual
            shutil.copytree(src, folder, ignore=shutil.ignore_patterns("venv", ".", "__")) # Copia a árvore de pastas
            tools.logger(2, bprint=False, ex="Backup realizado")
        except:
            pass
        time.sleep(3600) # Espera 3600 segundos para poder continuar
        btime = datetime.datetime.now().timestamp()
        tools.log_runtime(backup, atime, btime)
        

# Limpador de logs
def clearlog():
    while True:
        atime = datetime.datetime.now().timestamp()
        time.sleep(config["clear_log"])
        open("log", "w+").write("")
        btime = datetime.datetime.now().timestamp()
        tools.log_runtime(clearlog, atime, btime)


# Verificador de paredes de texto
def textwall():
    reddit.validate_on_submit = True
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            subcount = 0
            submissons = reddit.subreddit(config["subreddit"]).new(limit=int(config["submissions"])) # Pega subs
            for submission in submissons:
                time.sleep(1)
                subcount += 1
                subid = submission.id

                sublist = tools.getfiletext(open("rid", "r")) # Pega a lista de remoções
                indx = -1

                for i in sublist:
                    indx += 1
                    sublist[indx] = i.strip()

                if subid not in sublist: # Se o submissão não tiver na lista de subs...
                    try:
                        body = submission.selftext # Pega o corpo do texto
                    except:
                        body = ""
                    
                    # Coloca os valores padrões de parágrafos e frases para 1...
                    paragraphs = 1 
                    sentences = 1

                    # Determinar quantos parágrafos tem o texto
                    index = -1
                    paragraph_cond = False
                    if body != "": # Se o corpo for diferente de ""
                        for i in body:
                            index += 1
                            try:
                                if i == "\n" and body[index+1] == "\n":
                                    paragraphs += 1
                                    sentences += 1
                                    paragraph_cond = True
                            except IndexError:
                                pass

                            # Quantas frases tem
                            if i in [".", "?", "!"] and not paragraph_cond:
                                sentences += 1

                            paragraph_cond = False
                    else:
                        # Se não, é zero!
                        paragraphs = 0
                        sentences = 0

                    # Remove a publicação suspeita de parede de texto.
                    if paragraphs < config["text_filter"]["min_paragraphs"] or sentences < config["text_filter"]["min_sentences"]  or len(body) > config["text_filter"]["max_body"] :
                        reason = reasons['TEXTWALL']
                        submission.mod.remove(mod_note=reason['note'], spam=False)
                        submission.reply(body=reason['body'])
                        tools.logger(tp=4, sub_id=subid, reason="Parede de texto")

                        open("rid", "a").write(f"{subid}\n")
            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(textwall, atime, btime)
        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


def justification():
    '''
    Sistema que exige justifiação do post. Verifica depois de 1 hora de postado se o post foi justificado.
    :return:
    '''
    reddit.validate_on_submit = True
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            subcount = 0
            submissons = reddit.subreddit(config["subreddit"]).new(limit=int(config["submissions"]))  # Pega subs
            for submission in submissons:
                reasonings = json.load(open(f"reasoning/reasonings.json", "r"))
                now = datetime.datetime.now().timestamp()
                time.sleep(2)
                subcount += 1
                subid = submission.id
                reason = ""

                sublist = tools.getfiletext(open("jid", "r"))  # Pega a lista de ids
                idlist = tools.getfiletext(open("idlist", "r"))
                indx = -1

                # Contiunuar
                submission.comment_sort = 'new'  # Filtra os comentários por novos
                submission.comments.replace_more(limit=None)
                comments = submission.comments.list()
                didOPans = False # se o op respondeu
                breakparent = False

                for com in comments:
                    if com.author == api["username"]: # Se o autor do comentário for o bot.
                        # Verificar se o autor do post respondeu
                        comreplies = com.replies
                        for reply in comreplies: # Para cada resposta do comentário
                            if reply.author == submission.author:
                                didOPans = True
                                reason = reply.body # O motivo é o corpo da resposta
                                breakparent = True
                                break

                            if breakparent:
                                break

                # Para fins de evitar flood de remoções, verifica se o id não está na lista de ignorados
                igl = tools.getfiletext(open("ignore_list", "r"))

                if not didOPans and subid not in igl:
                    # Se o timestamp de criação - timestamp de agora for maior que 1 hora...
                    if now - submission.created_utc >= 3600:
                        removal = reasons['NO_REASON']
                        submission.mod.remove(mod_note=removal['note'], spam=False)
                        submission.reply(body=removal['body'])
                        tools.logger(tp=4, sub_id=subid, reason="Sem justificativa")
                else:
                    if subid in igl:
                        reason = "Post postado antes de precisar justificar."
                    open("jid", "a").write(f"{subid}\n")

                    # Salva o motivo
                    reasonings[subid] = reason

                    rstr = json.dumps(reasonings, indent=4)
                    open(f"reasoning/reasonings.json", "w").write(rstr)

            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(justification, atime, btime)
        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())



if __name__ == '__main__':
    # Preparar os arquivos
    prep.begin()

    # Carrega as funções
    funcs = [runtime, backup, clearlog, textwall, justification]
    processes = [multiprocessing.Process(target=x, args=[], name=x.__name__) for x in funcs] # Inicializa os processos

    pids = [os.getpid()]

    index = -1
    # E os bota para rodar de segundo plano
    for i in processes:
        index += 1
        i.start()
        pids.append(i.pid) # Salva os pids
        print(f"Iniciado processo com o PID {i.pid} para a função {funcs[index].__name__}()")

    # Termino do processo de inicializaçãp.
    end = datetime.datetime.now().timestamp()
    print(f"main: {(end-start)*1000:.0f} ms.")
    
    # Loop para os comandos (primeiro plano)
    while True:
        inp = input("=> ").upper().split(" ")
        if len(inp) >= 1:
            if inp[0] == "R": # Se o input do usuário for R, vai simplesmente reccarregar os valores. (Não testado)
                config = json.load(open('config.json', 'r'))
                api = json.load(open("api.json"))
                splashes = json.load(open('splashes.json', 'r'))
                print("Valores recarregados na memória.")
            elif inp[0] == "E": # E termina o programa.
                for i in processes:
                    i.terminate()

                break
            elif inp[0] == "RESTART": # Reinicia o programa
                for i in processes:
                    i.terminate()

                os.system(f"{config['python']} ./main.py")
                break
            elif inp[0] == "MEMORY": # Calcula a memória utilizada pelos processos
                mem = 0
                perc = 0
                all_processes = psutil.process_iter()

                for process in all_processes:
                    if process.pid in pids:
                        perc += process.memory_percent()
                        memory_info = process.memory_info()
                        mem += memory_info.rss / 1024 / 1024

                print(f"{mem:.0f} mb ({perc:.2f}%)")
