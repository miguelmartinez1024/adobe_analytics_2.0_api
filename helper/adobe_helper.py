# Author: Miguel Martinez 
# Site: https://analystadmin.com/

import jwt
import datetime
import requests
import os
import pandas as pd

# metascopes
metascopes = 'ent_analytics_bulk_ingest_sdk'

# URL Endpoints
imsHost = 'ims-na1.adobelogin.com'
imsExchange = 'https://ims-na1.adobelogin.com/ims/exchange/jwt'
discoveryUrl = 'https://analytics.adobe.io/discovery/me'
analyticsApiUrl = 'https://analytics.adobe.io/api'
accessTokenEndpoint = 'https://ims-na1.adobelogin.com/ims/exchange/jwt'


algorithm = 'RS256'


def getToken(org_id, tech_account_id, client_id, client_secret, private_key_path):
    payload = {
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=30),
        'iss': org_id,
        'sub': tech_account_id,
        'https://{}/s/{}'.format(imsHost, metascopes): True,
        'aud': 'https://{}/c/{}'.format(imsHost, client_id)

    }
    encoded = jwt.encode(payload, readPrivateKey(private_key_path),
                         algorithm=algorithm)

    post_payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'jwt_token': encoded
    }

    r = requests.post(accessTokenEndpoint, data=post_payload)

    if r.status_code == 200:
        r_json = r.json()

        token = {
            'success': True,
            'access_token': r_json['access_token'],
            'expires_in': r_json['expires_in'],
            'token_type': r_json['token_type']
        }

        return token
    else:
        return {
            'success': False,
            'error_code': r.status_code,
            'error_description': r.json()['error_description']
        }


def readPrivateKey(private_key_path):
    privatekeyfile = open(os.path.join(os.path.expanduser('~'), private_key_path), 'r')
    return privatekeyfile.read()

def discoverMe(client_id, access_token):
    r = requests.get(
        discoveryUrl,
        headers={
            "Authorization": "Bearer {}".format(access_token),
            "x-api-key": client_id
        }
    )
    if r.status_code == 200:
        data = r.json()
        data['success'] = True
        return data
    else:
        return {
            'success': False,
            'error_code': r.status_code,
            'error_description': r.json()['message']
        }


def get_all_calculated_metrics(client_id, access_token, global_company_id, report_suite, metric_name, include_type, owner, tag_names, filterByIds=''):
    data_type = 'calculated_metrics'
    data_content_array = []
    page = 1
    while True:
        overrides = {
            'rsids': report_suite,
            'name': metric_name,
            'includeType': include_type,
            'ownerId': owner,
            'tagNames': tag_names,
            'filterByIds' : filterByIds
        }
        if page != 1:
            overrides['page'] = page

        payload = getCalculatedMetrics(
            client_id=client_id,
            access_token=access_token,
            global_company_id=global_company_id,
            overrides=overrides
        )

        if payload['success']:
            return payload['payload']['content']
            # code needs to be modified to handle multiple pages...this is the reason for the While True


def getCalculatedMetrics(client_id, access_token, global_company_id, overrides=None):
    calculatedMetricsUrl = 'https://analytics.adobe.io/api/{}/calculatedmetrics'
    url = (calculatedMetricsUrl+'?').format(global_company_id)
    params = {
        'locale': 'en_US',
        'limit': '500',
        'page': '0',
        'sortDirection': 'ASC',
        'sortProperty': 'name',
        # 'rsids':'<rsid>',
        'includeType': 'shared',
        'expansion': 'reportSuiteName,ownerFullName,tags,definition,compatibility,categories'
    }

    # add additional args
    if overrides is not None:
        for k, v in overrides.items():
            if v:
                params[k] = v

    r = requests.get(
        url=url,
        params=params,
        headers={
            "Authorization": "Bearer {}".format(access_token),
            "x-api-key": client_id,
            "x-proxy-global-company-id": global_company_id,
            "accept": "application/json",
        }
    )
    if r.status_code == 200:
        data = {
            'success': True,
            'payload': r.json()
        }

        return data

    else:
        return {
            'success': False,
            'error_code': r.status_code,
            'error_description': r.json()['message']
        }
