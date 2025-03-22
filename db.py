import json
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy import text
engine = create_engine("mysql+mysqldb://remote:yemmiadem@51.159.159.63/test")

def init_db():
    connection = engine.connect()
    connection.execute(text('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id VARCHAR(128) PRIMARY KEY ,
            status Text,
            step Text,
            result JSON
        )
    '''))
    connection.commit()
    connection.close()

init_db()

#
def update(task_id, step, status, result = json.dumps({})):
    parameters = {'task_id':task_id, 'step':step, 'status':status, 'result':result}
    cursor = engine.connect()

    cursor.execute(text("INSERT IGNORE INTO tasks (task_id, step, status, result) "
                   "VALUES (:task_id, :step, :status, :result)"
                   "ON DUPLICATE KEY UPDATE step = :step, status=:status, result=:result"),
                   parameters)

    cursor.commit()
    cursor.close()

def get(task_id):
    parameters = {'task_id':task_id}
    connection = engine.connect()

    cursor = connection.execute(text("SELECT * FROM tasks where task_id = :task_id"),
                   parameters)

    result = cursor.fetchone()
    if result is None:
        id, pr, st, r = None, None, None, None
    else:
        id, pr, st, r = result
    cursor.close()
    connection.commit()
    connection.close()
    return {
        'id': id,
        'progress': pr,
        'step': st,
        'result': r
    }

# print(get('09b5dd74-201f-443a-b605-ef4f9751c98c'))