from typing import Optional, Dict, List, Any, Iterator
from dataclasses import dataclass

import pymongo

from lingularity.frontend.console.utils.date import datetag_today, n_days_ago
from .document_types import LastSessionStatistics, VocableAttributes


class MongoDBClient:
    @dataclass(frozen=True)
    class Credentials:
        host: str
        user: str
        password: str

        @classmethod
        def default(cls):
            return cls(
                host='cluster0.zthtl.mongodb.net/admin?retryWrites=true&w=majority',
                user='sickdude69',
                password='clusterpassword'
            )

        def client_endpoint(self, srv_endpoint: bool) -> str:
            return f'mongodb{"+srv" if srv_endpoint else ""}://{self.user}:{self.password}@{self.host}'

    def __init__(self, user: Optional[str] = None, language: Optional[str] = None):
        self._user = user
        self._language = language
        self._cluster = pymongo.MongoClient(self.Credentials.default().client_endpoint(srv_endpoint=True), serverSelectionTimeoutMS=1_000)

    # -------------------
    # Properties
    # -------------------
    @property
    def user(self) -> Optional[str]:
        return self._user

    @user.setter
    def user(self, value: str):
        if self._user is not None:
            raise AttributeError('user ought not to be reassigned')
        self._user = value

    @property
    def language(self) -> Optional[str]:
        return self._language

    @language.setter
    def language(self, value: str):
        if self._language is not None:
            raise AttributeError('language ought not to be reassigned')
        self._language = value

    # --------------------
    # .Database-related
    # --------------------
    @property
    def mail_addresses(self) -> Iterator[str]:
        return (self._cluster[user_name]['general'].find_one(filter={'_id': 'unique'})['emailAddress'] for user_name in self.usernames)

    def mail_address_taken(self, mail_address: str) -> bool:
        return mail_address in self.mail_addresses

    @property
    def usernames(self) -> List[str]:
        """ equals databases """

        return self._cluster.list_database_names()

    @property
    def user_data_base(self) -> pymongo.collection.Collection:
        assert self._cluster is not None, ''
        return self._cluster[self._user]

    # -------------------
    # Generic
    # -------------------
    def drop_all_databases(self):
        for db in self._cluster.list_database_names():
            self._cluster.drop_database(db)

    # ------------------
    # Collections
    # ------------------

    # ------------------
    # .General
    # ------------------
    @property
    def general_collection(self) -> pymongo.collection.Collection:
        """ {_id: 'unique',
             emaiLAddress: email_address,
             password: password,
             lastSession: {trainer: trainer,
                           nFacedItems: n_faced_items,
                           date: date,
                           language: language}} """

        return self.user_data_base['general']

    def initialize_user(self, email_address: str, password: str):
        print(email_address, password)
        self.general_collection.insert_one({'_id': 'unique',
                                            'emailAddress': email_address,
                                            'password': password})

    def update_last_session_statistics(self, trainer: str, faced_items: int):
        self.general_collection.update_one(
            filter={'_id': 'unique'},
            update={'$set': {'lastSession': {'trainer': trainer,
                                             'nFacedItems': faced_items,
                                             'date': datetag_today(),
                                             'language': self._language}}},
            upsert=True
        )

    def query_password(self) -> str:
        return self.general_collection.find_one({'_id': 'unique'})['password']

    def query_last_session_statistics(self) -> Optional[LastSessionStatistics]:
        try:
            return self.general_collection.find_one({'_id': 'unique'})['lastSession']
        except TypeError:
            return None

    # ------------------
    # .Vocabulary
    # ------------------
    @property
    def vocabulary_collection(self) -> pymongo.collection.Collection:
        """ {'_id': language,
             $target_language_token: {t: translation
                                      tf: times_faced
                                      s: score
                                      lfd: last_faced_date}} """

        return self.user_data_base['vocabulary']

    def insert_vocable(self, target_language_token: str, translation: str):
        self.vocabulary_collection.update_one(
            filter={'_id': self._language},
            update={'$set': {target_language_token: {
                         't': translation,
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

    def query_vocable_attributes(self, vocable: str) -> VocableAttributes:
        return self.vocabulary_collection.find_one(self._language)[vocable]

    def query_vocabulary_data(self) -> List[Dict[str, Any]]:
        result = self.vocabulary_collection.find_one(self._language)
        result.pop('_id')
        return [{k: v} for k, v in result.items()]

    def query_imperfect_vocabulary_entries(self, perfection_score=5, days_before_retention_assertion=50) -> List[Dict[str, Any]]:
        vocabulary_data = self.query_vocabulary_data()
        original_length = vocabulary_data.__len__()
        for i, vocabulary_entry in enumerate(vocabulary_data[::-1]):
            if vocabulary_entry['s'] >= perfection_score and n_days_ago(vocabulary_entry['lfd']) < days_before_retention_assertion:
                vocabulary_data.pop(original_length - i - 1)
        return vocabulary_data

    def get_vocabulary_possessing_languages(self) -> List[str]:
        return list(self.vocabulary_collection.find().distinct('_id'))

    # ------------------
    # .Training Chronic
    # ------------------
    @property
    def training_chronic_collection(self) -> pymongo.collection.Collection:
        """ {_id: language,
             $date: {$trainer_abbreviation: n_faced_items}} """

        return self.user_data_base['training_chronic']

    def inject_session_statistics(self, trainer_abbreviation: str, n_faced_items: int):
        self.training_chronic_collection.update_one(
            filter={'_id': self._language},
            update={'$inc': {f'{datetag_today()}.{trainer_abbreviation}': n_faced_items}},
            upsert=True
        )

    def query_training_chronic(self) -> Dict[str, Dict[str, int]]:
        training_chronic = next(iter(self.training_chronic_collection.find({'_id': self._language})))
        training_chronic.pop('_id')
        return training_chronic

    # ------------------
    # .Training Chronic
    # ------------------
    @property
    def language_related_collection(self) -> pymongo.collection.Collection:
        """ {_id: $language,
            playbackSpeed: $playback_speed} """

        return self.user_data_base['language_related']

    def insert_playback_speed(self, playback_speed: float):
        self.language_related_collection.update_one(filter={'_id': self._language},
                                                    update={'$set': {'playbackSpeed': playback_speed}},
                                                    upsert=True)

    def query_playback_speed(self) -> Optional[float]:
        try:
            return self.language_related_collection.find_one(filter={'_id': self._language})['playbackSpeed']
        except (AttributeError, KeyError, TypeError):
            return None

if __name__ == '__main__':
    client = MongoDBClient(user='janek_zangenberg', language='Italian')
