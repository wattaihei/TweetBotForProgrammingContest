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


def getCFsolved(consideringCount):
    # API から提出記録を抽出
    resultUrl = "https://codeforces.com/api/user.status?handle={0}&from=1&count={1}".format(username, consideringCount)
    r = requests.get(resultUrl)
    submittionData = json.loads(r.text)

    # id -> (title, difficulty, solvedTime)
    AC = {}
    for submittiondata in submittionData["result"]:
        if submittiondata["verdict"] == "OK":
            problemdata = submittiondata["problem"]
            problemId = str(problemdata["contestId"]) + "/" + problemdata["index"]
            if not problemId in AC:
                AC[problemId] = [
                    problemId,
                    problemdata["name"],
                    problemdata["rating"] if "rating" in problemdata else None,
                    submittiondata["creationTimeSeconds"]
                ]
            elif submittiondata["creationTimeSeconds"] < AC[problemId][3]:
                AC[problemId][2] = submittiondata["creationTimeSeconds"]
    
    # すでにあるものを取り出す
    connection = sqlite3.connect(DatabasePath)
    cursor1 = connection.cursor()
    cursor1.execute("SELECT id FROM cftasks")
    alreadyExistIds = set([a[0] for a in cursor1.fetchall()])

    needToInsert = []
    newIds = []
    for Id, content in AC.items():
        if not Id in alreadyExistIds:
            needToInsert.append(content)
            newIds.append(Id)
        
    cursor2 = connection.cursor()
    cursor2.executemany("INSERT INTO cftasks (id, title, difficulty, solvedTime) VALUES (?,?,?,?)", needToInsert)

    connection.commit()
    connection.close()

    return newIds



# 開いた問題を記録
def collectOpenedData(timestamp):
    # Chrome開いたままだとRockされてるのでコピーしておく
    subprocess.run(['cp', HistoryPath, CopyPath])

    # 集める
    connection = sqlite3.connect(CopyPath)
    cursor = connection.cursor()

    cursor.execute("SELECT DISTINCT url, last_visit_time, visit_count FROM urls WHERE url LIKE 'https://codeforces.com/problemset/problem/%/%' OR url LIKE 'https://codeforces.com/contest/%/problem/%'".format(timestamp))

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
        urlList = list(url.split("/"))
        if url.startswith("https://codeforces.com/contest"):
            Id = urlList[-3] + "/" + urlList[-1]
        else:
            Id = urlList[-2] + "/" + urlList[-1]
        if Id in ret_dic:
            if ret_dic[Id] is None:
                ret_dic[Id] = ChromeTimestampToUnix(timestamp)
            elif not timestamp is None:
                ret_dic[Id] = min(ret_dic[Id], ChromeTimestampToUnix(timestamp))
        else:
            ret_dic[Id] = ChromeTimestampToUnix(timestamp)
    #print(ret_dic)
    return ret_dic

# openしたタイムスタンプでupdate
def exportOpenedData(newIds, openedDic):
    Embedding = []
    for Id in newIds:
        if Id in openedDic:
            Embedding.append((openedDic[Id], Id))
    
    connection = sqlite3.connect(DatabasePath)
    cursor = connection.cursor()
    cursor.executemany("UPDATE cftasks SET openedTime = ? WHERE id = ?", Embedding)
    connection.commit()
    connection.close()


def main():
    newIds = getCFsolved(100)
    data_withoutId = collectOpenedData(0)
    data_dic = TaskurlToId(data_withoutId)
    exportOpenedData(newIds, data_dic)


if __name__ == "__main__":
    main()