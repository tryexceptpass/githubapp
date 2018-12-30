import os
from github import GitHubApp
from datetime import datetime


APP_ID = os.environ['GITHUBAPP_APP_ID']
INSTALL_ID = os.environ['GITHUBAPP_INSTALL_ID']
PRIVATE_KEY = os.environ['GITHUBAPP_KEY']
CHECK_RUN_HASH = os.environ['CHECK_RUN_HASH']

GITHUB_USER = 'tryexceptpass'
GITHUB_REPO = 'githubapp'
CHECK_RUN_NAME = 'pytest'


gh = GitHubApp(APP_ID, install_id=INSTALL_ID, private_key=PRIVATE_KEY)

run_id = gh.create_check_run(GITHUB_USER, GITHUB_REPO, CHECK_RUN_NAME, CHECK_RUN_HASH)['id']

gh.update_check_run(
    GITHUB_USER,
    GITHUB_REPO,
    run_id,
    status='in_progress',
    started_at=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
)

has_failed = False
outcomes = {}


def pytest_runtest_makereport(item, call):
    global has_failed

    # print(run_id, item.location, call.when, call.result if call.excinfo is None else call.excinfo.traceback)

    if item.location[-1] not in outcomes:
        outcomes[item.location[-1]] = {'setup': None, 'call': None, 'teardown': None}

    if call.excinfo is None:
        outcome = 'passed'
    else:
        outcome = 'failed'
        has_failed = True

    outcomes[item.location[-1]][call.when] = outcome

    if call.excinfo is None:
        if call.when == 'teardown':
            outcome = outcomes[item.location[-1]]

            if outcome['setup'] == 'passed' and outcome['call'] == 'passed' and outcome['teardown'] == 'passed':
                gh.update_check_run(
                    GITHUB_USER,
                    GITHUB_REPO,
                    run_id,
                    status='completed',
                    conclusion='failure' if has_failed else 'success',
                    completed_at=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    output={
                        'title': 'Execution Completed with Failures' if has_failed else 'Execution Completed Successfully',
                        'summary': '',
                        # 'text': "# SOME\n## Markdown Enabled\nText",
                        'annotations': [{
                            'path': item.location[0],
                            'filename': item.location[0],
                            'blob_href': 'http://blob.com',
                            '`warning_level`': 'notice',     # notice, warning, or failure.
                            'start_line': 0,
                            'end_line': 0,
                            # 'start_column'	               # The start column of the annotation.
                            # 'end_column'	                   # The end column of the annotation.
                            'annotation_level': 'notice',    # notice, warning, or failure.
                            'message': 'Passed',
                            'title': item.location[-1],
                            # 'raw_details': '',
                        }]
                    }
                )

    else:
        entry = call.excinfo.traceback.getcrashentry()

        gh.update_check_run(
            GITHUB_USER,
            GITHUB_REPO,
            run_id,
            status='completed',
            conclusion='failure',
            completed_at=datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
            output={
                'title': 'Execution Completed with Failures' if has_failed else 'Execution Completed Successfully',
                'summary': '',
                # 'text': "# SOME\n## Markdown Enabled\nText",
                'annotations': [{
                    'path': entry.frame.code.raw.co_filename,
                    'filename': entry.frame.code.raw.co_filename,
                    'blob_href': 'http://blob.com',
                    'warning_level': 'failure',      # notice, warning, or failure.
                    'start_line': entry.lineno,
                    'end_line': entry.lineno,
                    # 'start_column'	               # The start column of the annotation.
                    # 'end_column'	                   # The end column of the annotation.
                    'annotation_level': 'failure',   # notice, warning, or failure.
                    'message': call.excinfo.exconly(),
                    'title': item.location[-1],
                    'raw_details': str(call.excinfo.getrepr(showlocals=True, funcargs=True)),
                }]
            }
        )
