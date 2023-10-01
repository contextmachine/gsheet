
import os

import json

import httplib2
from googleapiclient.discovery import build

from oauth2client.service_account import ServiceAccountCredentials
def get_service_sacc(keyfile_dict, scopes=('https://www.googleapis.com/auth/spreadsheets',) ):
    scopes = list(scopes)
    creds_service = ServiceAccountCredentials.from_json_keyfile_dict(keyfile_dict,
                                                                     scopes).authorize(httplib2.Http())
    return build('sheets', 'v4', http=creds_service)

def get_sheet(*args,**kwargs):
    return get_service_sacc(*args,**kwargs).spreadsheets()
def update_sheet(sheet, data, sheet_range, sheet_id=os.getenv("SHEET_ID")):
    return sheet.values().update(
        spreadsheetId=sheet_id,
        range=sheet_range,
        valueInputOption='RAW',
        body={'values': data}).execute()
