Interpreting results
====================

After running the FxOS Certification Suite, a result file will be generated
(firefox-os-certification.zip by default) in the current directory.  Inside
this file are several logs; you need to review two of these to understand the
cert suite's results.

The results.html file
---------------------

This file contains the results of the web-platform-tests.  To see these results,
click the 'web-platform-tests' link.  You will see a list of all the tests run,
and their status.  Any test failures with have a status which begins with
'UNEXPECTED'.

The cert/results.json file
--------------------------

omni_results
''''''''''''
This section contains the output of the omni_analyzer tool.  The omni_alayzer
compares all the JS files in omni.ja on the device against a reference
version.  If any differences are found, the entire file containing
the differences is base-64 encoded and included in the result file.

To see the diffs between the files on the device and the reference versions,
use the omni_diff.py tool inside the certsuite package.  To run this tool:

    source certsuite_venv/bin/activate # this will exist after you run the tests
    cd certsuite
    python omni_diff.py /path/to/cert_results.json expected_omni_results/omni.ja.1.3 results.diff

You can then view results.diff in an editor.

Differences in omni.ja files are not failures; they are simply changes that
should be reviewed in order to verify that they are harmless, from a
branding perspective.

application_ini
'''''''''''''''
This section contains the details inside the application.ini on the device.
This section is informative.

headers
'''''''
This section contains all of the HTTP headers, including the user-agent
string, that the device transmits when requesting network resources.  This
section is informative.

buildprops
''''''''''
This section contains the full list of Android build properties that
the device reports.  This section is informative.

kernel_version
''''''''''''''
This section contains the kernel version that the device reports.  This
section in informative.

processes_running
'''''''''''''''''
This section contains a list of all the processes that were running on the
device at the time the test was performed.  This section is informative.

[unpriv|priv|cert]_unexpected_webidl_results
''''''''''''''''''''''''''''''''''''''''''''
This section, if present, represents differences in how interfaces defined
in WebIDL files in a reference version differ from the interfaces found
on the device in an (unprivileged|privileged|certified) context.
For example:

    {
      "message": "assert_true: The prototype object must have a property \"textTracks\" expected true got false",
      "name": "HTMLMediaElement interface: attribute textTracks",
      "result": "FAIL"
    },

This means that the HTMLMediaElement interface was expected to expose
a textTracks attribute, but that attribute was not found on the device.

[unpriv|priv|cert]_added_window_functions
'''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'window'
object which are present on a reference version, but not present on the device,
in an (unprivileged|privileged|certified) context.

[unpriv|priv|cert]_missing_window_functions
'''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'window'
object which are present on the device, but not on a reference version, in
an (unprivileged|privileged|certified) context.

[unpriv|priv|cert]_added_navigator_functions
''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'navigator'
object which are present on a reference version, but not present on the device,
in an (unprivileged|privileged|certified) context.

[unpriv|priv|cert]_missing_navigator_functions
''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'navigator'
object which are present on the device, but not on a reference version,
in an (unprivileged|privileged|certified) context.

[unpriv|priv|cert]_added_navigator_unprivileged_functions
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'navigator'
object which are reported as null on a reference version, but reported
as not-null on the device.  This could indicate a permissions problem; i.e.,
the object belongs to an API which a reference version reports as null because
the API is only available to privileged contexts, and the test is run in an
unprivileged context, but which is available in an unprivileged context on
the device.  This test is performed in an (unprivileged|privileged|certified)
context.

[unpriv|priv|cert]_missing_navigator_unprivileged_functions
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'navigator'
object which are reported as not-null on a reference version, but reported
as null on the device.  This could indicate a permissions problem; i.e.,
the object belongs to an API which should be available to unprivileged
contexts, but which is not available to an unprivileged context on the device.
This test is performed in an (unprivileged|privileged|certified) context.
