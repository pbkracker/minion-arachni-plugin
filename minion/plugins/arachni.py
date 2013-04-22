# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from minion.plugin_api import ExternalProcessPlugin
from urlparse import urlparse
import subprocess
import os
import re

def _get_test_name(s):
    return s.split('.')[-1]

def parse_arachni_output_for_issues(output):
    issues = []
    return issues

class ArachniPlugin(ExternalProcessPlugin):

    PLUGIN_NAME = "Arachni"
    PLUGIN_VERSION = "0.1"

    ARACHNI_NAME = os.path.dirname(os.path.realpath(__file__)) + "/arachni_runner.rb"
    ARACHNI_ARGS = []

    perc = 0
    status = ''
    report = ''
    in_report = False

    def do_start(self):
        self.output = ""
        self.stderr = ""
        url = urlparse(self.configuration['target'])
        self.report_progress(10, 'Starting Arachni')
        self.spawn(self.ARACHNI_NAME, self.ARACHNI_ARGS + [self.configuration['target']])

    def do_process_stdout(self, data):
        # Percent Done: [-4.27]
        # Current Status: [auditing]
        # Issues: {...}
        # -----[REPORT FOLLOWS]-----

        print "ARACHNIOUTPUT %s" % (str(data))
        self.report_progress(50, str(data))

        if 'Percentage Done:' in data:
            m = re.match(r"Percent Done: \[\-?(.*)\.(.*)\]", str(data))
            if m is not None:
                 self.perc = m.group(1)
                 self.report_progress(self.perc, self.status)
                 save_data = False
            else:
                 print "WEIRDERROR. 'Percent Done:' in output, but regex doesnt match. <" + str(data) + ">"


        if 'Current Status:' in data:
            m = re.match(r"Current Status: \[(.*)\]", str(data))
            if m is not None:
                 self.status = m.group(1)
                 self.report_progress(self.perc, self.status)
            else:
                 print "WEIRDERROR. 'Current Status:' in output, but regex doesnt match. <" + str(data) + ">"

        if '-----[REPORT FOLLOWS]-----' in data:
            self.report_progress(99, 'Scan Complete')
            in_report = True

        if self.in_report:
            self.report += str(data) + '\n'

        print "ARACHNIOUTPUT %s" % (str(data))
        self.output += data

    def do_process_stderr(self, data):
        # TODO: Look for ConnectionError and display a message informing the user to launch arachni_rpcd.
        # `initialize': Connection refused - connect(2) (Arachni::RPC::Exceptions::ConnectionError)
        
        self.stderr += data
        print "ARACHNIERROR %s" %(str(data))
        #self.report_errors([str(data)])
        #self.report_finish("Encountered An Error; dying")
        #self.report_issues([{"Summary": data}])

    def do_process_ended(self, status):
        if self.stopping and status == 9:
            self.report_finish("STOPPED")
        elif status == 0:
            with open("stdout.txt", "w") as f:
                f.write(self.output)
            with open("stderr.txt", "w") as f:
                f.write(self.stderr)
            self.report_artifacts("Arachni Output", ["stdout.txt", "stderr.txt"])
            self.callbacks.report_issues(parse_arachni_output_for_issues(self.output))
            self.callbacks.report_finish()
        else:
            self.report_finish("FAILED")
