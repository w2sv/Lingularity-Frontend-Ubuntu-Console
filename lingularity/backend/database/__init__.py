from typing import Optional, Dict, List, Any, Iterator
from dataclasses import dataclass

import pymongo

# TODO: resolve circular import when importing VocableEntry
from .document_types import LastSessionStatistics, VocableAttributes, TrainingChronic
from lingularity.backend.resources import strings as string_resources
from lingularity.backend.utils.date import today
from lingularity.backend.utils.state_sharing import MonoStatePossessor


class MongoDBClient(MonoStatePossessor):
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
        super().__init__()

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
        assert self._user is None, 'user ought not to be reassigned'
        self._user = value

    @property
    def user_set(self) -> bool:
        return self.user is not None

    @property
    def language(self) -> Optional[str]:
        return self._language

    @language.setter
    def language(self, value: str):
        assert self._language is None, 'language ought not to be reassigned'
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
        """ Equals databases """

        return self._cluster.list_database_names()

    @property
    def user_data_base(self) -> pymongo.collection.Collection:
        return self._cluster[self._user]

    # -------------------
    # Generic
    # -------------------
    def drop_all_databases(self):
        for db in self._cluster.list_database_names():
            self._cluster.drop_database(db)

    def delete_user(self, user: str):
        self._cluster.drop_database(user)

    @staticmethod
    def _get_ids(collection: pymongo.collection.Collection) -> List[Any]:
        return list(collection.find().distinct('_id'))

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

    def initialize_user(self, user: str, email_address: str, password: str):
        self.user = user
        self.general_collection.insert_one({'_id': 'unique',
                                            'emailAddress': email_address,
                                            'password': password})

    def update_last_session_statistics(self, trainer: str, faced_items: int):
        self.general_collection.update_one(
            filter={'_id': 'unique'},
            update={'$set': {'lastSession': {'trainer': trainer,
                                             'nFacedItems': faced_items,
                                             'date': str(today),
                                             'language': self._language}}},
            upsert=True
        )

    def query_password(self) -> str:
        return self.general_collection.find_one({'_id': 'unique'})['password']

    def query_last_session_statistics(self) -> Optional[LastSessionStatistics]:
        try:
            return self.general_collection.find_one({'_id': 'unique'})['lastSession']
        except KeyError:
            return None

    # ------------------
    # .Vocabulary
    # ------------------
    @property
    def vocabulary_collection(self) -> pymongo.collection.Collection:
        """ {'_id': language,
             $target_language_token: {t: translation_field
                                      tf: times_faced
                                      s: score
                                      lfd: last_faced_date}} """

        return self.user_data_base['vocabulary']

    def insert_vocable(self, vocable_entry):
        self.vocabulary_collection.update_one(
            filter={'_id': self._language},
            update={'$set': vocable_entry.entry},
            upsert=True
        )

    def delete_vocable_entry(self, vocable_entry):
        self.vocabulary_collection.update_one(
            filter={'_id': self._language},
            update={'$unset': vocable_entry.entry}
        )

    def update_vocable_entry(self, token: str, new_score: float):
        self.vocabulary_collection.find_one_and_update(
            filter={'_id': self._language, token: {'$exists': True}},
            update={'$inc': {f'{token}.tf': 1},
                    '$set': {f'{token}.lfd': str(today),
                             f'{token}.s': new_score}},
            upsert=False
        )

    def insert_altered_vocable_entry(self, old_vocable: str, altered_vocable_entry):
        # delete old sub document corresponding to old_vocable regardless of whether the vocable,
        # that is the sub document key has changed
        self.vocabulary_collection.find_one_and_update(
            filter={'_id': self._language},
            update={'$unset': {old_vocable: 1}}
        )

        self.insert_vocable(altered_vocable_entry)

    def query_vocabulary_possessing_languages(self) -> List[str]:
        return self._get_ids(self.vocabulary_collection)

    def query_vocabulary_data(self) -> List[Dict[str, Any]]:
        result = self.vocabulary_collection.find_one(self._language)
        result.pop('_id')
        return [{k: v} for k, v in result.items()]

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
            update={'$inc': {f'{str(today)}.{trainer_abbreviation}': n_faced_items}},
            upsert=True
        )

    def query_training_chronic(self) -> TrainingChronic:
        training_chronic = next(iter(self.training_chronic_collection.find({'_id': self._language})))
        training_chronic.pop('_id')
        return training_chronic

    # ------------------
    # .Language Metadata
    # ------------------
    @property
    def language_metadata_collection(self) -> pymongo.collection.Collection:
        """ {_id: $language,
            variety: {$language_variety: {playbackSpeed: float
                                          use: bool}}
            ttsEnabled: bool} """

        return self.user_data_base['language_metadata']

    # ------------------
    # ..language variety usage
    # ------------------
    def set_language_variety_usage(self, variety_identifier: str, value: bool):
        self.language_metadata_collection.update_one(filter={'_id': self._language},
                                                     update={'$set': {f'variety.{variety_identifier}.use': value}},
                                                     upsert=True)

    def query_language_variety(self) -> Optional[str]:
        """ assumes existence of varietyIdentifier sub dict in case of
            existence of language related collection """

        if (language_metadata := self.language_metadata_collection.find_one(filter={'_id': self._language})) is None:
            return None

        elif variety_2_usage := language_metadata.get('variety'):
            for identifier, value_dict in variety_2_usage.items():
                if value_dict['use']:
                    return identifier

        return None

    # ------------------
    # ..playback speed
    # ------------------
    def insert_playback_speed(self, variety: str, playback_speed: float):
        self.language_metadata_collection.update_one(filter={'_id': self._language},
                                                     update={'$set': {f'variety.{variety}.playbackSpeed': playback_speed}},
                                                     upsert=True)

    def query_playback_speed(self, variety: str) -> Optional[float]:
        try:
            return self.language_metadata_collection.find_one(filter={'_id': self._language})['variety'][variety]['playbackSpeed']
        except (AttributeError, KeyError, TypeError):
            return None

    # ------------------
    # ..tts enablement
    # ------------------
    def set_tts_enablement(self, value: bool):
        self.language_metadata_collection.update_one(filter={'_id': self._language},
                                                     update={'$set': {
                                                        f'ttsEnabled': value}},
                                                     upsert=True)

    def query_tts_enablement(self):
        try:
            return self.language_metadata_collection.find_one(filter={'_id': self._language}).get('ttsEnabled')
        except AttributeError:
            return None

    # ------------------
    # ..english reference language
    # ------------------
    def set_reference_language(self, reference_language: str):
        self.language_metadata_collection.update_one(filter={'_id': string_resources.ENGLISH},
                                                     update={'$set': {
                                                         f'referenceLanguage': reference_language}},
                                                     upsert=True)

    def query_reference_language(self) -> Optional[str]:
        try:
            return self.language_metadata_collection.find_one(filter={'_id': string_resources.ENGLISH})['referenceLanguage']
        except TypeError:
            return None


if __name__ == '__main__':
    client = MongoDBClient(user='janek')
    print(client.query_vocabulary_possessing_languages())
