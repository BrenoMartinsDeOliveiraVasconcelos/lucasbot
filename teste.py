import json


reddit_data = json.load(open("/media/breno/Srv/lucasbot/submissions.json"))
reddit_data["submissions"].append({"sdffvsf": "a"})

# Limpar para remover duplicados
list_submissions = reddit_data["submissions"].copy()
already_in = []

indx = -1
for subm in reddit_data["submissions"]:
    indx += 1

    for key in subm.keys():
        if key not in already_in:
            already_in.append(key)
            break
        else:
            # tools.logger(tp=2, ex=f"{key} é duplicado, por isso foi removido.")
            del list_submissions[indx]
            indx -= 1
            break

reddit_data["submissions"] = list_submissions
print(reddit_data)
