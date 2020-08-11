/*
A KBase module: kb_transyt_function_annotation
*/

module kb_transyt_function_annotation {
    typedef structure {
        string report_name;
        string report_ref;
    } ReportResults;

    /*
        This example function accepts any number of parameters and returns results in a KBaseReport
    */
    funcdef run_kb_transyt_function_annotation(mapping<string,UnspecifiedObject> params) returns (ReportResults output) authentication required;

};
