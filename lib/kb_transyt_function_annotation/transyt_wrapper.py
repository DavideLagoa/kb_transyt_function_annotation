import cobrakbase
import subprocess
import os
import cobra

class transyt_wrapper:

    def __init__(self, token=None, params=None, config=None, deploy_database=True, callbackURL=None):

        self.params = params
        self.config = config
        self.callback_url = callbackURL
        #self.inputs_path = '/Users/davidelagoa/Desktop/test/processingDir/'
        self.inputs_path = '/workdir/processingDir/'
        self.results_path = '/workdir/resultsDir/'
        #self.results_path = '/Users/davidelagoa/Desktop/test/resultsDir/'
        self.java = '/opt/jdk/jdk-11.0.1/bin/java'
        self.transyt_jar = '/opt/transyt/transyt.jar'
        self.ref_database = 'ModelSEED'

        self.ws = None
        self.taxonomy_id = None
        self.genome_id = None
        self.scientific_lineage = None
        self.genome = None

        self.kbase = cobrakbase.KBaseAPI(token, config=self.config)

        if deploy_database:
            self.deploy_neo4j_database()


    def run_transyt(self, model_obj_name = None, genome_obj_name = None, narrative_id = None):

        if self.ws is None:
            self.ws = narrative_id

        if narrative_id is None:
            self.ws = self.params['workspace_name']
            self.genome = self.kbase.get_object(self.params['genome_id'], self.ws)
        else:
            self.genome = self.retrieve_test_data(model_obj_name, genome_obj_name, narrative_id)

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


    def retrieve_test_data(self, model_obj_name, genome_obj_name, narrative_id):

        if self.params is None:
            self.params = {'genome_id': genome_obj_name}

        genome = self.kbase.get_object(genome_obj_name, narrative_id)

        return genome


    def inputs_preprocessing(self, genome):

        # detect taxa
        ref_data = self.kbase.get_object_info_from_ref(genome['taxon_ref'])
        ktaxon = self.kbase.get_object(ref_data.id, ref_data.workspace_id)
        self.scientific_lineage = ktaxon['scientific_lineage']
        self.taxonomy_id = ktaxon['taxonomy_id']

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
            f.write('reference_database' + "\t" + self.ref_database)
            f.close()

    def process_output(self):

        dic = {}

        with open(self.results_path + '/results/transport_genes_annotation.txt', 'r') as f:
            for line in f:
                split_line = line.split("\t")
                gene = split_line[0].strip()
                tc_numbers = split_line[1].strip()

                dic[gene] = tc_numbers

        for entry in self.genome["cdss"]:
            gene = entry["parent_gene"]
            if gene in dic:
                entry["ontology_terms"]["TranSyT"] = dic[gene]

        self.kbase.save_object(self.params['genome_id'], self.ws, "KBaseGenomes.Genome", self.genome)



    def deploy_neo4j_database(self):

        subprocess.Popen(["/opt/neo4j/neo4j-community-4.0.2/bin/neo4j", "start"])
