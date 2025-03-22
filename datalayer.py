import json
from chainlit.data.sql_alchemy import SQLAlchemyDataLayer
from chainlit.element import ElementDict
from models import Messages
from typing import Optional, Dict, List
from chainlit.logger import logger
import chainlit as cl


class DataLayer(SQLAlchemyDataLayer):
    async def update_element(self, element, user_id):
        import aiofiles
        import aiohttp
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_element, user_id={user_id}, element={element.to_dict()}")
        if element.path:
            async with aiofiles.open(element.path, "rb") as f:
                content = await f.read()
        elif element.url:
            async with aiohttp.ClientSession() as session:
                async with session.get(element.url) as response:
                    if response.status == 200:
                        content = await response.read()
                    else:
                        content = None
        elif element.content:
            content = element.content
        else:
            raise ValueError("Element url, path or content must be provided")
        if content is None:
            raise ValueError("Content is None, cannot upload file")

        element_dict = element.to_dict()

        file_object_key = f"{user_id}/{element.id}" + (
            f"/{element.name}" if element.name else ""
        )

        element_dict["url"] = ''
        element_dict["objectKey"] = file_object_key

        element_dict_cleaned = {k: v for k, v in element_dict.items() if v is not None}
        if "props" in element_dict_cleaned:
            element_dict_cleaned["props"] = json.dumps(element_dict_cleaned["props"])

        placeholders = ", ".join(
            f'"{column}"=:{value}' for column, value in zip(element_dict_cleaned.keys(), element_dict_cleaned.keys()))

        query = f'UPDATE elements SET {placeholders} WHERE "id"=$1 AND "threadId"=$2'
        await self.execute_sql(query=query, parameters=element_dict_cleaned)

    async def get_element(self, thread_id: str, element_id: str):
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_element, thread_id={thread_id}, element_id={element_id}")

        query = """SELECT * FROM elements WHERE "threadId" = :thread_id AND "id" = :element_id"""
        parameters = {"thread_id": thread_id, "element_id": element_id}
        element = await self.execute_sql(
            query=query, parameters=parameters
        )
        if isinstance(element, list) and element:
            element_dict = element[0]
            props = element_dict.get("props", "{}")
            return ElementDict(
                id=element_dict["id"],
                threadId=element_dict.get("threadId"),
                type=element_dict["type"],
                chainlitKey=element_dict.get("chainlitKey"),
                url=element_dict.get("url"),
                objectKey=element_dict.get("objectKey"),
                name=element_dict["name"],
                props=props if isinstance(props, dict) else json.loads(props),
                display=element_dict["display"],
                size=element_dict.get("size"),
                language=element_dict.get("language"),
                page=element_dict.get("page"),
                autoPlay=element_dict.get("autoPlay"),
                playerConfig=element_dict.get("playerConfig"),
                forId=element_dict.get("forId"),
                mime=element_dict.get("mime"),
            )
        else:
            return None

    async def update_messages(self, thread_id, msgs: Messages):
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_element, thread_id={thread_id}, messages={msgs.model_dump_json()}")

        parameters = {"thread_id": thread_id, "messages": msgs.model_dump_json()}
        resp = await DataLayer.get_messages(thread_id)
        if resp is None:
            query = """INSERT INTO messages ("threadId", "messages") VALUES (:thread_id, :messages)"""
            await self.execute_sql(query=query, parameters=parameters)
        else:
            query = '''UPDATE messages SET messages= :messages  WHERE "threadId"= :thread_id '''
            await self.execute_sql(query=query, parameters=parameters)

    async def get_messages(self, thread_id: str):
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_element, thread_id={thread_id}")

        query = """SELECT * FROM messages WHERE "threadId" = :thread_id"""
        parameters = {"thread_id": thread_id}
        element = await self.execute_sql(
            query=query, parameters=parameters
        )
        if isinstance(element, list) and element:
            messages_dict = element[0]
            print(messages_dict)
            messages = messages_dict.get("messages", "[{}]")
            msgs = Messages.model_validate(messages)
            return msgs.messages
        else:
            return None

    async def update_tasks(self, thread_id: str, task_id: str):
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_element, thread_id={thread_id}, task_id={task_id}")

        parameters = {
            "thread_id": thread_id,
            "task_id": task_id,
        }  # Remove keys with None values
        columns = ", ".join(f'"{key}"' for key in parameters.keys())
        values = ", ".join(f":{key}" for key in parameters.keys())
        updates = ", ".join(
            f'"{key}" = EXCLUDED."{key}"' for key in parameters.keys() if key not in ["thread_id"]
        )
        query = f"""
            INSERT INTO threads_tasks ({columns})
            VALUES ({values})
            ON CONFLICT ("thread_id") DO UPDATE
            SET {updates};
        """
        await self.execute_sql(query=query, parameters=parameters)

    async def get_task(self, thread_id: str):
        if self.show_logger:
            logger.info(f"SQLAlchemy: get_task, thread_id={thread_id}")

        query = """SELECT * FROM threads_tasks WHERE "thread_id" = :thread_id"""
        parameters = {"thread_id": thread_id}
        element = await self.execute_sql(
            query=query, parameters=parameters
        )
        if isinstance(element, list) and element:
            element_dict = element[0]
            return element_dict['task_id']
        else:
            return None

    async def update_thread(
            self,
            thread_id: str,
            name: Optional[str] = None,
            user_id: Optional[str] = None,
            metadata: Optional[Dict] = None,
            tags: Optional[List[str]] = None,
    ):

        if self.show_logger:
            logger.info(f"SQLAlchemy: update_thread, thread_id={thread_id}, name={name}")

        user_identifier = None
        if user_id:
            user_identifier = await self._get_user_identifer_by_id(user_id)

        data = {
            "id": thread_id,
            "createdAt": (
                await self.get_current_timestamp() if metadata is None else None
            ),
            "name": (
                name
                if name is not None and len(name) > 0
                else f"Session {await self.get_current_timestamp()}"
            ),
            "userId": user_id,
            "userIdentifier": user_identifier,
            "tags": tags,
            "metadata": json.dumps(metadata) if metadata else None,
        }
        parameters = {
            key: value for key, value in data.items() if value is not None
        }  # Remove keys with None values
        columns = ", ".join(f'"{key}"' for key in parameters.keys())
        values = ", ".join(f":{key}" for key in parameters.keys())
        updates = ", ".join(
            f'"{key}" = EXCLUDED."{key}"' for key in parameters.keys() if key != "id"
        )
        query = f"""
            INSERT INTO threads ({columns})
            VALUES ({values})
            ON CONFLICT ("id") DO UPDATE
            SET {updates};
        """
        await self.execute_sql(query=query, parameters=parameters)

    async def update_thread_name(
            self,
            thread_id: str,
            name: str = None,
    ):
        if self.show_logger:
            logger.info(f"SQLAlchemy: update_thread_name, thread_id={thread_id}, name={name}")

        data = {
            "id": thread_id,
            "name": (
                name
                if name is not None
                else f"Session {await self.get_current_timestamp()}"
            ),
        }
        parameters = {
            key: value for key, value in data.items() if value is not None
        }
        query = f"""
            UPDATE threads SET name=:name WHERE id=:id;
        """
        await self.execute_sql(query=query, parameters=parameters)
