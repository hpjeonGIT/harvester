import sys,os,argparse
import time
import logging
import json
from pathlib import Path
from bokeh.io import show
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, DataTable, TableColumn, HTMLTemplateFormatter, Div
from bokeh.layouts import column


logger = logging.getLogger(__name__)
 
class Results:
    target_path = ''   
    dict_result = {}
    overwrite = ''
    n_row = 0
    n_col = 80 # may need extension
    @classmethod
    def find_read(cls):
        dict_tmp = {}
        logger.info('Parsing folders...')
        with os.scandir(cls.target_path) as entries:
            for entry in entries:
                if os.access(entry, os.R_OK and entry.is_dir()):
                    target_file = cls.target_path + "/" + entry.name + "/summary.json"
                    if os.access(target_file, os.R_OK):                   
                        with open(target_file, 'r') as f:
                            res = json.load(f)
                            if len(res) > 0:
                                res['stats'] = 'OK'
                            else:                               
                                res = {'stats':'<No result>'}
                    elif entry.is_dir():
                        res = {'stats':'<File Not Accessible>'}    
                elif entry.is_dir():
                    res = {'stats':'<Dir Not Accessible>'}
                if entry.is_dir(): # local files are ignored. Only sub-folders
                    dict_tmp[entry.name] = res
        #sorting
        cls.dict_result = dict(sorted(dict_tmp.items()))
        cls.n_row = len(cls.dict_result)
        if len(cls.dict_result)> 0:
            with open(cls.target_path + "/all_summary.json",'w') as f:
                json.dump(cls.dict_result,f,indent=4)
            # find faulty ones
            tmp_dict = {}
            for k in cls.dict_result.keys():
                if cls.dict_result[k]['stats'] != 'OK':
                    tmp_dict[k] = cls.dict_result[k]
            if len(tmp_dict) > 0:
                with open(cls.target_path + "/list_broken.json",'w') as f:
                    json.dump(tmp_dict,f,indent=4)
        logger.info('Harvesting data completed')
 
def run_bokeh():
    # argument
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--overwrite', type=str, required=False)
    args = parser.parse_args()
    Results.target_path = args.path
    if args.overwrite:
        Results.overwrite = args.overwrite
    check_file = Path(Results.target_path + "/all_summary.json")
    if check_file.exists() and not Results.overwrite:
        logger.info(f'all_summary.json file is found. Parsing folders will be skipped')
        with open(Results.target_path + "/all_summary.json",'r') as f:
           try:
               Results.dict_result = json.load(f)
               Results.n_row = len(Results.dict_result)
           except json.decoder.JSONDecodeError:
               logger.info(f'Error when loading all_summary.json. We parse folders')
               Results.find_read()              
    else:
        Results.find_read()
    #
    dirname_list = []
    stat_list = []
    wtime_list = []
    val_list = []
    tstep_list = []
    graph_list = []
    for k,v in zip(Results.dict_result.keys(), Results.dict_result.values()):
        dirname_list.append(k)
        stat_list.append(v['stats'])
        if v['stats'] == 'OK':
            wtime_list.append(f'{v['walltime']:6.1f}')
            val_list.append(f'{v['value']:6.1f}')
            tstep_list.append(v['timestep'])
            graph_list.append('|'*int(v['timestep']/10))
        else:
            wtime_list.append('NA')
            val_list.append('NA')
            tstep_list.append('NA')
            graph_list.append('.'*100)
    # Data reformat along column direction
    data_reformat = {"dirname": dirname_list, "stat": stat_list, 
                     "wtime": wtime_list,"val":val_list,
                     "tstep":tstep_list,"graph":graph_list}        
    source = ColumnDataSource(data=data_reformat)
    template="""
                <div style="color:<%= tstep > 500 ? 'red' : 'green' %>; ">
                <%= value %>
                </div>
                """
    formatter =  HTMLTemplateFormatter(template=template)
    columns = [
        TableColumn(field="dirname", title="Folder Name", width=200),
        TableColumn(field="stat", title="Stat",width=300),
        TableColumn(field="wtime", title="Wall Time"),
        TableColumn(field="val", title="Value"),
        TableColumn(field="tstep", title="Time Step"),
        TableColumn(field="graph", title="Graphs",formatter=formatter,width=800)
    ]
    data_table = DataTable(source=source, columns=columns,width=1000)
    d = Div(
        text="""
        <h1>Harvesting results and summarizing them</h1>
        """)
    layout = column(d, data_table)
    show(layout)            
 
def visualize():
    logging.basicConfig(filename='log.harvest', level=logging.INFO,
                        format='%(asctime)s-%(levelname)s-%(message)s')
    logger.info('visualize() started')
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--overwrite', type=str, required=False)
    args = parser.parse_args()
    dir_path = args.path
    if (not os.path.exists(dir_path)):
        print("!!!! "+ dir_path + " doesn't exist. We stop here")
        sys.exit()
    run_bokeh()
 
if __name__ == "__main__":
    if sys.version_info < (3,10):
        print("Requires Python 3.10 or newer. We exit now")
        sys.exit()
    visualize()
