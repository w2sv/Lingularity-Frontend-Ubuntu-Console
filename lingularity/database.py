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

    # ------------------
    # Vocabulary Collection
    # ------------------
    @property
    def vocabulary_collection(self) -> pymongo.collection.Collection:
        return self.user_data_base['vocabulary']

    def insert_vocable(self, target_language_token: str, translation: str):
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

    def update_vocable_entry(self, token: str, correctly_answered: bool):
        self.vocabulary_collection.find_one_and_update(
            filter={'_id': self._language, token: {'$exists': True}},
            update={'$inc': {
                        f'{token}.tf': 1,
                        f'{token}.s': int(correctly_answered)},
                    '$set': {f'{token}.lfd': datetag_today()}
            },
            upsert=False
        )

    def alter_vocable_entry(self, current_token: str, new_token: Optional[str], altered_meaning: Optional[str]):
        vocable_attributes = self.vocabulary_collection.find_one({'_id': self._language})[current_token]
        new_attributes = {k: v if k != 'translation' else altered_meaning for k, v in vocable_attributes.items()}
        if current_token == new_token:
            self.vocabulary_collection.update_one(
                filter={'_id': self._language},
                update={'$set': {current_token: new_attributes}}
            )
        else:
            self.vocabulary_collection.find_one_and_update(
                filter={'_id': self._language},
                update={'$unset': {current_token: 1}}
            )
            self.vocabulary_collection.find_one_and_update(
                filter={'_id': self._language},
                update={'$set': {new_token: new_attributes}}
            )

    def query_vocable_attributes(self, vocable: str) -> Dict[str, Union[str, int]]:
        return self.vocabulary_collection.find_one(self._language)[vocable]

    # ------------------
    # Training Chronic Collection
    # ------------------
    @property
    def training_chronic_collection(self) -> pymongo.collection.Collection:
        return self.user_data_base['training_chronic']

    def inject_session_statistics(self, trainer_abbreviation: str, faced_items: int):
        self.training_chronic_collection.update_one(
            filter={'_id': self._language},
            update={'$inc': {f'{datetag_today()}.{trainer_abbreviation}': faced_items}},
            upsert=True
        )

    def query_training_chronic(self) -> Dict[str, Dict[str, int]]:
        training_chronic = next(iter(self.training_chronic_collection.find({'_id': self._language})))
        training_chronic.pop('_id')
        return training_chronic

    # -------------------
    # Generic
    # -------------------
    def drop_all_databases(self):
        for db in self._cluster.list_database_names():
            self._cluster.drop_database(db)

    
if __name__ == '__main__':
    client = MongoDBClient(user='janek_zangenberg', language='italian', credentials=Credentials.default())
    # client.drop_all_databases()
    client.inject_session_statistics('s', 92)
    print(client.query_training_chronic())