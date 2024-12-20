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

import datetime
import praw
import prawcore
import prawcore.exceptions
import json
import praw.exceptions
import tools
import multiprocessing
import shutil
import time
import traceback
import random
import os
import psutil
import readline
import mysql.connector
import preparation as prep
import argparse


parser = argparse.ArgumentParser(prog='lucasbot', description='Bot do reddit.')

parser.add_argument('-p') # Senha do banco de dados
parser.add_argument("-b", default="Nn") # inicia imediatamente o bakcup ou não
args = parser.parse_args()


start = datetime.datetime.now().timestamp()

# Timestamp do inicio do programa
start1 = datetime.datetime.now().timestamp()

# Carregamento dos arquivos json de configuração

config = tools.config
reasons = tools.reasons
boot = tools.boot

config_path = tools.config_path


print(f"Bem-vindo!")

# Carregar o banco de dados para pegar informações
end1 = datetime.datetime.now().timestamp()
start2 = datetime.datetime.now().timestamp()

sql = tools.db_connect(args=args)

apid = int(config['db']['api_id'])

cursor = sql.cursor()
cursor.execute('set global max_allowed_packet=67108864;')
sql.commit()

cursor.execute(f"SELECT * FROM users WHERE id={apid};")
api_t = cursor.fetchall()

# Gerar user agent

uagent = f'<{os.name}>:<{config["info"]["name"]}>:<{config["info"]["version"]}> (by /u/{config["info"]["creator"]})'

# Entrar no reddit

try:
    reddit = praw.Reddit(
        user_agent=uagent,
        client_id=api_t[0][2],
        client_secret=api_t[0][3],
        username=api_t[0][1],
        password=api_t[0][4]
    )
except (prawcore.exceptions.TooManyRequests, praw.exceptions.RedditAPIException):
    print("Permissão negada ao conectar ao Reddit. Verifique as credenciais e tente novamente.")

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
        sql = tools.db_connect(args=args)

        cursor = sql.cursor()
        try:
            # Texto placeholder para a parte que diz o veredito atual
            ftxt = f"# Veredito atual:" \
                   f" Não processado ainda\n\n"
            subcount = 0  # Número da submissão atual
            submissons = reddit.subreddit(config["subreddit"]).new(
                limit=int(config["submissions"]))  # Pega X submissões do feed do subreddit
            atime = datetime.datetime.now().timestamp()  # Essa parte serve para o cálculo do tempo que roddou a função

            # Loop para iterar nas 
            tmr_exceptions = 0
            for submission in submissons:
                try:
                    time.sleep(config["sleep_time"]["main"])

                    sql.commit()
                    flairchanges = []
                    edits = []
                    adds = []

                    subcount += 1
                    tools.logger(tp=2, ex=f"Submissão atual: {subcount}")
                    timestmp = datetime.datetime.now().timestamp() - config[
                        "break_time"]  # Calcula o quaõ velho o post tem que ser para ser ignorado

                    if submission.created_utc <= timestmp:
                        break  # quebra o loop se o tempo de agora - x dias for maior que o tempo que criado.
                    # Pegar os splashes
                    cursor.execute(f"SELECT text FROM splashes WHERE owner={apid};")

                    splashes = []
                    for x in cursor.fetchall():
                        splashes.append(x[0])

                    joke = random.choice(splashes)  # Escolhe qual a mensagem vai ficar no final
                    etxt = f"""
                                    
*{joke}* 
*{config['info']['name']} {config['info']['version']} - by JakeWisconsin.*
*Veja meu código fonte: [Código fonte]({config['info']['github']}). Configurações para o subreddit: [Configurações]({config['info']['config_github']})*"""  # A parte final do comentário

                    # Gera o dicionário que contêm os votos
                    assholecount = {}
                    for flair in config["flairs"].keys():
                        if flair not in config["flairs_ignore"]:
                            assholecount[flair] = 0

                    # Pega a lista de ids usando a função getflietext()
                    sublist = tools.getfiletext(open(f"{config['list_path']}/idlist", "r"))

                    indx = -1
                    # abrir a lista de corpos já salvos ou não

                    # Salva as alterações no arquivo de corpos
                    if submission.id not in sublist:  # Se a submissão não tiver nos ids
                        submission.reply(
                            body="OP, por favor responda esse comentário com o motivo de você achar ser o babaca ou não para ajudar no julgamento.\n\n>!NOEDIT!<")
                        botcomment = submission.reply(
                            body=ftxt + botxt + etxt)  # Responde a publicação com a soma das partes como placeholder
                        try:
                            botcomment.reply(body="# Texto original\n\n"+submission.selftext+"\n\n>!NOEDIT!<")
                        except Exception:
                            botcomment.reply(body="Texto muito longo.\n\n>!NOEDIT!<")
                        tools.logger(0, sub_id=submission.id)
                        botcomment.mod.distinguish(sticky=True)  # Marca o comentário como MOD e o fixa
                        botcomment.mod.approve()  # Aprova o comentário
                        sublist.append(submission.id)  # Coloca o post na lista de ids
                        submission.flair.select(
                            config["flairs"]["NOT_CLASSIFIED"][0])  # Seleciona a flair de não classificado aind
                        with open(f"{config['list_path']}/idlist", 'a') as f:
                            f.write(submission.id + '\n')  # Grava a nova lista de ids
                    
                    submission.comment_sort = 'new'  # Filtra os comentários por novos
                    submission.comments.replace_more(limit=None)
                    comments = submission.comments.list()  # E por fim pegas os comentários para calcular o julgamento

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
                    invalid = 0  # Comentários inválidos
                    for comment in comments:
                        try:
                            if comment.author != api["username"] and comment.author not in users \
                                    and comment.author != submission.author:  # Se o votante não for o autor, não tiver sido contado já ou não for o bot...
                                # Vê as respostas dos comentários para achar o comentário de ignorar

                                if True:  # Removendo a censura
                                    comment_body = comment.body.split(' ')  # O corpo do comentário é divido em palavras
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
                                    rate = []  # Lista de palvras strippadas
                                    # Para palavra no comentário...
                                    for sub in comment_body:
                                        sub = sub.strip()  # Méteodo strip na palavra....
                                        replaces = config["replace_list"]
                                        for c in replaces:
                                            sub = sub.replace(c, "")  # Remove caractéres especiais

                                        rate.append(sub)

                                    indx = -1
                                    for w in rate:  # Para w na lista de palvras estripadas...
                                        indx += 1
                                        rate[indx] = w.upper()  # Coloca a palavra EM MAIUSCULO

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
                                        total += v  # Adiciona mais um no total
                                        if v >= highest:  # E vê qual o maior
                                            highest = v
                                            key = k
                                    try:
                                        percent = highest / total  # Caclula qual a poercentagem
                                    except ZeroDivisionError:
                                        percent = 1.00

                                    # Calcula o julgamento
                                    ind = rates.index(key)
                                    judgment = judges[ind]

                                    if percent < 0.50:  # Se a porcentagem for menor quee 50%, nenhum teve a maioria
                                        judgment = "Nenhum voto atingiu a maioria"
                                        votetxt = f"{total} votos contados ao total"
                                    else:
                                        votetxt = f"{percent * 100:.2f}% de {total} votos"  # Se não, atingiu

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

                    assholes = 0  # Número de votos babacas
                    commoners = 0  # Número de votos "comuns"
                    total_ac = 0  # Total de votos babacas e comuns
                    # Calcula os babacas e põe informações na tabela
                    for k, v in assholecount.items():
                        votxt += f"{k} | {v} | {percents[k]}%\n"
                        if total >= 1:
                            if k in config["asshole"] or k in config['not_asshole']:
                                total_ac += v

                    # Adicionar os comentários ignorados
                    votxt += f"\n\n**Comentários inválidos: {invalid}**\n"
                    if submission.approved:
                        votxt += "\n*O post foi verificado e aprovado pela moderação, portanto votos FANFIC e OT são desconsiderados*.\n"

                    # Pega a porcentagem de votos babacas e votos não babacas
                    if total_ac >= 1:
                        for k, v in assholecount.items():
                            if k in config["asshole"]:
                                assholes += (v / total_ac) * 100
                            elif k in config["not_asshole"]:
                                commoners += (v / total_ac) * 100

                    points = int(((assholes - commoners) + 100) * 5)  # Por fim, calculado os pontos de babaquice

                    # Adiciona no corpo do texto
                    ftxt += f"\n# Nível de babaquice: {points / 10:.2f}%"
                    timeval = "\n\nÚltima análise feita em: " \
                            f"{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n "  # Última analise...
                    etxt = votxt + timeval + etxt  # Junta várias partes do corpo do comentário

                    current_flair = submission.link_flair_template_id
                    try:
                        selected_flair = config["flairs"][key][0]
                    except KeyError:
                        selected_flair = ""
                    not_avaliable_flair = config["flairs"]["NOT_AVALIABLE"][0]
                    inconclusive_flair = config["flairs"]["INCONCLUSIVE"][0]

                    changed_flair = True

                    if percent >= 0.5 and total > 0:

                        # Verifica se a flair já não foi aplicada. Só aplica se for diferente
                        if current_flair != selected_flair and selected_flair != "":
                            submission.flair.select(selected_flair)  # Seleciona a flair se tiver uma 
                        else:
                            changed_flair = False
                            
                        if key in ["FANFIC", "OT"]:  # Se o voto mais top tiver em um desses dois ai...
                            if not submission.approved:
                                # Remover se o numero de votos for maior que o numero especificado no config
                                if total >= config["remove_votes"]:
                                    removes = open(f"{config['list_path']}/rid", "r").readlines()  # Checa a lista de remoções

                                    indx = -1
                                    for sub in removes:
                                        indx += 1
                                        removes[indx] = sub.strip()

                                    # if submission.id not in removes and total > 3:  # Se a submissão não tiver na lista de remoção e o total for maior que 1 (a lista ainda nn foi gravada)

                                    # Reporta a submissão e adiciona lista de remoções
                                    
                                    reason = reasons["FAKE_OT"]
                                    #submission.mod.remove(mod_note=f"{reason['note']}", spam=False)
                                    submission.report("Post suspeito de ser FANFIC/OT.")
                                    submission.reply(body=f"{reason['body']}")
                                    tools.logger(tp=4, sub_id=submission.id, reason="VIolação")
                                    open(f"{config['list_path']}/rid", "a").write(f"{submission.id}\n")
                                else:
                                    submission.flair.select(config["flairs"]["NOT_AVALIABLE"][0])
                            else:
                                if current_flair != not_avaliable_flair:
                                    submission.flair.select(not_avaliable_flair)
                                    ftxt = f"### " \
                                            f"Post marcado como FANFIC/OT mas aprovado pela moderação"
                                else:
                                    changed_flair = False
                    # Se a porcaentagem está fora da média, seleciona a flair de fora da média
                    elif percent < 0.5 and total > 0:
                        if current_flair != inconclusive_flair:
                            submission.flair.select(inconclusive_flair)
                        else:
                            changed_flair = False
                    elif total == 0:  # Se o total for exatamente zero, a de não disponível
                        if current_flair != not_avaliable_flair:
                            submission.flair.select(config["flairs"]["NOT_AVALIABLE"][0])
                        else:
                            changed_flair = False

                    if changed_flair:
                        flairchanges += f"\n* Flair de https://www.reddit.com/{submission.id} é '{judgment}'"
                        tools.logger(2, ex=f"Flair editada em {submission.id}")

                    # Adiciona a justificativa no corpo do bot
                    ebotxt = botxt
                    ebotxt += f"\n\nDe acordo com u/{submission.author}, o motivo dele se achar ou não um babaca é esse:\n\n"
                    for _ in range(0, 3):  # Tentar 3 vezes para caso de erro
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
                            fullbody = ftxt + ebotxt + etxt  # Cola as partes do comentário
                            if ">!NOEDIT!<" not in bd:  # Se não tiver ">!NOEDIT!<"

                                com.edit(
                                    body=fullbody)  # Edita o comentário do placar
                                tools.logger(1, sub_id=submission.id)
                                edits += f"\n* Comentário do bot editado em https://www.reddit.com/{submission.id}\n"

                    ftxt = f"# Veredito atual:" \
                        f" Não disponível \n\nÚltima atualização feita em: " \
                        f"{datetime.datetime.now().strftime('%d/%m/%Y às %H:%M')}\n\n "

                    tmr_exceptions = 0 # Reseta o wait time se tudo deu certo
                except (prawcore.exceptions.TooManyRequests, praw.exceptions.RedditAPIException):
                    sleep_time = 10 + tmr_exceptions # Tempo de espera total
                    tools.logger(tp=5, ex=f"Too many requests! esperando {sleep_time} segundos...", bprint=False)

                    if sleep_time > 600:
                        tools.logger(tp=5, exx="O acesso a api está negado?", bprint=True)
                        exit(-1)
                    
                    time.sleep(sleep_time)

                    tmr_exceptions += 1

            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(runtime, atime, btime)  # Coloca o runtime total da função
        except Exception as e:
            tools.logger(5, ex=traceback.format_exc())


# Função de backup
def backup():
    already_run = False
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            current_time = datetime.datetime.now().strftime('%H:%M')
            backup_path = config['backup']['path']
            # Só faz backup em determinados temopos
            if (current_time in config["backup"]["time"] and not already_run) or args.b in "SsYy":
                folder = f"{backup_path}/{datetime.datetime.now().strftime('%Y-%m-%d/%H-%M-%S')}"  # Pega a pasta para salvar o backup
                src_list = [".", config_path, config["list_path"]]  # O sources
                for src in src_list:
                    shutil.copytree(src, f"{folder}/{src.split('/')[-1] if src != '.' else 'Main'}",
                                    ignore=shutil.ignore_patterns("venv", "__", "pyenv", "Backups"), dirs_exist_ok=True)  # Copia a árvore de pastas
                #tools.logger(2, bprint=False, ex="Backup realizado")

                # Deletar os backups dos dias mais antigos
                folders = os.listdir(backup_path)
                max_days = config["backup"]["max_days"]

                if len(folders) > max_days:
                    index = 0
                    
                    # Colocar o path nos indexes das pastas
                    for f in folders:
                        folders[index] = os.path.join(backup_path, f)
                        index += 1

                    # Tirar os mais recentes da lista de acordo com max_days
                    for _ in range(0, max_days):
                        del folders[-1]

                    # Excluir os que restaram
                    for f in folders:
                        shutil.rmtree(f)

                already_run = True
            else:
                already_run = False
        except Exception:
            print(traceback.format_exc())
        time.sleep(config["sleep_time"]["backup"])
        btime = datetime.datetime.now().timestamp()


# Limpador de logs
def clearlog(non_automatic=False):
    while True:
        current = f"{datetime.datetime.now().hour}:{datetime.datetime.now().minute}"

        if current in config["clear_log"]:
            open(f'{config["list_path"]}/log', "w+").write("")
            time.sleep(60)

        if non_automatic:
            open(f'{config["list_path"]}/log', "w+").write("")
            break

        time.sleep(0.1)


# Verificador de paredes de texto
def sub_filter():
    reddit.validate_on_submit = True
    while True:
        atime = datetime.datetime.now().timestamp()
        try:
            subcount = 0
            submissons = reddit.subreddit(config["subreddit"]).new(limit=int(config["submissions"]))  # Pega subs
            tmr_exceptions = 0
            for submission in submissons:
                is_removed = False
                try:
                    timestmp = datetime.datetime.now().timestamp() - config[
                        "break_time"]  # Calcula o quaõ velho o post tem que ser para ser ignorado

                    if submission.created_utc <= timestmp:
                        break  # quebra o loop se o tempo de agora - x dias for maior que o tempo que criado.

                    time.sleep(config["sleep_time"]["textwall"])
                    subcount += 1
                    subid = submission.id

                    sublist = tools.getfiletext(open(f"{config['list_path']}/rid", "r"))  # Pega a lista de remoções
                    indx = -1

                    for i in sublist:
                        indx += 1
                        sublist[indx] = i.strip()

                    
                    keywords = tools.getfiletext(open(f"{config['list_path']}/keywords.txt", "r"))  # Palavras de filtro

                    subcount += 1

                    sublist_com = tools.getfiletext(open(f"{config['list_path']}/cid", "r"))  # Pega a lista de remoções
                    indx = -1

                    submission.comment_sort = 'new'  # Filtra os comentários por novos
                    submission.comments.replace_more(limit=None)
                    comments = submission.comments.list()

                    # Iteração pela lista de comentários
                    for com in comments:
                        time.sleep(config["sleep_time"]["filter_sub"])
                        if com.id not in sublist_com:
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
                    
                    time.sleep(config["sleep_time"]["filter_sub"])
                    if subid not in sublist and not submission.approved:  # Se o submissão não tiver na lista de subs...
                        remove_replies = [] # Todos os comentários de remoção do bot
                        try:
                            body = submission.selftext  # Pega o corpo do texto
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

                        if body != "":  # Se o corpo for diferente de ""
                            for i in body:
                                index += 1
                                chars += 1

                                # Quantas frases tem
                                if i in [".", "?", "!", " "]:
                                    sentences += 1

                                paragraph_cond = False
                            
                            # Tentativa de contar os paragrafos de um jeito melhor
                            split_body = body.split("\n\n")
                            paragraphs = len(split_body)
                        else:
                            # Se não, é zero!
                            paragraphs = 0
                            sentences = 0
                        
                        owner = config["info"]["owner"]

                        min_paragraphs = config["text_filter"]["min_paragraphs"]
                        min_sentences = config["text_filter"]["min_sentences"]
                        max_body = config["text_filter"]["max_body"]
                        min_body = config["text_filter"]["min_body"]
                        # Remove a publicação suspeita de parede de texto.
                        if (paragraphs < min_paragraphs or
                                sentences < min_sentences or
                                len(body) > max_body or
                                len(body) < min_body):
                        
                            reason = reasons['TEXTWALL']
                            submission.mod.remove(mod_note=reason['note'], spam=False)
                            reasonstr = f"Post caiu no filtro de parede de texto e por isso foi removido. Arrume e reposte. Confira os critérios analizados:\n\n"

                            # Adicionar as condicionais e seus valores booleanos
                            conds = [f"* Tem o número minimo de paragrafos? {'sim' if paragraphs >= min_paragraphs else 'não'} (Mínmo: {min_paragraphs})", 
                                    f"* Tem o número minimo de frases? {'sim' if sentences >= min_sentences else 'não'} (Mínmo: {min_sentences})", 
                                    f"* Menor que o número máximo de caractéres? {'sim' if len(body) <= max_body else 'não'} (Máximo: {max_body})", 
                                    f"* Tem o número mínimo de caractéres? {'sim' if len(body) >= min_body else 'não'} (Mínimo: {min_body})"]
                            for x in range(0, len(conds)):
                                reasonstr += conds[x]+"\n"

                            submission.reply(body=reasonstr + f"\n\nParágrafos: {paragraphs}\n\nFrases: {sentences}\n\nCaractéres: {chars}\n\nCaso tenha sido um erro, fale com a [moderação](https://www.reddit.com/message/compose?to=r%2F{config['subreddit']}).\n\n>!NOEDIT!<.")
                            tools.logger(tp=4, sub_id=subid, reason="Parede de texto")


                            open(f"{config['list_path']}/rid", "a").write(f"{subid}\n")      

                        # Olhar os regexes
                        if config["text_filter"]["filter_human"]:
                            # Idade
                            remove = False
                            reason_raw = f"O post foi removido pois ele não possui ?. Coloque a idade e o genero no post seguindo o padrão 'idade genero' e reposte. Coloque a idade como um número e o genero como uma dessas letras: 'H', 'M', 'NB'. Exemplo: 18 H."
                            reason = ""
                            if not tools.match("age", body):
                                reason = reason_raw.replace("?", "idade")
                                remove = True
                            
                            if not tools.match("gender", body):
                                reason = reason_raw.replace("?", "gênero")
                                remove = True

                            if tools.match("phone", body):
                                remove = True
                                reason = f"Sua publicação foi removida pois ela possui um número de telefone, logo pode ser spam ou uma tentativa de doxxing."

                            if tools.match("email", body):
                                remove = True
                                reason = f"Sua publicação foi removida pois ela possui um email, logo pode ser spam ou uma tentativa de doxxing."

                            if tools.match("cpf", body):
                                remove = True
                                reason = f"Sua publicação foi removida pois ela possui um CPF."

                            if tools.match("url", body):
                                remove = True
                                reason = f"Sua publicação foi removida pois ela possui um link. É proibido qualquer spam no subreddit."

                            if remove:
                                submission.mod.remove(mod_note="Sem idade", spam=False)
                                submission.reply(body=reason+f"\n\nCaso tenha sido um erro, fale com a [moderação](https://www.reddit.com/message/compose?to=r%2F{config['subreddit']}).\n\n>!NOEDIT!<")
                                open(f"{config['list_path']}/rid", "a").write(f"{subid}\n")

                        karma_filter = config["text_filter"]["karma_checker"]

                        if karma_filter["enabled"]:
                            karma = submission.author.comment_karma + submission.author.link_karma
                            if karma < karma_filter["min"]:
                                sub_created = submission.created_utc
                                now = datetime.datetime.now().timestamp()

                                if now - sub_created < karma_filter["timeout"]:
                                    submission.mod.remove(mod_note="Sem karma", spam=False)
                                    submission.reply(body=f"Seu post foi removido pois você não possui karma suficiente para postar nesse subreddit. Envie um modmail para a [moderação](https://www.reddit.com/message/compose?to=r%2F{config['subreddit']}) para revisar o seu post.\n\n>!NOEDIT!<")
                                else:
                                    if karma <= karma_filter["after_timeout_report_when"]:
                                        # Reportar
                                        submission.mod.report(
                                            mod_note=f"Post suspeito. Usuário possui {karma} de karma."
                                        )

                                open(f"{config['list_path']}/rid", "a").write(f"{subid}\n")
                    tmr_exceptions = 0
                except (prawcore.exceptions.TooManyRequests, praw.exceptions.RedditAPIException):
                    sleep_time = 10 + tmr_exceptions # Tempo de espera total
                    tools.logger(tp=5, ex=f"Too many requests! esperando {sleep_time} segundos...", bprint=False)

                    if sleep_time > 600:
                        tools.logger(tp=5, exx="O acesso a api está negado?", bprint=True)
                        exit(-1)
            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(sub_filter, atime, btime)
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
            tmr_exceptions = 0
            for submission in submissons:
                try:
                    timestmp = datetime.datetime.now().timestamp() - config[
                        "break_time"]  # Calcula o quaõ velho o post tem que ser para ser ignorado

                    if submission.created_utc <= timestmp:
                        break  # quebra o loop se o tempo de agora - x dias for maior que o tempo que criado.
                    
                    reasonings = json.load(open(f"{config['list_path']}/reasoning/reasonings.json", "r"))

                    time.sleep(config["sleep_time"]["justification"])
                    subcount += 1
                    subid = submission.id
                    reason = ""

                    # Contiunuar
                    submission.comment_sort = 'new'  # Filtra os comentários por novos
                    submission.comments.replace_more(limit=None)
                    comments = submission.comments.list()
                    didOPans = False  # se o op respondeu
                    breakparent = False

                    for com in comments:
                        if com.author == api["username"]:  # Se o autor do comentário for o bot.
                            # Verificar se o autor do post respondeu
                            comreplies = com.replies
                            for reply in comreplies:  # Para cada resposta do comentário
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
                                        reason = reply.body  # O motivo é o corpo da resposta
                                        breakparent = True
                                        break

                                if breakparent:
                                    break

                    # Para fins de evitar flood de remoções, verifica se o id não está na lista de ignorados
                    igl = tools.getfiletext(open(f"{config['list_path']}/ignore_list", "r"))

                    if didOPans:
                        if subid in igl:
                            reason = "Post postado antes de precisar justificar."
                        open(f"{config['list_path']}/jid", "a").write(f"{subid}\n")

                        # Salva o motivo
                        reasonings[subid] = reason

                        rstr = json.dumps(reasonings, indent=4)
                        open(f"{config['list_path']}/reasoning/reasonings.json", "w").write(rstr)
                    tmr_exceptions = 0
                except (prawcore.exceptions.TooManyRequests, praw.exceptions.RedditAPIException):
                    sleep_time = 10 + tmr_exceptions # Tempo de espera total
                    tools.logger(tp=5, ex=f"Too many requests! esperando {sleep_time} segundos...", bprint=False)

                    if sleep_time > 600:
                        tools.logger(tp=5, exx="O acesso a api está negado?", bprint=True)
                        exit(-1)
            btime = datetime.datetime.now().timestamp()
            tools.log_runtime(justification, atime, btime)
        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


def stat():  # Estatisticas do subreddit
    while True:
        sql = tools.db_connect(args=args)

        cursor = sql.cursor()
        try:
            

            add = False
            subr = reddit.subreddit(config["subreddit"])
            reddit.validate_on_submit = True

            sql.commit()
            cursor.execute("SELECT max(id) FROM statistics")
            last_id = int(cursor.fetchall()[0][0])

            # Checar se ja não foi checado e adicionar caso tenha passado uma hora no arquivo csv
            sql_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            subs = subr.subscribers

            cursor.execute(f"SELECT members FROM statistics WHERE id={last_id};")

            last_members = int(cursor.fetchall()[0][0])
            growt = subs - last_members
            growt_perc = ((subs - last_members) / last_members) * 100

            cursor.execute(
                f"INSERT INTO statistics (`id`, `owner`, `datetime`, `members`, `growt`, `growt_percent`) VALUES ({last_id + 1}, {apid}, '{sql_time}', {subs}, {growt}, {growt_perc})")

            sql.commit()
            time.sleep(config["sleep_time"]["stat"])
        # if add:
        #    reddit.subreddit(f"{config['log_subreddit']}").submit(title=f"{date} {int(hour)-1 if int(hour) >= 1 else '23'}-{ctime} - GROWT", selftext=f"{subs} (CRESCIMENTO: {growt})")

        #tools.log_runtime(stat, atime, btime)

        except Exception:
            tools.logger(tp=5, ex=traceback.format_exc())


if __name__ == '__main__':
    tools.clear_console(), 
    prep.begin(config)

    # Carrega as funções
    funcs = [[runtime], [sub_filter], [justification], [backup], [clearlog], [stat]]

    # Inicializa os processos
    indx = 0
    processes = []
    for x in funcs:
        processes.append(multiprocessing.Process(target=x[0], name=x[0].__name__))

    pids = [os.getpid()]

    index = -1
    # E os bota para rodar de segundo plano
    func_total = 0  # total de milisegundos na inicialização da função

    # Antes de começar, printa o PID da thread principal
    print(f"main: {pids[0]}")

    for i in processes:
        func_start = datetime.datetime.now().timestamp()  #ms da função

        index += 1
        i.start()
        pids.append(i.pid)  # Salva os pids  

        func_end = datetime.datetime.now().timestamp()  # ms da função
        func_total += (func_end - func_start) * 1000

        print(
            f"Iniciado processo com o PID {i.pid} para a função {funcs[index][0].__name__}: {(func_end - func_start) * 1000:.0f} ms")

        # Termino do processo de inicializaçãp.

    pids_str = [str(x) for x in pids]
    open(f'{config["list_path"]}/pids', "w+").write("\n".join(pids_str))
    open(f'{config["list_path"]}/main', "w+").write(str(os.getpid()))

    end2 = datetime.datetime.now().timestamp()

    total_main = (((end2 - start2) + (
                end1 - start1)) * 1000)

    print(
        f"main: {total_main:.0f} ms. ({total_main - (func_total):.0f} ms de inicialização e {func_total:.0f} ms de preparação)")

    # Loop para os comandos (primeiro plano)
    while True:
        try:
            # Try para EOF e erros sem tratamento específico
            inp = input("=> ").upper().split(" ")
            if len(inp) >= 1:
                if inp[0] == "R":  # Se o input do usuário for R, vai simplesmente reccarregar os valores. (Não testado)
                    config = json.load(open('config.json', 'r'))
                    sql.commit()
                    print("Valores recarregados na memória.")
                elif inp[0] == "E":  # E termina o programa.
                    for i in processes:
                        i.terminate()

                    break
                elif inp[0] == "LEAVE":
                    print("Saindo do modo de input.")
                    break
                elif inp[0] == "RESTART":  # Reinicia o programa
                    for i in processes:
                        i.terminate()

                    os.system(f"{config['python']} ./main.py -p {args.p}")
                    break
                elif inp[0] == "MEMORY":  # Calcula a memória utilizada pelos processos
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

                                    print(
                                        f"{funcs[index][0].__name__ if r > 0 else 'main'} ({process.pid}): {mem_qnt:.0f} mb, {cpu:.2f}% CPU")

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
                    cursor.execute(f"SELECT id FROM splashes WHERE owner={apid};")
                    lastid = int(cursor.fetchall()[-1][0])

                    try:
                        cursor.execute(
                            f"INSERT INTO splashes (`id`, `owner`, `text`) VALUES ({lastid + 1}, {apid}, '{str(input('Texto: '))}')")
                    except Exception as e:
                        print(traceback.format_exc())

                    sql.commit()
                elif inp[0] == "INJECT":
                    # O comando inject faz injeções python ou sql
                    if config["debug"]["injectable"]:
                        while True:
                            if len(inp) > 0:
                                if inp[1] == 'PYTHON':
                                    try:
                                        eval(input("INJECT => "))
                                    except SyntaxError:
                                        print("Saindo!")
                                        break
                                    except Exception as e:
                                        print(traceback.format_exc())
                                elif inp[1] == "SQL":
                                    try:
                                        sql.commit()
                                        injection = input("INJECT => ")

                                        if injection != "EXIT;":
                                            cursor.execute(injection)
                                            output = cursor.fetchall()
                                            print(output)
                                        else:
                                            break
                                    except mysql.connector.Error as e:
                                        print(f"{e}")

                    else:
                        print("Não é possível usar esse comando se 'injectable' for False.")
                elif inp[0] == "SWITCH":
                    if len(inp) > 1:
                        try:
                            agreement = False
                            
                            if inp[1] == "INJECTABLE":
                                uinp = input("Ao alterar esse valor, você concorda sobre os potenciais riscos de segurança. Digite 'Eu concordo' para aceitar.\n=> ")
                                if uinp == "Eu concordo":
                                    if input("Senha do banco de dados: ") == args.p:
                                        agreement = True
                            else:
                                agreement = True

                            if agreement:
                                config["debug"][inp[1].lower()] = not config["debug"][inp[1].lower()]   
                                print("Alterado valor temporariamente.")
                            else:
                                print("Recusado.")
                        
                        except KeyError:
                            print("Erro! chave não existnte.")
                elif inp[0] == "LICENSE":
                    print(f"""
        {config["info"]["name"]}  Copyright (C) {datetime.datetime.now().year}  {config["info"]["author"]}
    This program comes with ABSOLUTELY NO WARRANTY;
    This is free software, and you are welcome to redistribute it
    under certain conditions; Digite 'ABOUTME' para mostrar a licença completa.""")
                elif inp[0] == "ABOUTME":
                    license = open("./LICENSE.md", "r").readlines()

                    for line in license:
                        time.sleep(0.05)
                        print(line, end="")
                elif inp[0] == "CLEAR":
                    tools.clear_console()
                elif inp[0] == "CLEARLOG":
                    clearlog(0, non_automatic=True)
                elif inp[0] == "":
                    print("Nenhum comando a executar.")
                else:
                    print(f"O comando {inp[0]} não é válido.")
        except EOFError:
            print("Fim do arquivo de input. Encerrando loop de comandos.")
            break


    # Loop while que acontece em caso de EOFError ou qualquer outro erro que termine o loop de comandos.
    while True:
        time.sleep(0.5)
else:
    print("Esse programa não pode ser usado como biblioteca. Rode diretamente.")
        
