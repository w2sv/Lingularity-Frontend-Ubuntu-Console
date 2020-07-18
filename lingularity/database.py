from typing import *
from dataclasses import dataclass

import pymongo

from lingularity.utils.datetime import datetag_today, day_difference


class MongoDBClient:
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

    _cluster = None

    def __init__(self, user: Optional[str], language: Optional[str], credentials: Credentials):
        self._user = user
        self._language = language
        self._cluster = pymongo.MongoClient(credentials.client_endpoint(srv_endpoint=True), serverSelectionTimeoutMS=1_000)

    def set_language(self, language: str):
        assert self._language is None, 'language ought not to be reassigned'
        self._language = language

    @property
    def user_names(self) -> List[str]:
        return self._cluster.database_names()

    @property
    def user_data_base(self) -> pymongo.collection.Collection:
        return self._cluster[self._user]

    # ------------------
    # General
    # ------------------
    @property
    def general_collection(self) -> pymongo.collection.Collection:
        return self.user_data_base['general']

    def initialize_user(self, password: str, first_name: str):
        self.general_collection.insert_one({'_id': 'unique', 'password': password, 'first_name': first_name})

    def update_last_session_statistics(self, trainer: str, faced_items: int):
        self.general_collection.update_one(
            filter={'_id': 'unique'},
            update={'$set': {'last_session': {'trainer': trainer,
                                              'faced_items': faced_items,
                                              'date': datetag_today(),
                                              'language': self._language}}},
            upsert=True
        )

    def query_password(self) -> str:
        return self.general_collection.find_one({'_id': 'unique'})['password']

    def query_first_name(self) -> str:
        return self.general_collection.find_one({'_id': 'unique'})['first_name']

    def query_last_session_statistics(self) -> Dict[str, Union[str, int]]:
        return self.general_collection.find_one({'_id': 'unique'})['last_session']

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

    def update_vocable_entry(self, token: str, score_increment: float):
        self.vocabulary_collection.find_one_and_update(
            filter={'_id': self._language, token: {'$exists': True}},
            update={'$inc': {
                        f'{token}.tf': 1,
                        f'{token}.s': score_increment},
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

    def query_vocabulary_data(self) -> List[Dict[str, Union[str, int, float]]]:
        result = self.vocabulary_collection.find_one(self._language)
        result.pop('_id')
        return [{k: v} for k, v in result.items()]

    def query_imperfect_vocabulary_entries(self, perfection_score=5, days_before_retention_assertion=50) -> List[Dict[str, Union[str, int]]]:
        vocabulary_data = self.query_vocabulary_data()
        original_length = vocabulary_data.__len__()
        for i, vocabulary_entry in enumerate(vocabulary_data[::-1]):
            if vocabulary_entry['s'] >= perfection_score and day_difference(vocabulary_entry['lfd']) < days_before_retention_assertion:
                vocabulary_data.pop(original_length - i - 1)
        return vocabulary_data

    def get_vocabulary_possessing_languages(self) -> List[str]:
        return list(self.vocabulary_collection.find().distinct('_id'))

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
    client = MongoDBClient(user='janek_zangenberg', language='Italian', credentials=MongoDBClient.Credentials.default())
    client.update_last_session_statistics('s', 78)
