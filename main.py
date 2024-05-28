'''
This file is the main file
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
# Timestamp do inicio do programa
import datetime
start = datetime.datetime.now().timestamp()

import praw
import json
import tools
import multiprocessing
import shutil
import time
import traceback
import random
import os
import psutil
import readline
import csv
import mysql.connector


import preparation as prep

# Timestamp do inicio do programa
start = datetime.datetime.now().timestamp()

# Carregamento dos arquivos json de configuração


config_path = open("./config_path.txt").readlines()[0]

config = json.load(open(f'{config_path}/config.json', 'r')) # Configurações do bot
#api = json.load(open(f"{config['config']}/api.json", "r")) # Configurações da API
#splashes = json.load(open(f"{config['config']}/splashes.json", 'r')) # Mensagens localizadas no final do comentário do bot
reasons = json.load(open(f"{config['config']}/reasons.json", "r")) # Motivos para punição automatizada
boot = True

print(f"Bem-vindo!")

# Carregar o banco de dados para pegar informações
try:
    sql = mysql.connector.connect(
        host=config["db"]["host"],
        user=config["db"]["user"],
        password=input(f"Senha do banco de dados: "),
        database=config["db"]["database"]
    )
except mysql.connector.ProgrammingError:
    print("Permissão negada!")
    exit()

apid = int(config['db']['api_id'])
    
cursor = sql.cursor()

cursor.execute(f"SELECT * FROM users WHERE id={apid};")
api_t = cursor.fetchall()

# Entrar no reddit
reddit = praw.Reddit(
    user_agent=api_t[0][5],
    client_id=api_t[0][2],
    client_secret=api_t[0][3],
    username=api_t[0][1],
    password=api_t[0][4]
)

api = {
    "username": api_t[0][1]
}


# Função da thread principal
def runtime():
    # Parte do meio do comentário
    botxt = f"\n\n# {config['upper_text']}\n\nOlá, meu nome é {config['info']['character']} e eu vou contar os votos que as pessoas dão nesse post. Pra seu voto ser contado, " \
            f"responda o post com uma dessas siglas nos comentários...\n\n"

    # Verifica quais são os votos no arquivo de configuração e adiciona no corpo do comentário
    votxt = ["", "", ""]
    for k, v in config["flairs"].items():
        votxt[v[1]] += f"{k} - {v[2]}\n\n"

    # Adiciona também os votos especiais...
    botxt += votxt[0] + "**Votos especiais**\n\n" + votxt[1] + "\n\n"

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
                sql.commit()
                flairchanges = []
                edits = []
                adds = []

                subcount += 1
                timestmp = datetime.datetime.now().timestamp() - config["break_time"] # Calcula o quaõ velho o post tem que ser para ser ignorado

                if submission.created_utc <= timestmp:
                    break # quebra o loop se o tempo de agora - x dias for maior que o tempo que criado.
                # Pegar os splashes
                cursor.execute(f"SELECT text FROM splashes WHERE owner={apid};")

                splashes = []
                for x in cursor.fetchall():
                    splashes.append(x[0]) 
           
                joke = random.choice(splashes) # Escolhe qual a mensagem vai ficar no final
                etxt = f"""
                                
*{joke}* 
*{config['info']['name']} {config['info']['version']} - by [{config['info']['creator']}](https://www.reddit.com/u/{config['info']['creator']}).*
*Veja meu código fonte: [Código fonte]({config['info']['github']}).*""" # A parte final do comentário

                # Gera o dicionário que contêm os votos
                assholecount = {}
                for flair in config["flairs"].keys():
                    if flair not in config["flairs_ignore"]:
                        assholecount[flair] = 0

                # Pega a lista de ids usando a função getflietext()
                sublist = tools.getfiletext(open(f"{config['list_path']}/idlist", "r"))

                indx = -1
                bdlist = open(f"{config['list_path']}/bodies/bdlist", "r").readlines()
                for sub in bdlist:
                    indx += 1
                    bdlist[indx] = sub.strip()
                indx = -1
                # abrir a lista de corpos já salvos ou não
                bodylist = json.load(open(f"{config['list_path']}/bodies/bodies.json", "r"))
                try:
                    bodylist[f"{submission.id}"]
                except KeyError:
                    bodylist[f"{submission.id}"] = submission.selftext

                bodies_json = json.dumps(bodylist, indent=4)

                # Salva as alterações no arquivo de corpos
                open(f"{config['list_path']}/bodies/bodies.json", "w+").write(bodies_json)
                if submission.id not in sublist: # Se a submissão não tiver nos ids
                    submission.reply(body="OP, por favor responda esse comentário com o motivo de você achar ser o babaca ou não para ajudar no julgamento.\n\n>!NOEDIT!<")
                    botcomment = submission.reply(body=ftxt + botxt + etxt) # Responde a publicação com a soma das partes como placeholder
                    tools.logger(0, sub_id=submission.id)
                    botcomment.mod.distinguish(sticky=True) # Marca o comentário como MOD e o fixa
                    botcomment.mod.approve() # Aprova o comentário
                    sublist.append(submission.id) # Coloca o post na lista de ids
                    submission.flair.select(config["flairs"]["NOT_CLASSIFIED"][0]) # Seleciona a flair de não classificado aind
                    with open(f"{config['list_path']}/idlist", 'a') as f:
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
                invalid = 0 # Comentários inválidos
                for comment in comments:
                    try:
                        if comment.author != api["username"] and comment.author not in users \
                                and comment.author != submission.author: # Se o votante não for o autor, não tiver sido contado já ou não for o bot...
                            # Vê as respostas dos comentários para achar o comentário de ignorar

                            if True: # Removendo a censura
                                comment_body = comment.body.split(' ') # O corpo do comentário é divido em palavras
                                indx = -1
                                # Aparentemente esse código não era tão inutil
                                for sub in comment_body:
                                    indx += 1
                                    sub = sub.split("\n")
                                    comment_body[indx] = sub[0]
                                    try:
                                        comment_body.insert(indx + 1, sub[1])
                                    except IndexError:
                                        pass
                                rate = [] # Lista de palvras strippadas
                                # Para palavra no comentário...
                                for sub in comment_body:
                                    sub = sub.strip() # Méteodo strip na palavra....
                                    replaces = config["replace_list"]
                                    for c in replaces:
                                        sub = sub.replace(c, "") # Remove caractéres especiais

                                    rate.append(sub)

                                indx = -1
                                for w in rate: # Para w na lista de palvras estripadas...
                                    indx += 1
                                    rate[indx] = w.upper() # Coloca a palavra EM MAIUSCULO

                                # Da lista de votos possíveis, se um deles tiver ali, adiciona mais um no número de votos
                                doesItCount = False
                                for r in rates:
                                    if r in rate:
                                        assholecount[r] += 1
                                        doesItCount = True
                                        break

                                # Adiciona os ignorados caso não esteja nas keys
                                if not doesItCount:
                                    invalid += 1

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
                        else:
                            invalid += 1
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

                # Adicionar os comentários ignorados
                votxt += f"\n\n**Comentários inválidos: {invalid}**\n"

                # Pega a porcentagem de votos babacas e votos não babacas
                if total_ac >= 1:
                    for k, v in assholecount.items():
                        if k in config["asshole"]:
                            assholes += (v/total_ac)*100
                        elif k in config["not_asshole"]:
                            commoners += (v/total_ac)*100

                points = int(((assholes - commoners) + 100) * 5) # Por fim, calculado os pontos de babaquice


                # Adiciona no corpo do texto
                ftxt += f"\n# Nível de babaquice: {points/10:.2f}%"
                timeval = "\n\nÚltima análise feita em: " \
                   f"{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n " # Última analise...
                etxt = votxt + timeval + etxt # Junta várias partes do corpo do comentário
                if percent >= 0.5 and total > 0:
                    submission.flair.select(config["flairs"][key][0]) # Seleciona a flair se tiver uma maioria.
                    if key in ["FANFIC", "OT"]: # Se o voto mais top tiver em um desses dois ai...
                        removes = open(f"{config['list_path']}/rid", "r").readlines() # Checa a lista de remoções

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
                            open(f"{config['list_path']}/rid", "a").write(f"{submission.id}\n")
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
                    open(f"{config['list_path']}/bodies/bdlist", "a").write(f"{submission.id}\n")

                body_obj = bodylist[f"{submission.id}"].split("\n\n") # Pega o corpo do comentário
                index = 0
                for line in body_obj:
                    body_obj[index] = ">" + line + "\n\n" # Formata certinho
                    index += 1

                body_obj = ''.join(body_obj)
                bodytxt = f"\n\n# Texto original\n\n{body_obj}\n\n>!NOEDIT!<" # Adiciona o header

                # Adiciona a justificativa no corpo do bot
                ebotxt = botxt
                ebotxt += f"\n\nDe acordo com u/{submission.author}, o motivo dele se achar ou não um babaca é esse:\n\n"
                for _ in range(0, 3): # Tentar 3 vezes para caso de erro
                    time.sleep(config["sleep_time"]["main"])
                    try:
                        reasoning = json.load(open(f"{config['list_path']}/reasoning/reasonings.json", "r"))
                        areason = reasoning[submission.id]
                        break
                    except KeyError:
                        areason = "Não justificado."
                        break
                    except json.JSONDecodeError:
                        # O erro não interfere no programa aprentemente...
                        areason = "Erro ao abrir o arquivo, favor falar para a moderação."

                for line in areason.split("\n"):
                    ebotxt += f">{line}\n"

                for com in comments:
                    if com.author == f"{api['username']}":
                        bd = com.body.split("\n")
                        fullbody = ftxt + ebotxt + etxt # Cola as partes do comentário
                        if ">!NOEDIT!<" not in bd: # Se não tiver ">!NOEDIT!<"
                            if notInBody:
                                com.reply(body=bodytxt)  # Se ainda não tiver o texto original, o comenta
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
    already_run = False
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            current_time = datetime.datetime.now().strftime('%H:%M')

             # Só faz backup em determinados temopos
            if current_time in config["backup"]["time"] and not already_run:
                folder = f"{config['backup']['path']}/{datetime.datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}" # Pega a pasta para salvar o backup
                src_list = [".", config_path, config["list_path"]] # O sources
                for src in src_list:
                    shutil.copytree(src, f"{folder}/{src.split('/')[-1] if src != '.' else 'Main'}", ignore=shutil.ignore_patterns("venv", "__", "pyenv")) # Copia a árvore de pastas
                #tools.logger(2, bprint=False, ex="Backup realizado")
                already_run = True
            else:
                already_run = False
        except Exception:
            print(traceback.format_exc())
        time.sleep(config["sleep_time"]["backup"])
        btime = datetime.datetime.now().timestamp()
        

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
                time.sleep(config["sleep_time"]["textwall"])
                subcount += 1
                subid = submission.id

                sublist = tools.getfiletext(open(f"{config['list_path']}/rid", "r")) # Pega a lista de remoções
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

                    # Número de caracteres
                    chars = 0

                    if body != "": # Se o corpo for diferente de ""
                        for i in body:
                            index += 1
                            chars += 1
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
                    if (paragraphs < config["text_filter"]["min_paragraphs"] or
                            sentences < config["text_filter"]["min_sentences"] or
                            len(body) > config["text_filter"]["max_body"] or
                            len(body) < config["text_filter"]["min_body"]):
                        reason = reasons['TEXTWALL']
                        submission.mod.remove(mod_note=reason['note'], spam=False)
                        submission.reply(body=reason['body']+f"\n\nParágrafos: {paragraphs}\n\nFrases: {sentences}\n\nCaractéres: {chars}")
                        tools.logger(tp=4, sub_id=subid, reason="Parede de texto")

                        open(f"{config['list_path']}/rid", "a").write(f"{subid}\n")
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
                reasonings = json.load(open(f"{config['list_path']}/reasoning/reasonings.json", "r"))
                now = datetime.datetime.now().timestamp()
                time.sleep(config["sleep_time"]["justification"])
                subcount += 1
                subid = submission.id
                reason = ""

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
                                # Checa se não tem um caractere blacklistado, para evitar abusos
                                blacklist = []
                                count = True
                                for i in blacklist:
                                    for x in reply.body:
                                        if x == i:
                                            count = False
                                            break

                                    if not count:
                                        break
                                if count:
                                    didOPans = True
                                    reason = reply.body # O motivo é o corpo da resposta
                                    breakparent = True
                                    break

                            if breakparent:
                                break

                # Para fins de evitar flood de remoções, verifica se o id não está na lista de ignorados
                igl = tools.getfiletext(open(f"{config['list_path']}/ignore_list", "r"))

                if not didOPans and subid not in igl:
                    rid = tools.getfiletext(open(f"{config['list_path']}/rid", "r")) # Abrir a lista de remoções
                    # Se o timestamp de criação - timestamp de agora for maior que 1 hora...
                    if now - submission.created_utc >= 3600:
                        if subid not in rid:
                            removal = reasons['NO_REASON']
                            if not boot: # Se não tiver aado de inicialzar..
                                submission.mod.remove(mod_note=removal['note'], spam=False)
                                submission.reply(body=removal['body'])
                            tools.logger(tp=4, sub_id=subid, reason="Sem justificativa")
                            open(f"{config['list_path']}/rid", "a").write(f"{subid}\n")
                else:
                    if subid in igl:
                        reason = "Post postado antes de precisar justificar."
                    open(f"{config['list_path']}/jid", "a").write(f"{subid}\n")

                    # Salva o motivo
                    reasonings[subid] = reason

                    rstr = json.dumps(reasonings, indent=4)
                    open(f"{config['list_path']}/reasoning/reasonings.json", "w").write(rstr)

            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(justification, atime, btime)
        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


# Filtro para reportar comentários potencialmente perigosos
def filter():
    reddit.validate_on_submit = True
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            subcount = 0
            submissons = reddit.subreddit(config["subreddit"]).new(limit=int(config["submissions"])) # Pega subs
            
            for submission in submissons:
                keywords = tools.getfiletext(open(f"{config['list_path']}/keywords.txt", "r")) # Palavras de filtro

                time.sleep(config["sleep_time"]["filter_sub"])
                subcount += 1

                sublist = tools.getfiletext(open(f"{config['list_path']}/cid", "r")) # Pega a lista de remoções
                indx = -1

                submission.comment_sort = 'new' # Filtra os comentários por novos
                submission.comments.replace_more(limit=None)
                comments = submission.comments.list()

                # Iteração pela lista de comentários
                for com in comments:
                    time.sleep(config["sleep_time"]["filter_com"])
                    if com.id not in sublist:
                        for x in com.body.lower().replace("\n", " ").replace("\n\n", " ").split(" "):
                            for letra in x:
                                replace = config["replace_list"]
                                if letra in replace:
                                    x = x.replace(letra, '')
                            if x in keywords:
                                # Se o filtro pegar, o comentário vai ser denunciado
                                com.report(f"Filtro detectou: {x}")

                                tools.logger(ex=x, sub_id=submission.id, com_id=com.id, tp=6)

                        open(f"{config['list_path']}/cid", "a").write(f"{com.id}\n")

            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(filter, atime, btime)
        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


def stat(): # Estatisticas do subreddit
    reddit.validate_on_submit = True
    while True:
        try:
            time.sleep(config["sleep_time"]["stat"])
            add = False
            subr = reddit.subreddit(config["subreddit"])

            sql.commit()
            cursor.execute("SELECT max(id) FROM statistics")
            last_id = int(cursor.fetchall()[0][0])

            # Checar se ja não foi checado e adicionar caso tenha passado uma hora no arquivo csv
            sql_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            subs = subr.subscribers
            
            cursor.execute(f"SELECT members FROM statistics WHERE id={last_id}")

            last_members = int(cursor.fetchall()[0][0])
            growt = subs-last_members
            growt_perc = ((subs-last_members)/last_members)*100

            cursor.execute(f"INSERT INTO statistics (`id`, `owner`, `datetime`, `members`, `growt`, `growt_percent`) VALUES ({last_id+1}, {apid}, '{sql_time}', {subs}, {growt}, {growt_perc})")

            sql.commit()
           # if add:
            #    reddit.subreddit(f"{config['log_subreddit']}").submit(title=f"{date} {int(hour)-1 if int(hour) >= 1 else '23'}-{ctime} - GROWT", selftext=f"{subs} (CRESCIMENTO: {growt})")
            
            #tools.log_runtime(stat, atime, btime)

        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


if __name__ == '__main__':
    tools.clear_console()
    # Preparar os arquivos
    prep.begin(config)

    # Carrega as funções
    funcs = [runtime, backup, clearlog, textwall, justification, filter, stat]
    processes = [multiprocessing.Process(target=x, args=[], name=x.__name__) for x in funcs] # Inicializa os processos

    pids = [os.getpid()]

    index = -1
    # E os bota para rodar de segundo plano
    func_total = 0 # total de milisegundos na inicialização da função
    for i in processes:
        func_start = datetime.datetime.now().timestamp() #ms da função
        
        index += 1
        i.start()
        pids.append(i.pid) # Salva os pids
        
        func_end = datetime.datetime.now().timestamp() # ms da função
        func_total += (func_end - func_start)*1000

        print(f"Iniciado processo com o PID {i.pid} para a função {funcs[index].__name__}: {(func_end - func_start)*1000:.0f} ms") 

    # Termino do processo de inicializaçãp.
    end = datetime.datetime.now().timestamp()

    total_main = (end-start)*1000
    print(f"main: {total_main:.0f} ms. ({total_main - func_total:.0f} ms de inicialização e {func_total:.0f} ms de preparação)")
    
    # Loop para os comandos (primeiro plano)
    while True:
        inp = input("=> ").upper().split(" ")
        if len(inp) >= 1:
            if inp[0] == "R": # Se o input do usuário for R, vai simplesmente reccarregar os valores. (Não testado)
                config = json.load(open('config.json', 'r'))
                sql.commit()
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
                while True:
                    try:
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
                                
                                print(f"{funcs[index].__name__ if r > 0 else 'main'} ({process.pid}): {mem_qnt:.0f} mb, {cpu:.2f}% CPU")

                                if r > 0:
                                    index += 1
                                
                                r += 1

                        print(f"Total: {mem:.0f} mb ({perc:.2f}%), {cputotal:.2f}% CPU")
                        uinput = input("")

                        if uinput != "":
                            break
                        os.system("clear")
                    except KeyboardInterrupt:
                        os.system(f"{config['python']} ./main.py")
                        break

            elif inp[0] == "LOGSTREAM":
                while True:
                    user = input("")
                    tools.clear_console() 
                    if user == "":
                        print(open(f"{config['list_path']}/log", "r").readlines()[-1])
                    else:
                        break
            elif inp[0] == "ADDSPLASH":
                sql.commit()
                cursor.execute(f"SELECT id FROM splashes WHERE owner={apid}")
                lastid = int(cursor.fetchall()[-1][0])
                
                try:
                    cursor.execute(f"INSERT INTO splashes (id, owner, text) VALUES ({lastid+1}, {apid}, {str(input('Texto: '))})")
                except Exception as e:
                    print(traceback.format_exc())

                sql.commit()

