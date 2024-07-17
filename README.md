
## Lucasbot

Lucasbot é um bot feito para o subreddit r/EuSouOBabaca utilizando `python` e a biblioteca `praw`. Ele também usa um servidor `mysql` para algumas tarefas como geração de estatísticas e algumas configurações básicas.

## Requisitos mínimos
|Requisito|Valor  |
|--|--|
| Python |3.9  |
| Bibliotecas|`praw, psutil, mysql-connector-python`  |
| RAM|512 mb  |
| CPU|1 núcleo  |
| Disco|600 mb livres |

## Como rodar
Depois de instalar as bibliotecas necessárias usando `python3 -m pip install -r requirements.txt`, basta configurar o bot usando o modelo em MODELOS e depois `python3 main.py -p "Senha do banco de dados"`.

 ![Terminal com o bot rodando](https://i.imgur.com/uyYvogh.png)
 ## Comandos
 
|Comando|Output  |
|--|--|
| R | Recarrega valores na memória |
| E| Termina o programa |
| LEAVE| Sai do input de comandos. Pode ser útil para manter a segurança. |
| MEMORY| Calcula a memória e o CPU usado em cada processo. ENTER para atualizar, digite qualquer coisa e aperte ENTER para sair do loop. |
| LOGSTREAM | Mostra o registro do log em tempo real |
| ADDSPLASH | Adiciona um texto debaixo do indicador de veredito |
| INJECT SQL ou PYTHON | Se injectable em config.json for True, permite executar códigos sql ou python no programa |
| SWITCH Chave em 'debug' | Altera temporariamente o valor presente no dicionário 'debug' em config.json |
| LICENSE | Texto de licença |
| ABOUTME | About me |
