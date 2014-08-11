Interpreting results
====================

After running the FxOS Certification Suite, a result file will be generated
(firefox-os-certification_timestamp.zip by default) in the current directory.
Inside this file are several logs; you need to review two of these to
understand the cert suite's results.

The results.html file
---------------------

This file contains the results of all PASS/FAIL tests run by the cert suite,
including the webapi tests, the web-platform-tests, and the webIDL tests.

The cert/cert_results.html file
-------------------------------

This file contains informative test output that needs to be interpreted
by a human engineer.  It contains the following sections:

omni_result
'''''''''''
This section contains the output of the omni_analyzer tool.  The omni_alayzer
compares all the JS files in omni.ja on the device against a reference
version.  If any differences are found, they are displayed here.

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

[web|privileged|certified]_unexpected_webidl_results
''''''''''''''''''''''''''''''''''''''''''''''''''''
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

[web|privileged|certified]_added_webidl_results
'''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, represents new, unexpected APIs which are
exposed to applications in an (unprivileged|privileged|certified) context
on the test device, but which are not present on a reference device.

[web|privileged|certified]_missing_webidl_results
'''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, represents APIs which are missing
in an (unprivileged|privileged|certified) context on the test device,
but which are present on a reference device.

[web|privileged|certified]_added_window_functions
'''''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'window'
object which are present on a reference version, but not present on the device,
in an (unprivileged|privileged|certified) context.

[web|privileged|certified]_missing_window_functions
'''''''''''''''''''''''''''''''''''''''''''''''''''
This section, if present, lists objects descended from the top-level 'window'
object which are present on the device, but not on a reference version, in
an (unprivileged|privileged|certified) context.
