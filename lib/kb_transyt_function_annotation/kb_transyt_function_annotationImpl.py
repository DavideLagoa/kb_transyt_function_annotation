# -*- coding: utf-8 -*-
#BEGIN_HEADER
import logging
import os
import transyt_wrapper as tw
from installed_clients.KBaseReportClient import KBaseReport
import uuid

#END_HEADER


class kb_transyt_function_annotation:
    '''
    Module Name:
    kb_transyt_function_annotation

    Module Description:
    A KBase module: kb_transyt_function_annotation
    '''

    ######## WARNING FOR GEVENT USERS ####### noqa
    # Since asynchronous IO can lead to methods - even the same method -
    # interrupting each other, you must be *very* careful when using global
    # state. A method could easily clobber the state set by another while
    # the latter method is running.
    ######################################### noqa
    VERSION = "0.0.1"
    GIT_URL = ""
    GIT_COMMIT_HASH = ""

    #BEGIN_CLASS_HEADER
    #END_CLASS_HEADER

    # config contains contents of config file in a hash or None if it couldn't
    # be found
    def __init__(self, config):
        #BEGIN_CONSTRUCTOR
        self.callback_url = os.environ['SDK_CALLBACK_URL']
        self.shared_folder = config['scratch']
        self.config = config
        logging.basicConfig(format='%(created)s %(levelname)s: %(message)s',
                            level=logging.INFO)
        #END_CONSTRUCTOR
        pass


    def run_kb_transyt_function_annotation(self, ctx, params):
        """
        This example function accepts any number of parameters and returns results in a KBaseReport
        :param params: instance of mapping from String to unspecified object
        :returns: instance of type "ReportResults" -> structure: parameter
           "report_name" of String, parameter "report_ref" of String
        """
        # ctx is the context object
        # return variables are: output
        #BEGIN run_kb_transyt_function_annotation

        print(params)

        transyt_process = tw.transyt_wrapper(token=ctx['token'], params=params, config=self.config,
                                             callbackURL=self.callback_url, shared_folder=self.shared_folder)
        exit_code = transyt_process.run_transyt()

        output = {} # build an output that catches the error

        if exit_code == 0:
            output = transyt_process.process_output()
        elif exit_code == -3:

            report = KBaseReport(self.callback_url)
            report_params = {
                'warnings': ["TranSyT was already executed using the provided set of parameters for the same "
                            "database version."],
                'workspace_name': params['workspace_name'],
                'report_object_name': 'run_transyt_annotation_' + uuid.uuid4().hex,
                'objects_created': []
            }

            report_info = report.create_extended_report(report_params)

            output = {
                'report_name': report_info['name'],
                'report_ref': report_info['ref'],
                'fbamodel_id': params['genome_id']
            }

        print(os.system("ls " + self.shared_folder))

        #END run_kb_transyt_function_annotation

        # At some point might do deeper type checking...
        if not isinstance(output, dict):
            raise ValueError('Method run_kb_transyt_function_annotation return value ' +
                             'output is not type dict as required.')
        # return the results
        return [output]
    def status(self, ctx):
        #BEGIN_STATUS
        returnVal = {'state': "OK",
                     'message': "",
                     'version': self.VERSION,
                     'git_url': self.GIT_URL,
                     'git_commit_hash': self.GIT_COMMIT_HASH}
        #END_STATUS
        return [returnVal]
