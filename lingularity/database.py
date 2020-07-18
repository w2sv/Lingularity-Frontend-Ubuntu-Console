from typing import *
from dataclasses import dataclass

import pymongo

from lingularity.utils.datetime import datetag_today


@dataclass(frozen=True)
class Credentials:
    host: str
    user: str
    password: str

    @classmethod
    def default(cls):
        return cls(
            host='cluster0.zthtl.mongodb.net/janek_zangenberg?retryWrites=true&w=majority',
            user='sickdude69',
            password='clusterpassword'
        )

    def client_endpoint(self, srv_endpoint: bool) -> str:
        return f'mongodb{"+srv" if srv_endpoint else ""}://{self.user}:{self.password}@{self.host}'


class MongoDBClient:
    def __init__(self, user: str, language: str, credentials: Credentials):
        self._user = user
        self._language = language
        self._cluster = pymongo.MongoClient(credentials.client_endpoint(srv_endpoint=True), serverSelectionTimeoutMS=1_000)

    @property
    def user_data_base(self) -> pymongo.collection.Collection:
        return self._cluster[self._user]

    @property
    def vocabulary_collection(self) -> pymongo.collection.Collection:
        return self.user_data_base['_vocabulary']

    def insert_vocabulary(self, target_language_token: str, translation: str):
        self.vocabulary_collection.update_one(
            filter={'_id': self._language},
            update={'$set': {target_language_token: {
                         'translation': translation,
                         'tf': 0,
                         's': 0,
                         'lfd': None}
                }
            },
            upsert=True
        )

    def update_vocabulary_entry(self, target_language_token: str, correctly_answered: bool):
        self.vocabulary_collection.find_one_and_update(
            filter={'_id': self._language, target_language_token: {'$exists': True}},
            update={'$inc': {
                        f'{target_language_token}.tf': 1,
                        f'{target_language_token}.s': int(correctly_answered)},
                    '$set': {f'{target_language_token}.lfd': datetag_today()}
            },
            upsert=False
        )

    @property
    def usage_frequency_data_collection(self) -> pymongo.collection.Collection:
        return self.user_data_base['usage_frequency']

    def inject_session_synopsis(self, trainer_abbreviation: str, faced_items: int):
        self.usage_frequency_data_collection.update_one(
            filter={'_id': datetag_today()},
            update={'$inc': {f'{self._language}.{trainer_abbreviation}': faced_items}},
            upsert=True
        )

    
if __name__ == '__main__':
    client = MongoDBClient(user='janek_zangenberg', language='italian', credentials=Credentials.default())
    client.inject_session_synopsis('v', 5)
