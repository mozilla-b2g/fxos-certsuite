from mozlog.structured import (
    structuredlog,
    handlers,
    formatters,
    reader,
)

import subsuite

def get_test_failures(raw_log):
    '''
    Return the list of test failures contained within a structured log file.
    '''
    failures = []
    def test_status(data):
        if data['status'] == 'FAIL':
            failures.append(data)
    with open(raw_log, 'r') as f:
        reader.each_log(reader.read(f),
                        {'test_status':test_status})
    return failures
