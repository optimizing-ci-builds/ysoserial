import pandas as pd
import numpy as np
import os


def show_directories(file_path):
    with open(file_path, 'r') as f:
        df = pd.read_csv(file_path, sep=',')
        paths = df["file_name"].to_list()
        root = TreeNode("", None)

        for path in paths:
            find_and_insert(root, path.split("/")[1:])

        stack = []
        root.print(True, stack)
        return stack


class TreeNode:
    def __init__(self, name, parent):
        self.parent = parent
        self.name = name
        self.number_of_children = 0
        self.children = []

    def add_child(self, node):
        self.children.append(node)
        self.number_of_children+=1
        return node

    def print(self, is_root, stack):
        pre_0 = "    "
        pre_1 = "\u2502   "
        pre_2 = "\u251c\u2500\u2500 "
        pre_3 = "\u2514\u2500\u2500 "

        tree = self
        prefix = pre_2 if tree.parent and id(tree) != id(tree.parent.children[-1]) else pre_3

        while tree.parent and tree.parent.parent:
            if tree.parent.parent and id(tree.parent) != id(tree.parent.parent.children[-1]):
                prefix = pre_1 + prefix
            else:
                prefix = pre_0 + prefix

            tree = tree.parent

        if is_root:
            stack.append(self.name)
        else:
            stack.append(f"{prefix} {self.name} {str(self.number_of_children)}")

        for child in self.children:
            child.print(False, stack)


def find_and_insert(parent, edges):
    # Terminate if there is no edge
    if not edges:
        return

    # Find a child with the name edges[0] in the current node
    match = [tree for tree in parent.children if tree.name == edges[0]]

    # If there is already a node with the name edges[0] in the children, set "pointer" tree to this node. If there is no such node, add a node in the current tree node then set "pointer" tree to it
    tree = match[0] if match else parent.add_child(TreeNode(edges[0], parent))

    # Recursively process the following edges[1:]
    find_and_insert(tree, edges[1:])


df = pd.read_csv('/home/runner/inotify-logs.csv', sep = ';', names=['time', 'watched_filename', 'event_filename', 'event_name'])
df['event_filename'] = df['event_filename'].replace(np.nan, '')
steps = {}
starting_indexes = df[(df['event_filename'].str.contains('starting_')) & (df['event_name'] == 'CREATE')].index.to_list() + [df.shape[0]]
ending_indexes = [0] + df[(df['event_filename'].str.contains('starting_')) & (df['event_name'] == 'DELETE')].index.to_list()
starting_df = df[df['event_filename'].str.contains('starting_')]
touch_file_names = ['setup'] + [x.replace('starting_', '') for x in starting_df['event_filename'].value_counts().index.to_list()]
for starting_index, ending_index, touch_file_name in zip(starting_indexes, ending_indexes, touch_file_names):
    if touch_file_name == 'setup': continue
    steps[touch_file_name] = (ending_index, starting_index)
touch_file_names.pop(0)
df['watched_filename'] = df['watched_filename'] + df['event_filename']
df.drop('event_filename', axis=1, inplace=True)
df.rename(columns={'watched_filename':'file_name'}, inplace=True)
modify_df = df[df['event_name'] == 'MODIFY']
file_names = modify_df['file_name'].value_counts().index.to_list()
info = []
for file_name in file_names:
    last_access_step = ''
    last_modify_step = ''
    creation_step = ''
    if df[(df['file_name'] == file_name) & (df['event_name'] == 'MODIFY')].shape[0] == 0: last_modify_index = -1; last_modify_step = 'Not provided'
    else: last_modify_index = df[(df['file_name'] == file_name) & (df['event_name'] == 'MODIFY')].index.to_list()[-1]
    if df[(df['file_name'] == file_name) & (df['event_name'] == 'ACCESS')].shape[0] == 0: last_access_index = -1; last_access_step = 'Not provided'
    else: last_access_index = df[(df['file_name'] == file_name) & (df['event_name'] == 'ACCESS')].index.to_list()[-1]
    if df[(df['file_name'] == file_name) & (df['event_name'] == 'CREATE')].shape[0] == 0: creation_index = -1; creation_step = 'Not provided'
    else: creation_index = df[(df['file_name'] == file_name) & (df['event_name'] == 'CREATE')].index.to_list()[0]

    if last_access_index < last_modify_index:
        for touch_file_name, (starting_index, ending_index) in steps.items():
            if (last_access_index > starting_index) and (last_access_index < ending_index):
                last_access_step = touch_file_name.split('_')[1]
            if (last_modify_index > starting_index) and (last_modify_index < ending_index):
                last_modify_step = touch_file_name.split('_')[1]
            if (creation_index > starting_index) and (creation_index < ending_index):
                creation_step = touch_file_name.split('_')[1]
        if f'/home/runner/work/ysoserial/ysoserial/.git/' not in file_name:
            info.append({'file_name': file_name, 'last_access_index': last_access_index, 'last_modify_index': last_modify_index, 'creation_index': creation_index, 'last_access_step':last_access_step , 'last_modify_step':last_modify_step, 'creation_step': creation_step})
os.mkdir(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis')
os.mkdir(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details')
info_df = pd.DataFrame(info)
step_statistics = []
for step, (starting_index, ending_index) in steps.items():
    step_name = step.split('_')[1]
    if step_name == 'finished': continue
    c = info_df['creation_step'] == step_name
    m = info_df['last_modify_step'] == step_name
    a = info_df['last_access_step'] == step_name
    # _a  is accessed in another step
    # __a is never accessed
    _a  = (info_df['last_access_step'] != step_name) & (info_df['last_access_index'] != -1)
    __a = info_df['last_access_index'] == -1
    cma = info_df[c & m & a].shape[0]
    cm_a = info_df[c & m & _a].shape[0]
    cm__a = info_df[c & m & __a].shape[0]
    c_ma = info_df[c & ~m & a].shape[0]
    c_m_a = info_df[c & ~m & _a].shape[0]
    c_m__a = info_df[c & ~m & __a].shape[0]
    _cma = info_df[~c & m & a].shape[0]
    _cm_a = info_df[~c & m & _a].shape[0]
    _cm__a = info_df[~c & m & __a].shape[0]
    _c_ma = info_df[~c & ~m & a].shape[0]
    _c_m_a = info_df[~c & ~m & _a].shape[0]
    _c_m__a = info_df[~c & ~m & __a].shape[0]
    created_file_count = info_df[c].shape[0]
    modified_file_count = info_df[m].shape[0]
    starting_time = list(map(int, df.iloc[starting_index]['time'].split(':')))
    if ending_index == len(df): ending_time = list(map(int, df.iloc[ending_index-1]['time'].split(':')))
    else: ending_time = list(map(int, df.iloc[ending_index]['time'].split(':')))
    hour = ending_time[0] - starting_time[0]
    if starting_time[1] > ending_time[1]:
        minute = ending_time[1] - starting_time[1] + 60
        hour -= 1
    else: minute = ending_time[1] - starting_time[1]
    if starting_time[2] > ending_time[2]:
        second = ending_time[2] - starting_time[2] + 60
        minute -= 1
    else: second = ending_time[2] - starting_time[2]
    total_seconds = second + (minute * 60) + (hour * 60 * 60)
    if step_name != '':
        os.mkdir(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}')
        if created_file_count > 0: info_df[c]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/c.csv')
        if modified_file_count > 0: info_df[m]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/m.csv')
        if cma > 0: info_df[c & m & a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/cma.csv')
        if cm_a > 0: info_df[c & m & _a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/cm_a.csv')
        if cm__a > 0: info_df[c & m & __a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/cm__a.csv')
        if c_ma > 0: info_df[c & ~m & a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/c_ma.csv')
        if c_m_a > 0: info_df[c & ~m & _a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/c_m_a.csv')
        if c_m__a > 0: info_df[c & ~m & __a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/c_m__a.csv')
        if _cma > 0: info_df[~c & m & a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_cma.csv')
        if _cm_a > 0: info_df[~c & m & _a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_cm_a.csv')
        if _cm__a > 0: info_df[~c & m & __a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_cm__a.csv')
        if _c_ma > 0: info_df[~c & ~m & a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_c_ma.csv')
        if _c_m_a > 0: info_df[~c & ~m & _a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_c_m_a.csv')
        if _c_m__a > 0: info_df[~c & ~m & __a]["file_name"].to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/step-details/{step_name}/_c_m__a.csv')
        step_statistics.append({'step_name': step_name, '#c': created_file_count, '#m': modified_file_count,
        'cma': cma, 'cm_a': cm_a, 'cm__a': cm__a, 'c_ma': c_ma, 'c_m_a': c_m_a, 'c_m__a': c_m__a, '_cma': _cma, '_cm_a': _cm_a, '_cm__a': _cm__a, '_c_ma': _c_ma, '_c_m_a': _c_m_a, '_c_m__a': _c_m__a, 'time': total_seconds})
step_df = pd.DataFrame(step_statistics)
step_df.to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/steps.csv')
info_df.to_csv(f'/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/files.csv')
directories = show_directories('/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/files.csv')
string_version = ''
for line in directories:
    string_version += line + '\n'
with open("/home/runner/work/ysoserial/ysoserial/optimizing-ci-builds-ci-analysis/directories.txt", "w+", encoding="utf-8") as f:
    f.write(string_version)