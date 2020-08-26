import cobrakbase
import subprocess
import os
import time
import datetime
import re
from installed_clients.WorkspaceClient import Workspace as workspaceService
import kb_transyt_report
import shutil

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True, callbackURL=None,
                 shared_folder=None):

        self.token = token
        self.params = params
        self.config = config
        self.callback_url = callbackURL
        self.shared_folder = shared_folder
        #self.inputs_path = '/Users/davidelagoa/Desktop/test/processingDir/'
        self.inputs_path = '/workdir/processingDir/'
        self.results_path = '/workdir/resultsDir/'
        #self.results_path = '/Users/davidelagoa/Desktop/test/resultsDir/'
        self.java = '/opt/jdk/jdk-11.0.1/bin/java'
        self.transyt_jar = '/opt/transyt/transyt.jar'
        self.results_path = self.inputs_path + "results/transport_genes_annotation.txt"
        self.report_template_html = "/kb/module/conf/report_template.html"
        self.ontology_key = "transyt"

        self.taxonomy_id = None
        self.genome = None
        self.sso_ref = None
        self.kbase = None
        self.ws_client = None
        self.ontologies_data = None
        self.ontologies_data_version = None

        if self.config is not None:
            self.kbase = cobrakbase.KBaseAPI(token, config=self.config)
            self.ws_client = workspaceService(config["workspace-url"])
        else:
            self.ws_client = workspaceService("https://kbase.us/services/ws/")

        if deploy_database:
            self.deploy_neo4j_database()
    '''
    def run_test(self, genome_id, narrative_id):

        if self.kbase is None:
            self.kbase = cobrakbase.KBaseAPI(self.token, dev=False)
            self.results_path = "/Users/davidelagoa/Desktop/biolog_data_complete2/tests/ontologies/results/results/transport_genes_annotation.txt"

        self.download_ontology_data()

        genome = self.kbase.get_object(genome_id, narrative_id)

        sso_event = self.make_sso_ontology_event()
        ontology_event_index = 0

        go = True

        if 'ontology_events' in genome:
            for previous_event in genome['ontology_events']:
                if sso_event["description"] == previous_event["description"]:
                    go = False
            if go:
                genome['ontology_events'].append(sso_event)
                ontology_event_index += len(genome['ontology_events']) - 1
        else:
            genome['ontology_events'] = [sso_event]

        ontologies_present = {}

        # used to build the report
        new_annotations = {}
        warnings = []

        if go:
            results = self.get_genes_annotations()

            for feature in genome['features']:
                if feature["id"] in results.keys():
                    for tc in results[feature["id"]]:
                        if "ontology_terms" not in feature:
                            feature["ontology_terms"] = {self.ontology_key: {}}

                        if tc in feature["ontology_terms"]["transyt"]:
                            feature["ontology_terms"][self.ontology_key][tc].append(ontology_event_index)
                        else:
                            feature["ontology_terms"][self.ontology_key][tc] = [ontology_event_index]

                            if feature["id"] not in new_annotations:
                                new_annotations[feature["id"]] = []
                            new_annotations[feature["id"]].append(tc + " - " + self.ontologies_data[tc]["name"])

                        if tc not in ontologies_present:
                            ontologies_present[tc] = self.ontologies_data[tc]["name"]

            self.save_ontologies_present(genome, ontologies_present)

            self.kbase.save_object(genome_id, narrative_id, "KBaseGenomes.Genome", genome)

            report_path = "/Users/davidelagoa/Desktop/biolog_data_complete2/tests/ontologies/results/results/report.html"
            self.report_template_html = "/Users/davidelagoa/PycharmProjects/kb_transyt_function_annotation/conf/report_template.html"

            if len(new_annotations) == 0:
                new_annotations = None
                warnings.append("TranSyT was not able to find new annotations using this set of parameters.")

        if not go:
            warnings.append("TranSyT was already executed using this set of parameters for the same database version.")

        objects_created = []
        kb_transyt_report.generate_report(report_path, warnings, new_annotations, objects_created, self.callback_url, self.ws,
                                          genome_id, self.results_path, self.report_template_html)
    '''
    def save_ontologies_present(self, genome, ontologies_present):

        if "ontologies_present" in genome:
            if self.ontology_key in genome["ontologies_present"]:
                for tc in ontologies_present:
                    if tc not in genome["ontologies_present"][self.ontology_key]:
                        genome["ontologies_present"][self.ontology_key][tc] = ontologies_present[tc]
            else:
                genome["ontologies_present"][self.ontology_key] = ontologies_present
        else:
            genome["ontologies_present"] = {self.ontology_key: ontologies_present}

    def run_transyt(self):

        self.genome = self.kbase.get_object(self.params['genome_id'], self.params['workspace_name'])

        if not os.path.exists(self.inputs_path):
            os.makedirs(self.inputs_path)

        self.inputs_preprocessing(self.genome)

        if not os.path.exists(self.results_path):
            os.makedirs(self.results_path)

        transyt_subprocess = subprocess.Popen([self.java, "-jar", "--add-exports",
                                               "java.base/jdk.internal.misc=ALL-UNNAMED",
                                               "-Dio.netty.tryReflectionSetAccessible=true", "-Dworkdir=/workdir",
                                               "-Dlogback.configurationFile=/kb/module/conf/logback.xml",
                                               "-Xmx4096m", self.transyt_jar, "4", self.inputs_path])

        exit_code = transyt_subprocess.wait()

        print("jar process finished! exit code: " + str(exit_code))

        return exit_code

    def inputs_preprocessing(self, genome):

        '''
        # detect taxa
        ref_data = self.kbase.get_object_info_from_ref(genome['taxon_ref'])
        ktaxon = self.kbase.get_object(ref_data.id, ref_data.workspace_id)
        self.scientific_lineage = ktaxon['scientific_lineage']
        self.taxonomy_id = ktaxon['taxonomy_id']
        '''

        # fix this
        self.taxonomy_id = 83333

        self.genome_to_faa(genome)
        self.params_to_file()

    def genome_to_faa(self, genome):
        faa_features = []
        for feature in genome['features']:
            if 'protein_translation' in feature and feature['protein_translation'] is not '':
                faa_features.append('>' + feature['id'] + '\n' + feature['protein_translation'])

        with open(self.inputs_path + 'protein.faa', 'w') as f:
            f.write('\n'.join(faa_features))
            f.close()


    def params_to_file(self):

        with open(self.inputs_path + 'params.txt', 'w') as f:

            for key in self.params:
                f.write(key + "\t" + str(self.params[key]) + "\n")

            f.write('taxID' + "\t" + str(self.taxonomy_id) + "\n")
            f.close()

    def process_output(self):

        self.download_ontology_data()

        sso_event = self.make_sso_ontology_event()
        ontology_event_index = 0

        go = True

        if 'ontology_events' in self.genome:
            for previous_event in self.genome['ontology_events']:
                if sso_event["description"] == previous_event["description"]:
                    go = False
            if go:
                self.genome['ontology_events'].append(sso_event)
                ontology_event_index += len(self.genome['ontology_events']) - 1
        else:
            self.genome['ontology_events'] = [sso_event]

        ontologies_present = {}

        # used to build the report
        new_annotations = {}
        warnings = []
        shared_results_file = ""

        if go:
            results = self.get_genes_annotations()

            for feature in self.genome['features']:
                if feature["id"] in results.keys():
                    for tc in results[feature["id"]]:
                        if "ontology_terms" not in feature:
                            feature["ontology_terms"] = {self.ontology_key: {}}

                        if tc in feature["ontology_terms"]["transyt"]:
                            feature["ontology_terms"][self.ontology_key][tc].append(ontology_event_index)
                        else:
                            feature["ontology_terms"][self.ontology_key][tc] = [ontology_event_index]

                            if feature["id"] not in new_annotations:
                                new_annotations[feature["id"]] = []
                            new_annotations[feature["id"]].append(tc + " - " + self.ontologies_data[tc]["name"])

                        if tc not in ontologies_present:
                            ontologies_present[tc] = self.ontologies_data[tc]["name"]

            self.save_ontologies_present(self.genome, ontologies_present)

            self.kbase.save_object(self.params["genome_id"], self.params['workspace_name'],
                                   "KBaseGenomes.Genome", self.genome)

            shared_results_file = self.shared_folder + "/" + self.params["genome_id"] + "tc_numbers.txt"
            shutil.copyfile(self.results_path, shared_results_file)

            if len(new_annotations) == 0:
                new_annotations = None
                warnings.append("TranSyT was not able to find new annotations using the provided set of parameters.")

        if not go:
            warnings.append("TranSyT was already executed using the provided set of parameters for the same "
                            "database version.")

        objects_created = []
        report_path = self.shared_folder + "/report.html"
        report_info = kb_transyt_report.generate_report(report_path, warnings, new_annotations, objects_created,
                                                        self.callback_url, self.params['workspace_name'],
                                                        self.params["genome_id"], shared_results_file,
                                                        self.report_template_html)
        output = {
            'report_name': report_info['name'],
            'report_ref': report_info['ref']
        }

        return output

    def download_ontology_data(self):
        ontologies_object = self.ws_client.get_objects([{"ref": "KBaseOntology/transyt_tc_ontologies"}])[0]
        sso_info = ontologies_object["info"]
        self.ontologies_data_version = ontologies_object["data"]["data_version"]
        self.sso_ref = str(sso_info[6]) + "/" + str(sso_info[0]) + "/" + str(sso_info[4])
        self.ontologies_data = ontologies_object["data"]["term_hash"]

    def make_sso_ontology_event(self):
        """

        :param sso_ref: Reference to the annotation library set
        :return: Ontology_event to be appended to the list of genome ontology events
        """
        time_string = str(
            datetime.datetime.fromtimestamp(time.time()).strftime('%Y_%m_%d_%H_%M_%S'))
        yml_text = open('/kb/module/kbase.yml').read()
        version = re.search("module-version:\n\W+(.+)\n", yml_text).group(1)

        description = "auto_accept_evalue:" + str(self.params["auto_accept_evalue"]) \
                      + "__percent_accept:" + str(self.params["percent_accept"]) \
                      + "__limit_evalue_accept:" + str(self.params["limit_evalue_accept"]) \
                      + "__blast_evalue_threshold:" + str(self.params["blast_evalue_threshold"]) \
                      + "__bitscore_threshold:" + str(self.params["bitscore_threshold"]) \
                      + "__query_coverage_threshold:" + str(self.params["query_coverage_threshold"]) \
                      + "__similarity_score:" + str(self.params["similarity"]) \
                      + "__alpha_families:" + str(self.params["alpha_families"]) \
                      + "__data_version:" + str(self.ontologies_data_version)

        return {
            "method": "transyt_transporters_annotation",
            "description":description,
            "method_version": version,
            "timestamp": time_string,
            "id": self.ontology_key,
            "ontology_ref": self.sso_ref
        }

    def get_genes_annotations(self):

        dic = {}

        for line in open(self.results_path, "r"):

            if len(line.strip()) > 0:

                line_split = line.split("\t")

                gene = line_split[0].replace(">", "").strip()
                tc_numbers = line_split[1].strip().split(";")

                dic[gene] = tc_numbers

        return dic


    def deploy_neo4j_database(self):

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.2/bin/neo4j", "start"])
