# 1 - O que é?

Lucas Bot é um bot feito para o subreddit "r/EuSouOBabacaBOT" de forma a suprir a necessidade cálculo de votos das publicações.

Ele conta os votos com base no arquivo `config.json` encontrado na mesma pasta que o arquivo principal `main.py`.
# 2 - Estrutura básica

Primeiro, o programa pega as credenciais de login no arquivo `api.json`. O arquivo se parece com isso:

    {
        "clientid": "clientid",
        "clientsecret": "secret",
        "rusername": "username",
        "password": "password",
        "useragent": "Mozilla/5.0 (Linux; Android 10; SM-G996U Build/QP1A.190711.020; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Mobile Safari/537.36"
    }
*PS: Ao rodar o bot, crie um arquivo com esse nome e essa estrutura!*

Em seguida, ele carrega o arquivo de configuração `config.json`. Cada campo tem seu significado:

* `python`: Esse campo serve para armazenar o comando do python3 na máquina que roderá o script. Ele será usado no comando de reiniciar o programa.
* `info`: Armazena as informações do programa. O subcampo `name` é o nome do programa; O campo `version` é a versão; `creator` se refere ao criador (Por favor, se for trocar pelo menos me dê os créditos do código base :( ); O campo `github` serve para armazenar o link do repositório.
* `upper_text`: O texto que fica debaixo da última atualização.
* `submissions`: O número de posts que o bot vai pegar de uma vez.
* `subreddit`: O subreddit alvo.
* `backup`: Onde será colocado o backup dos arquivos do bot.
* `clear_log`: Quanto tempo vai demorar em segundos para o log ser limpo.
* `flairs`: Onde fica armazenado os votos. Cada subcampo é um voto; O valor é um array de 3 items, sendo o primeiro indice o id da flair - o segundo índice o itpo de voto e, o terceiro a descrição do bot.
* `flairs_ignore`: Tem votos que é apenas para ocasiões especiais, nesse caso deverá ser colocado esses flairs nesse array.
* `vote_name`: O nome dos votos.
* `text_filter`: Se define o numero minimo de frases e paragráfos, alem do tamanho máximo de caractéres por publicação

Ele pega outro arquivo para quando um post  for removido. É o `reasons.json`, que tem os motivos e o texto deles. Cada motivo é um campo que tem os seguintes subcampos:

* `note`: A nota que justificará os motivos da remoção.
* `body`: O texto que será comentado no post removido ao remover.

Perceba que o texto, no finalzinho, tem uma mensagem geralmente filosófica aleatória. Essas frases são pegas no arquivo `splashes.json`. Esse arquivo é um array de texto basicamente.

# 3 - Comentários

O bot gera dois tipos de comentário. O primeiro é o normal, que aparece contando os bots, que segue um exemplo abaixo de como fica:

    # Veredito atual: Não é o babaca (94.16% de 154 votos)

    Última atualização feita em: 03/06/2023 às 11:36
    
    
    
    **Feliz mês do orgulho LGBT! 🌈**
    
    Vou contar as respostas que as pessoas dão nesse post! Pra ser contado, responda com essas siglas o post:
    
    NEOB - Não é o babaca (e o resto sim)
    
    EOB - É o babaca
    
    EOT - É um trouxa, um otário
    
    NGM - Ninguem é o babaca
    
    INFO - Falta informação para julgar
    
    TEOB - Todo mundo é o babaca
    
    **Votos especiais**
    
    FANFIC - Sinalizar o post como falso
    
    OT - Sinalizar como fora do tópico
    
    META - Publicação META
    
    
    
    ##Nota: Pode demorar cerca de 2 horas para atualizar!
    
    
    # Tabela de votos
    Voto | Quantidade | %
    :--:|:--:|:--:
    NEOB | 145 | 94.16%
    EOB | 0 | 0.00%
    EOT | 1 | 0.65%
    NGM | 0 | 0.00%
    INFO | 0 | 0.00%
    TEOB | 0 | 0.00%
    FANFIC | 8 | 5.19%
    OT | 0 | 0.00%
    META | 0 | 0.00%
    
                                
    *Se a sua vida pode mudar uma vez, ela pode mudar novamente. (Sugerido por Ydnam_Mandy).* 
    *Lucas Bot v3 - by [JakeWisconsin](https://www.reddit.com/u/JakeWisconsin).*
    *Veja meu código fonte: [Código fonte](https://github.com/BrenoMartinsDeOliveiraVasconcelos/EuSouOBabacaBOT).*

O reddit funciona sob a linguagem markdown, então o comentário ficará estilizado conforme o markdown.

O segundo tipo é quando uma publicação é removida. 

# 4 - Controlando o bot

Por agora, existem apenas 3 comandos para controlar o bot. Mais serão adicionados em breve.

**Comando** | **Resultado**
--|:--:
R | Recarrega os arquivos json
E | Desliga o bot
RESTART | Recarrega o bot
MEMORY | Mostra o consumo de memória em megabytes

# 5 - Requisitos mínimos

**Tipo** | **Valor**
--|--
RAM | 512 mb
CPU | 1 núcelo ou superior
Python | 3.7+
Bibliotecas Python | praw, prawcore, psutil
Internet | Sim
Sistema operacional | Qualquer sistema compatível com Python 3.9 e com acesso a internet 

Para executar, basta criar o arquivo conforme o primeiro tópico e rodar o arquivo `main.py`.