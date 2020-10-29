from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from datetime import datetime
from django.conf import settings


class GoogleDrive():

    def __init__(self):
        self.client = None
        self.parent_folder = "1ZMIY6wtPLO8wMOovVwWshH3L4_rwtScO"
        self.path = str(settings.BASE_DIR) + '/' + 'token.pickle'
        print('PATH: ', self.path)

    def open_connection(self):
        if os.path.exists(self.path):
            with open(self.path, 'rb') as token:
                try:
                    creds = pickle.load(token)
                    self.client = build('drive', 'v3', credentials=creds)
                    print("Connected to Drive API")
                    if creds and creds.expired and creds.refresh_token:
                        creds.refresh(Request())
                        with open(self.path, 'wb') as token:
                            pickle.dump(creds, token)
                    return True
                except Exception as e:
                    print("Failed To Connect to Drive API", e)
                    return False

        else:
            print("Token Doesn't exists")
            return False

    def close_connection(self):
        del self.client

    def search_folder(self, name):
        file = self.client.files().list(q="name:'{n}'".format(n=name),
                                        fields="files(id, name)").execute()
        try:
            return file['files'][0]['id']
        except Exception as e:
            print("Folder,", name, " Doesn't Exists", e)
            return None

    def create_folder_if_not_exists(self, pid, name):
        pid2 = self.search_folder(name)
        if pid2 is None:
            file_metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [pid]
            }
            file = self.client.files().create(body=file_metadata,
                                              fields='id').execute()
            print("creating new")
            return file.get('id')
        else:
            print('Already Exists')
            return pid2

    def upload(self, newname, oldname, parent):
        new_name = newname + '.' + oldname.split('.')[-1]
        file_metadata = {'name': new_name, 'parents': [parent]}
        media = MediaFileUpload(oldname, mimetype='image/jpeg')
        file = self.client.files().create(body=file_metadata,
                                          media_body=media,
                                          fields='id').execute()
        print('File ID: %s' % file.get('id'))

    def refresh_token(self):
        pass

    def upload_image(self, oldname, corrID):
        id = self.create_folder_if_not_exists(self.parent_folder, corrID)
        newName = datetime.now().strftime('%d-%m-%Y')
        self.upload(newName, oldname, id)

#
# obj = GoogleDrive()
# obj.open_connection()
# obj.upload_image('', '1345')
