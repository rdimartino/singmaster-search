from peewee import *
from datetime import datetime

DEFAULT_FLAG = 0
INFO_FLAG = 1
POSITIVE_FLAG = 10
SUCCESS_FLAG = 100
WARNING_FLAG = -10
DANGER_FLAG = -100

db = MySQLDatabase('pascal', user='pascal', host='localhost')


class Center(Model):
    center_id = PrimaryKeyField()
    diagonal = IntegerField()
    value = TextField()
    centerSearchTime = FloatField(null=True)
    matchCount = IntegerField(default=0)
    ts = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Result(Model):
    result_id = PrimaryKeyField()
    target = ForeignKeyField(Center, to_field='center_id', null=True)
    diagonal = IntegerField()
    index = TextField()
    match = BooleanField()
    binarySearchExpandCount = IntegerField()
    binarySearchNarrowCount = IntegerField()
    searchTime = FloatField()
    ts = DateTimeField(default=datetime.now)

    class Meta:
        database = db


class Log(Model):
    log_id = PrimaryKeyField()
    ts = DateTimeField(default=datetime.now)
    header = CharField(10, default='info')
    message = TextField()
    flag = IntegerField(default=INFO_FLAG)

    class Meta:
        database = db


def createLog():
    db.drop_table(Log, fail_silently=True)
    db.create_table(Log)
    Log.create(message='Log created', header='reset', flag=DANGER_FLAG)


def logLine(message, header='info', flag=INFO_FLAG):
    Log.create(message=message, header=header, flag=flag)


def pullLog():
    last_log = Log.select(fn.Max(Log.ts)).where(Log.flag == DANGER_FLAG).scalar()
    log_lines = Log.select().where(Log.ts >= last_log).order_by(Log.ts.asc())
    return [{'message': l.message, 'header':l.header, 'flag': l.flag ,'ts': l.ts.strftime('%Y-%m-%d %H:%M:%S')} for l in log_lines]


def pullVizData():
    last_log = Log.select(fn.Max(Log.ts)).where(Log.flag == DANGER_FLAG).scalar()
    center_lines = Center.select().where(Center.ts >= last_log).order_by(Center.diagonal.asc())
    return [{'center': c.diagonal, 'centerSearchTime': c.centerSearchTime, 'matchCount': c.matchCount} for c in center_lines]


def recreateTables():
    db.drop_tables([Center, Result], safe=True)
    db.create_tables([Center, Result])


def resumeSearch():
    lastCenter = Result.select(fn.Max(Result.diagonal)).scalar()
    lastCount = Result.select(fn.Count(Result.result_id)).join(Center).where(Center.diagonal == lastCenter).scalar()
    if lastCount == lastCenter - 1:
        resumeCenter = lastCenter + 1
    else:
        unfinishedCenter = Center.select().where(Center.diagonal == lastCenter)
        Result.delete().where(Result.target == unfinishedCenter).execute()
        Center.delete().where(Center.diagonal == lastCenter).execute()
        resumeCenter = lastCenter
    resumeIndices = [1, 1] + [int(d.index) for d in Result.select().join(Center)
                                                         .where(Center.diagonal == resumeCenter - 1)
                                                         .order_by(Result.diagonal.asc())]
    return {'lastCenterIndex': resumeCenter,
            'searchStartIndices': resumeIndices}


def uploadResult(data):
    c = data['center']
    r = data['results']
    db.connect()
    target = Center.create(diagonal=c['diagonal'], value=c['value'], centerSearchTime=c['centerSearchTime'], matchCount=c['matchCount'])
    for row in r:
        row.update({'target': target})
    Result.insert_many(r).execute()
    db.close()