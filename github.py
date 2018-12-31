"""GitHub Appplication access service

Usage:
  github.py list installations --app-id APPLICATION_ID --key PRIVATE_KEY_PATH [options]

Options:
  --app-id APPLICATION_ID
  --install-id INSTALLATION_ID
  --key PRIVATE_KEY_PATH

  -d --debug                 Enable debug mode.
"""


__version__ = '0.0.0'


import requests
import logging
import jwt

from datetime import datetime
from docopt import docopt

from pprint import pprint


class GitHubApp():
    def __init__(self, app_id, install_id=None, url='https://api.github.com', private_key=None):
        self.app_token = None
        self.url = url
        self.app_id = app_id
        self.install_id = None
        self.install_token = None

        with open(private_key, 'rb') as f:
            self.key = f.read()

        if install_id is not None:
            self.authenticate_as_installation(install_id)

    def get(self, endpoint, as_installation=False, accept='application/vnd.github.machine-man-preview+json'):
        if self.app_token is None:
            logging.debug(f"Signing new app token")
            now = int(datetime.now().timestamp())
            self.app_token = jwt.encode({'iat': now, 'exp': now + 600, 'iss': self.app_id}, self.key, algorithm='RS256').decode('utf-8')

        token = self.install_token if as_installation else self.app_token

        resp = requests.get(
            f'{self.url}/{endpoint}',
            headers={'accept': accept, 'authorization': f'Bearer {token}'}
        )

        if resp.status_code == 401:
            if "'Expiration' claim" in resp.json()['message']:
                if as_installation:
                    logging.debug(f"Requesting new app token")
                    self.app_token = None
                else:
                    logging.debug(f"Requesting new installation token")
                    self.authenticate_as_installation(self.installation_id)

                return self.post(endpoint, as_installation=as_installation)

        return resp.json()

    def post(self, endpoint, payload, as_installation=False, accept='application/vnd.github.machine-man-preview+json'):
        if self.app_token is None:
            logging.debug(f"Signing new app token")
            now = int(datetime.now().timestamp())
            self.app_token = jwt.encode({'iat': now, 'exp': now + 600, 'iss': self.app_id}, self.key, algorithm='RS256').decode('utf-8')

        token = self.install_token if as_installation else self.app_token

        resp = requests.post(
            f'{self.url}/{endpoint}',
            json=payload,
            headers={'accept': accept, 'authorization': f'Bearer {token}'}
        )

        if resp.status_code == 401:
            if "'Expiration' claim" in resp.json()['message']:
                if as_installation:
                    logging.debug(f"Requesting new app token")
                    self.app_token = None
                else:
                    logging.debug(f"Requesting new installation token")
                    self.authenticate_as_installation(self.installation_id)

                return self.post(endpoint, payload, as_installation=as_installation)

        return resp.json()

    def patch(self, endpoint, payload, as_installation=False, accept='application/vnd.github.machine-man-preview+json'):
        if self.app_token is None:
            logging.debug(f"Signing new app token")
            now = int(datetime.now().timestamp())
            self.app_token = jwt.encode({'iat': now, 'exp': now + 600, 'iss': self.app_id}, self.key, algorithm='RS256').decode('utf-8')

        token = self.install_token if as_installation else self.app_token

        resp = requests.patch(
            f'{self.url}/{endpoint}',
            json=payload,
            headers={'accept': accept, 'authorization': f'Bearer {token}'}
        )

        if resp.status_code == 401:
            if "'Expiration' claim" in resp.json()['message']:
                if as_installation:
                    logging.debug(f"Requesting new app token")
                    self.app_token = None
                else:
                    logging.debug(f"Requesting new installation token")
                    self.authenticate_as_installation(self.installation_id)

                return self.post(endpoint, payload, as_installation=as_installation)

        return resp.json()

    def list_installations(self):
        return self.get(f'app/installations')

    def authenticate_as_installation(self, id):
        resp = self.post(f'app/installations/{id}/access_tokens', {})

        if 'token' in resp:
            self.install_id = id
            self.install_token = resp['token']
            logging.info(f"Using installation {self.install_id}")
            logging.debug(f"Using installation token {self.install_token}")
        else:
            logging.error(f"Unable to authenticate as installation {id}")
            return resp

    def list_pullrequests(self, owner, repo):
        logging.debug(f"Listing pull requests for {owner}/{repo}")

        return self.get(f'repos/{owner}/{repo}/pulls', as_installation=True)

    def get_pullrequest(self, owner, repo, pr):
        logging.debug(f"Getting PR #{pr} for {owner}/{repo}")

        return self.get(f'repos/{owner}/{repo}/pulls/{pr}', as_installation=True)

    def create_check_run(self, owner, repo, name, sha, **check):
        logging.debug(f"Creating {name} check run at {sha} for {owner}/{repo}")

        check.update({
            'name': name,
            'head_sha': sha,
            # 'details_url': '',
            # 'external_id': '',
            # 'status': '',       # queued, in_progress, completed
            # 'started_at': '',   # YYYY-MM-DDTHH:MM:SSZ
            # 'conclusion': '',   # success, failure, neutral, cancelled, timed_out, or action_required
            # 'completed_at': '', # YYYY-MM-DDTHH:MM:SSZ
        })

        return self.post(
            f'repos/{owner}/{repo}/check-runs',
            check,
            as_installation=True,
            accept='application/vnd.github.antiope-preview+json'
        )

    def update_check_run(self, owner, repo, id, **check):
        logging.debug(f"Updating check {id} for {owner}/{repo}")

        return self.patch(
            f'repos/{owner}/{repo}/check-runs/{id}',
            check,
            as_installation=True,
            accept='application/vnd.github.antiope-preview+json'
        )


if __name__ == '__main__':
    logging.basicConfig(format='[%(levelname)s] %(asctime)s - %(funcName)s: %(message)s', level=logging.INFO)

    # Parse command line
    arguments = docopt(__doc__, version=__version__)

    # Enable debug if needed
    if arguments['--debug']:
        logging.getLogger().setLevel(logging.DEBUG)

    gh = GitHubApp(app_id=arguments['--app-id'], install_id=arguments['--install-id'], private_key=arguments['--key'])
    if arguments['list'] and arguments['installations']:
        pprint(gh.list_installations())

    # run_id = gh.create_check_run('tryexceptpass', 'githubapp', 'pytest', 'ca3944e')['id']
    #
    # pprint(gh.update_check_run(
    #     'tryexceptpass',
    #     'githubapp',
    #     run_id,
    #     started_at=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
    #     status='in_progress',
    #     # conclusion='failure',
    #     # completed_at=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
    #     output={
    #         'title': 'SOME TITLE',
    #         'summary': 'SOME SUMMARY',
    #         'text': "# SOME\n## Markdown Enabled\nText\n\n```python\nprint('Hellow World')\n```",
    #         'annotations': [{
    #             'path': '.gh-runner.yml',
    #             'filename': '.gh-runner.yml',
    #             'blob_href': 'http://blob.com',
    #             'warning_level': 'notice',
    #             'start_line': 6,
    #             'end_line': 6,
    #             # 'start_column'	    # The start column of the annotation.
    #             # 'end_column'	    # The end column of the annotation.
    #             'annotation_level': 'notice',   # notice, warning, or failure.
    #             'message': "Some Message",
    #             'title': 'Some failure annontation title',
    #             'raw_details': 'SOME REALLy Raw Deeetz',
    #         }]
    #     }
    # ))
