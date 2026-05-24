import sys,os,argparse
import curses
import json
import time
import logging
from pathlib import Path
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
class FileWindow:
    def __init__(self,h,w,y,x):
        self.win = curses.newwin(h,w,y,x)
        self.win.border(0,0,0,0,0,0,0,0)
        self.current_row = 0
        self.h = h
        self.w = w       
    def __getattr__(self,attr):
        return getattr(self.win,attr)
    def build_pad(self):
        self.pad = curses.newpad(Results.n_row, self.w)
        meter_start = 40
        max_w_meter = self.w - meter_start
        for i, k in enumerate(Results.dict_result.keys()):
            stats = Results.dict_result[k]['stats']
            if stats == 'OK':
                wtime = Results.dict_result[k]['walltime']
                value = Results.dict_result[k]['value']
                tstep = Results.dict_result[k]['timestep']
                self.pad.addstr(i,1,  k) # folder name
                self.pad.addstr(i,10, stats)
                self.pad.addstr(i,15, f'{wtime:4.0f}')
                self.pad.addstr(i,23, f'{value:4.0f}')
                self.pad.addstr(i,31, str(tstep))
                meter = '|'* int(tstep*max_w_meter/1000)
                self.pad.addstr(i,meter_start-1,'[')
                self.pad.addstr(i,self.w-4,']')
                if tstep < 400:
                    self.pad.addstr(i,meter_start, meter, curses.color_pair(3) | curses.A_REVERSE)
                elif tstep <800:
                    self.pad.addstr(i,meter_start, meter, curses.color_pair(2) | curses.A_REVERSE)
                else:
                    self.pad.addstr(i,meter_start, meter, curses.color_pair(1) | curses.A_REVERSE)
            else:
                self.pad.addstr(i,1,  k)
                self.pad.addstr(i,10, stats, curses.color_pair(1))
                self.pad.addstr(i,meter_start-1,'[')
                self.pad.addstr(i,meter_start,'.'*(max_w_meter-4))
                self.pad.addstr(i,self.w-4,']')
    def rf(self):
        self.win.clear()
        self.win.border(0,0,0,0,0,0,0,0)
        self.win.addstr(0,1," Folder | ")
        self.win.addstr(0,10,"Stat|", curses.color_pair(2))
        self.win.addstr(0,15," Wtime |", curses.color_pair(2))
        self.win.addstr(0,23," Value |", curses.color_pair(3))
        self.win.addstr(0,31," Time-steps ", curses.color_pair(4))
        hmax, wmax = self.win.getmaxyx()
        self.win.addstr(hmax-1,1,str(len(Results.dict_result)))
        self.win.refresh()
        self.pad.refresh(self.current_row, 0,3,1, hmax-1, wmax-3)
class TopWindow:
    def __init__(self,h,w,y,x):
        self.win = curses.newwin(h,w,y,x)
    def __getattr__(self,attr):
        return getattr(self.win,attr)
    def rf(self):
        self.win.addstr(0,1,"** Collecting and visualizing results** ")
        self.win.addstr(1,1,Results.target_path)
        self.win.refresh()
 
def draw_menu(stdscr):
    # preparation
    if curses.has_colors():
        curses.start_color()
        curses.init_pair(1,curses.COLOR_RED,    curses.COLOR_BLACK)
        curses.init_pair(2,curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3,curses.COLOR_GREEN,  curses.COLOR_BLACK)
        curses.init_pair(4,curses.COLOR_BLUE,   curses.COLOR_BLACK)
    curses.cbreak()
    curses.curs_set(0)
    curses.noecho()
    stdscr.keypad(True)
    stdscr.refresh()
    h, w = stdscr.getmaxyx()   
    # Initialization
    h_file = h - 2;
    w_file = int(w * 0.3);   
    twin = TopWindow(2, w, 0, 0)
    fwin = FileWindow(h_file, w, 2, 0)
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
    fwin.build_pad()
    twin.rf()
    fwin.rf()
    # Wait for next input
    while True:
        k = stdscr.getkey()
        if k in ['q', 'Q']:
            break
        elif k == "KEY_DOWN" and fwin.current_row < Results.n_row-1:
            fwin.current_row += 1
        elif k == "KEY_UP" and fwin.current_row > 0:
            fwin.current_row -= 1
        elif k == "KEY_PPAGE":
            if fwin.current_row > h_file:
                fwin.current_row -= h_file
            else:
                fwin.current_row = 0
        elif k == "KEY_NPAGE":
            if fwin.current_row < (Results.n_row - h_file):
                fwin.current_row += h_file
        fwin.rf()
 
def visualize():
    logging.basicConfig(filename='log.harvest', level=logging.INFO,
                        format='%(asctime)s-%(levelname)s-%(message)s')
    logger.info('visualizse() started')
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True)
    parser.add_argument('--overwrite', type=str, required=False)
    args = parser.parse_args()
    dir_path = args.path
    if (not os.path.exists(dir_path)):
        print("!!!! "+ dir_path + " doesn't exist. We stop here")
        sys.exit()
    curses.wrapper(draw_menu)
 
if __name__ == "__main__":
    if sys.version_info < (3,10):
        print("Requires Python 3.10 or newer. We exit now")
        sys.exit()
    visualize()
