import requests
import sqlite3
import json


# 問題が追加されたら回す

HistoryPath = "/Users/taihei/Library/Application Support/Google/Chrome/Default/History"
CopyPath = "/Users/taihei/BotProject/History"
ProblemPath = "/Users/taihei/BotProject/problemData.sqlite"
DatabasePath = "/Users/taihei/BotProject/submitData.sqlite"
username = "wattaihei"

# API から問題のデータを持ってきてDBに保存
# (id, title, contest_id, point, difficulty, is_experimental)
def getProblemData():
    mergedProblemsUrl = "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    r = requests.get(mergedProblemsUrl)
    problemdata = json.loads(r.text)

    # すでにあるidのものを取り出しておく
    connection = sqlite3.connect(ProblemPath)
    cursor1 = connection.cursor()
    cursor1.execute("SELECT id FROM problems")
    alreadyExistIds = set([a[0] for a in cursor1.fetchall()])
    cursor1.close()

    # Insertするデータを持ってくる
    needToInsert = []
    for problemdatum in problemdata:
        if not problemdatum["id"] in alreadyExistIds:
            needToInsert.append((
                problemdatum["id"],
                problemdatum["title"],
                problemdatum["contest_id"],
                problemdatum["point"]
            ))

    cursor2 = connection.cursor()
    cursor2.executemany("INSERT INTO problems (id, title, contest_id, point) VALUES (?,?,?,?)", needToInsert)
    connection.commit()
    cursor2.close()

    connection.close()

# difficulty のデータを持ってきてDBに保存
def getDifficultyData():
    DifficultyUrl = "https://kenkoooo.com/atcoder/resources/problem-models.json"
    r = requests.get(DifficultyUrl)
    problemdata = json.loads(r.text)

    # すでにDifのあるidのものを取り出しておく
    connection = sqlite3.connect(ProblemPath)
    cursor1 = connection.cursor()
    cursor1.execute("SELECT id FROM problems WHERE difficulty IS NOT NULL")
    alreadyDeterminedIds = set([a[0] for a in cursor1.fetchall()])
    cursor1.close()

    # Insertするデータを持ってくる
    needToInsert = []
    for Id, content in problemdata.items():
        if not Id in alreadyDeterminedIds and "difficulty" in content:
            needToInsert.append((content["difficulty"], content["is_experimental"], Id))


    cursor2 = connection.cursor()
    cursor2.executemany("UPDATE problems SET difficulty = ?, is_experimental = ? WHERE id = ?", needToInsert)
    connection.commit()
    cursor2.close()

    connection.close()


getProblemData()
getDifficultyData()
