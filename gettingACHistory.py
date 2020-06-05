import sqlite3
import subprocess
import requests
import json
from datetime import datetime

HistoryPath = "/Users/taihei/Library/Application Support/Google/Chrome/Default/History"
CopyPath = "/Users/taihei/BotProject/History"
ProblemPath = "/Users/taihei/BotProject/problemData.sqlite"
DatabasePath = "/Users/taihei/BotProject/submitData.sqlite"
username = "wattaihei"

# 開いた問題を記録
def collectOpenedData(timestamp):
    # Chrome開いたままだとRockされてるのでコピーしておく
    subprocess.run(['cp', HistoryPath, CopyPath])

    # 集める
    connection = sqlite3.connect(CopyPath)
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT url, last_visit_time, visit_count FROM urls WHERE last_visit_time > {} AND url LIKE 'https://atcoder.jp/contests/%/tasks/%'".format(timestamp))

    retData = cursor.fetchall()
    connection.close()

    return retData


# Chrome Historyに入ってるのは変なやつなので変換
# http://www.mirandora.com/?p=697
def ChromeTimestampToUnix(ChromeTimestamp):
    return int(ChromeTimestamp/1000000-11644473600) if not ChromeTimestamp is None else None


# URLからidを切り取る
# 2つある場合timestamp が小さい方を取得
def TaskurlToId(Data):
    ret_dic = {}
    for url, timestamp, visit_count in Data:
        if visit_count != 1:
            timestamp = None
        Id = list(url.split("/"))[-1]
        if Id in ret_dic:
            if ret_dic[Id] is None:
                ret_dic[Id] = ChromeTimestampToUnix(timestamp)
            elif not timestamp is None:
                ret_dic[Id] = min(ret_dic[Id], ChromeTimestampToUnix(timestamp))
        else:
            ret_dic[Id] = ChromeTimestampToUnix(timestamp)
    return list(ret_dic.items())



# contest_idなどを入手
def convertOpenedData(Data):
    retData = []
    connection = sqlite3.connect(ProblemPath)
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM problems")
    # dicに変換しとく
    dic = {}
    for Id, title, contest_id, point, difficulty, is_experimental in cursor.fetchall():
        dic[Id] = (title, contest_id, point, difficulty, is_experimental)
    
    for Id, openedTime in Data:
        if Id in dic:
            title, contest_id, point, difficulty, is_experimental = dic[Id]
            retData.append((Id, title, contest_id, point, difficulty, is_experimental, openedTime))
    cursor.close()
    connection.close()
    return retData

# 収納
def exportOpeneddata(Data):
    connection = sqlite3.connect(DatabasePath)
    cursor1 = connection.cursor()
    cursor1.execute("SELECT id FROM tasks")
    alreadyExistIds = set([a[0] for a in cursor1.fetchall()])

    needToInsert = []
    for content in Data:
        if not content[0] in alreadyExistIds:
            needToInsert.append(content)

    cursor2 = connection.cursor()
    cursor2.executemany("INSERT INTO tasks (id, title, contest_id, point, difficulty, is_experimental, openedTime) VALUES (?,?,?,?,?,?,?)", needToInsert)
    connection.commit()
    connection.close()




def main():
    timestamp = 0
    data_withoutid = collectOpenedData(timestamp)
    data_withid = TaskurlToId(data_withoutid)
    data_withcolumn = convertOpenedData(data_withid)
    exportOpeneddata(data_withcolumn)


if __name__ == "__main__":
    main()