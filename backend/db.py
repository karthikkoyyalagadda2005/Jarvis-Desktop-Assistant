# import os
# from datetime import datetime, timezone

# from pymongo import MongoClient
# from pymongo.errors import PyMongoError


# class Database:
#     def __init__(self):
#         self.mongo_uri = os.getenv("MONGO_URI")
#         self.database_name = os.getenv(
#             "MONGO_DATABASE",
#             "personal_assistant",
#         )
#         self.collection_name = os.getenv(
#             "MONGO_COLLECTION",
#             "commands",
#         )

#         if not self.mongo_uri:
#             raise ValueError(
#                 "MONGO_URI is missing from the environment variables."
#             )

#         self.client = MongoClient(
#             self.mongo_uri,
#             serverSelectionTimeoutMS=5000,
#         )

#         self.db = self.client[self.database_name]
#         self.commands = self.db[self.collection_name]

#     # --------------------------------------------------
#     # TEST DATABASE CONNECTION
#     # --------------------------------------------------

#     def test_connection(self):
#         try:
#             self.client.admin.command("ping")
#             return True
#         except PyMongoError:
#             return False

#     # --------------------------------------------------
#     # SAVE COMMAND
#     # --------------------------------------------------

#     def save_command(self, command_text, response_text):
#         document = {
#             "command_text": command_text,
#             "response_text": response_text,
#             "created_at": datetime.now(timezone.utc),
#         }

#         try:
#             self.commands.insert_one(document)
#             return True
#         except PyMongoError as error:
#             print(f"MongoDB save error: {error}")
#             return False

#     # --------------------------------------------------
#     # GET COMMAND HISTORY
#     # --------------------------------------------------

#     def get_history(self, limit=50):
#         try:
#             documents = (
#                 self.commands
#                 .find(
#                     {},
#                     {
#                         "_id": 1,
#                         "command_text": 1,
#                         "response_text": 1,
#                         "created_at": 1,
#                     },
#                 )
#                 .sort("created_at", -1)
#                 .limit(limit)
#             )

#             history = []

#             for document in documents:
#                 history.append(
#                     {
#                         "id": str(document["_id"]),
#                         "command_text": document.get(
#                             "command_text",
#                             "",
#                         ),
#                         "response_text": document.get(
#                             "response_text",
#                             "",
#                         ),
#                         "created_at": (
#                             document["created_at"].isoformat()
#                             if document.get("created_at")
#                             else None
#                         ),
#                     }
#                 )

#             return history

#         except PyMongoError as error:
#             print(f"MongoDB history error: {error}")
#             return []






























import os
import datetime as dt

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from dotenv import load_dotenv


load_dotenv()


class Database:

    def __init__(self):

        self.mongo_uri = os.getenv(
            "MONGO_URI",
            "mongodb://localhost:27017",
        )

        self.database_name = os.getenv(
            "MONGO_DATABASE",
            "personal_assistant",
        )

        self.collection_name = os.getenv(
            "MONGO_COLLECTION",
            "command_history",
        )

        print("MongoDB URI:", self.mongo_uri)
        print("MongoDB Database:", self.database_name)
        print("MongoDB Collection:", self.collection_name)

        self.client = MongoClient(
            self.mongo_uri,
            serverSelectionTimeoutMS=5000,
        )

        self.db = self.client[
            self.database_name
        ]

        self.collection = self.db[
            self.collection_name
        ]

    # ==========================================================
    # TEST CONNECTION
    # ==========================================================

    def test_connection(self):

        try:

            self.client.admin.command(
                "ping"
            )

            return True

        except PyMongoError as error:

            print(
                f"MongoDB connection error: {error}"
            )

            return False

    # ==========================================================
    # SAVE COMMAND
    # ==========================================================

    def save_command(
        self,
        command_text,
        response_text,
        response_type="unknown",
    ):

        try:

            document = {
                "command_text": str(
                    command_text
                ).strip(),

                "response_text": str(
                    response_text
                ).strip(),

                "response_type": str(
                    response_type
                ).strip(),

                "created_at": dt.datetime.now(
                    dt.timezone.utc
                ),
            }

            result = self.collection.insert_one(
                document
            )

            print(
                "MongoDB document inserted:",
                result.inserted_id,
            )

            return True

        except PyMongoError as error:

            print(
                f"MongoDB insert error: {error}"
            )

            return False

        except Exception as error:

            print(
                f"Unexpected DB save error: {error}"
            )

            return False

    # ==========================================================
    # GET HISTORY
    # ==========================================================

    def get_history(self, limit=100):

        try:

            documents = (
                self.collection
                .find({})
                .sort(
                    "created_at",
                    -1,
                )
                .limit(limit)
            )

            history = []

            for document in documents:

                history.append(
                    {
                        "_id": str(
                            document.get("_id")
                        ),

                        "command_text":
                            document.get(
                                "command_text",
                                "",
                            ),

                        "response_text":
                            document.get(
                                "response_text",
                                "",
                            ),

                        "response_type":
                            document.get(
                                "response_type",
                                "unknown",
                            ),

                        "created_at":
                            document.get(
                                "created_at"
                            ).isoformat()
                            if document.get(
                                "created_at"
                            )
                            else None,
                    }
                )

            return history

        except PyMongoError as error:

            print(
                f"MongoDB history error: {error}"
            )

            return []

        except Exception as error:

            print(
                f"Unexpected history error: {error}"
            )

            return []   