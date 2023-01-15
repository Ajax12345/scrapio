import collections, copy, json
import typing, itertools

def group_results_collections(cols):
    chosen_row = next(([i, a['unique']['result']['rows']] for i, a in enumerate(cols) if a['unique']['result']['match']), None)
    _chosen, _col_key = [] if chosen_row is None else chosen_row[-1], 0 if chosen_row is None else chosen_row[0]
    if not _chosen:
        return {'result':False, 'data':[{**i, 'has_group':False, 'col':[[k] for k in i['unique']['nodes']]} for i in cols]}
    
    group_mapper, unmatched_mapper = {i:{str(l['lid']):[] for l in cols} for i in _chosen}, {str(l['lid']):[] for l in cols}
    for col in cols:
        for node in col['unique']['nodes']:
            #_id_f = next((i for i in node['tree'] if i in group_mapper), None) #old way
            _id_f = [i for i in node['tree'] if i in group_mapper]
            if _id_f:
                group_mapper[_id_f[-1]][str(col['lid'])].append(node)
            else:
                unmatched_mapper[str(col['lid'])].append(node)
    
    _chosen_id_set, _col_key_count_check = ','.join(_chosen), 0
    _final_results = []
    for i, a in enumerate(cols):
        _first_lookup = [j[str(a['lid'])] for j in group_mapper.values()]
        _final_results.append({**a, 'is_group_key':_col_key == i - 1, 'id':str(a['lid']), 'has_group':True, 'group_id_row':_chosen_id_set, 'col':[*([] if not any(_first_lookup) else _first_lookup), *[[y] for y in unmatched_mapper[str(a['lid'])]]]})

    return {'result':True, 'data':_final_results}
    

def all_col_match(vals:typing.List[dict], ind:int, _map:dict) -> bool:
    return all(len(i['tree']) > ind and _map[i['tree'][ind]] == 1 for i in vals)

def get_subnodes_unique_ind(subnodes:typing.List[dict]) -> typing.List[dict]:
    _n = next((i for i, a in enumerate(zip(*[x['n']['tree'] for x in subnodes])) if len(set(a)) == len(subnodes)), None)
    return {'result':False} if _n is None else {'result':True, 'ind':_n, 'nodes':subnodes}
    '''
    for i in range(0, min([len(x['n']['tree']) for x in subnodes])):
        if len(set([x['n']['tree'][i] for x in subnodes])) == len(subnodes):
            return {'result':True, 'ind':i, 'nodes':subnodes}
    return {'result':False} 
    '''

def unique_paths_collections(all_nodes):
    inner_result = {'match':False, 'rows':[]}
    if len(all_nodes) <= 1:
        return {'result':inner_result, 'nodes':all_nodes}
    

    _len_groups = collections.defaultdict(list)
    for i, a in enumerate(all_nodes):
        _len_groups[len(a['tree'])].append({'ind':i, 'n':a})
    
    g_1, e_1 = [a for a, b in _len_groups.items() if len(b) > 1], [a for a, b in _len_groups.items() if len(b) == 1]
    if not g_1:
        g_1 = e_1
        e_1 = []
    
    for e in e_1:
        _len_groups[min(g_1, key=lambda x:abs(x - e))].extend(_len_groups[e])

    _groups_inds = [get_subnodes_unique_ind(_len_groups[i]) for i in g_1]
    if all(i['result'] for i in _groups_inds):
        _full_mapping = {}
        for g in _groups_inds:
            for s in g['nodes']:
                _full_mapping[s['ind']] = s['n']['tree'][g['ind']]

        inner_result['match'] = True
        for i in range(len(all_nodes)):
            inner_result['rows'].append(_full_mapping[i])

    '''
    #old implementation
    _tree_freqs = collections.Counter([i for b in all_nodes for i in b['tree']])
    _f_ind = next((i for i, a in enumerate(all_nodes[0]['tree']) if _tree_freqs[a] == 1 and all_col_match(all_nodes, i, _tree_freqs)), None)
    if _f_ind is not None:
        inner_result['match'] = True
        inner_result['path_ind'] = _f_ind
     
    if inner_result['match']:
        inner_result['rows'] = [i['tree'][_f_ind] for i in all_nodes]
    '''
    return {'result':inner_result, 'nodes':all_nodes}

def form_table_vals(tableid:str, template:dict, t_data:dict, vals:list) -> typing.Any:
    d = collections.defaultdict(list)
    for i in vals:
        d[i['tableid']].append(i)

    final_results = []
    if t_data:
        for a, b in d.items():
            _full_array = [{**i, 'label':template[str(i['tid'])][str(i['id'])]['label'], 'lid':int(i['id']), 'cols':[{**j, 'tid':str(i['tid'])} for x, y in t_data[str(i['tid'])]['levels'].items() for j in y['labels'].get(str(i['id']), [])]} for i in b]    
            _f_with_unique = [{**i, 'unique':unique_paths_collections(i['cols'])} for i in _full_array]
            final_results.extend(group_results_collections(_f_with_unique)['data'])

    return final_results

def get_table_joins(_collections:dict, p_clct_id:str) -> typing.Iterator:
    for i in _collections['tables']:
        if i['parent'] is not None and int(i['parent']) == int(p_clct_id):
            yield from [{**k, 'tableid':str(i['clct_id'])} for k in _collections['table_records'][i['clct_id']]]
            yield from get_table_joins(_collections, i['clct_id'])

def form_display_tables(_collections:dict) -> dict:
    return {str(i['clct_id']):[*[{**k, 'tableid':str(i['clct_id'])} for k in _collections['table_records'][str(i['clct_id'])]], *get_table_joins(_collections, str(i['clct_id']))] for i in _collections['tables'] if i['parent'] is None}

def run_generic_flattening(data:list) -> typing.List[dict]:
    _grouped_container_data = []
    _current_group = []
    _current_group_type = None
    _current_group_similarity = None
    for i in data:
        if _current_group_type is None:
            _current_group_type = i['has_group']
            if i['has_group']:
                _current_group_similarity = i['group_id_row']
            
            _current_group.append(i)

        elif _current_group_type == i['has_group']:
            if i['has_group']:
                if _current_group_similarity == i['group_id_row']:
                    _current_group.append(i)
                
                else:
                    _grouped_container_data.append({'is_group':True, 'data':_current_group})
                    _current_group = [i]
                    _current_group_similarity = i['group_id_row']
            
            else:
                _current_group.append(i)
            
        else:
            _grouped_container_data.append({'is_group':_current_group_type, 'data':_current_group})
            _current_group_type = i['has_group']
            if i['has_group']:
                _current_group_similarity = i['group_id_row']
            
            _current_group = [i]

    _grouped_container_data.append({'is_group':_current_group_type, 'data':_current_group})
    return _grouped_container_data

def __eq_gb(col:dict, gb:dict) -> bool:
    #return parseInt(col.tableid) === parseInt(gb.tableid) && parseInt(col.tid) === parseInt(gb.tid) && parseInt(col.id) === parseInt(gb.id) 
    return all(int(col[i]) == int(gb[i]) for i in ['tableid', 'tid', 'id'])

def tabular_structure_display(data:typing.List[dict], groupby=None) -> dict:
    _max_col_length, full_obj_results = max([len(i['col']) for i in data]), {'headers':[], 'vals':[], 'is_tabular':True}
    for i in data:
        _max_href = (lambda x:0 if not x else max(x))([sum(k['is_a'] for k in x) for x in i['col']])
        _max_text = max(map(len, i['col']))
        _structured_col_payload = {'labels':[], 'id':i['id'], 'tid':i['tid'], 'vals_by_row':[], 'ind':'1'}
        for c in i['col']:
            _temp_href_m, _temp_text_m = _max_href, _max_text
            _temp_header_c, _temp_row_c = [], []
            _h_count = 0
            for j in filter(lambda x:x['is_a'], c):
                _temp_header_c.append({'text':i["label"] if not _h_count else f'{i["label"]}({_h_count})', 'is_link':False, 'is_first':not _h_count, 'has_groupby':(groupby is not None and __eq_gb(i, groupby)), 'tableid':i['tableid'], 'id':i['id'], 'tid':i['tid']})
                _temp_header_c.append({'text':f'{i["label"]}(url)' if not _h_count else f'{i["label"]}(url)({_h_count})', 'is_link':True, 'is_first':False})
                _temp_row_c.append({'is_link':False, 'text':j['text'], 'show_more_vals':False, 'hid':i['tid'], 'lid':i['id']})
                _temp_row_c.append({'is_link':True, 'text':j['href'], 'show_more_vals':False})
                _temp_href_m -= 1
                _temp_text_m -= 1
                _h_count += 1

            for j in filter(lambda x:not x['is_a'], c):
                _temp_header_c.append({'text':f'{i["label"]}({_h_count})' if _h_count else i["label"], 'is_link':False, 'is_first':not _h_count, 'has_groupby':(groupby is not None and __eq_gb(i, groupby)), 'tableid':i['tableid'], 'id':i['id'], 'tid':i['tid']})
                _temp_row_c.append({'is_link':False, 'text':j['text'], 'show_more_vals':False, 'hid':i['tid'], 'lid':i['id']})
                if _temp_href_m:
                    _temp_header_c.append({'text':f'{i["label"]}(url)({_h_count})' if _h_count else f'{i["label"]}(url)', 'is_link':True})
                    _temp_row_c.append({'is_link':False, 'text':'', 'show_more_vals':False, 'is_dummy':True, 'hid':i['tid'], 'lid':i['id']})
                    _temp_href_m -= 1
    
                _temp_text_m -= 1
                _h_count += 1

            while _temp_text_m:
                _temp_header_c.append({'text':f'{i["label"]}({_h_count})' if _h_count else i["label"], 'is_link':False, 'is_first':not _h_count, 'has_groupby':(groupby is not None and __eq_gb(i, groupby)), 'tableid':i['tableid'], 'id':i['id'], 'tid':i['tid']})
                _temp_row_c.append({'is_link':False, 'text':'', 'show_more_vals':False, 'is_dummy':True, 'hid':i['tid'], 'lid':i['id']})
                if _temp_href_m:
                    _temp_header_c.append({'text': f'{i["label"]}(url)({_h_count})' if _h_count else f'{i["label"]}(url)', 'is_link':True})
                    _temp_row_c.append({'is_link':False, 'text':'', 'show_more_vals':False, 'is_dummy':True, 'hid':i['tid'], 'lid':i['id']})
                    _temp_href_m -= 1
            
                _temp_text_m -= 1
                _h_count += 1
        
            _structured_col_payload['vals_by_row'].append(_temp_row_c)
            _structured_col_payload['labels'] = _temp_header_c

        for j in range(_max_col_length - len(i['col'])):
            _structured_col_payload['vals_by_row'].append([{'is_link':False, 'text':"", 'hid':i['tid'], 'lid':i['id']} for _ in range(_max_text+_max_href or 1)])

        full_obj_results['vals'].append({'data':_structured_col_payload['vals_by_row'], 'ind':'1'})
        full_obj_results['headers'].append({'data':_structured_col_payload['labels'], 'ind':'1'})

    return full_obj_results

    

def flatten_group_block(data:typing.List[dict], groupby = None) -> dict:
    _payload_response, _main_vals = {'headers':[], 'vals':[], 'is_tabular':False}, []
    _max_col_len = max([len(i['col']) for i in data])
    for i in range(_max_col_len):
        for b in data:
            if i >= len(b['col']):
                _payload_response['headers'].append({'text':f'{b["label"]}({i})' if i else b['label'], 'is_link':False, 'tid':b['tid'], 'id':b['id'], 'is_first':not i, 'has_groupby':(groupby is not None and __eq_gb(b, groupby)), 'tableid':b['tableid']})
                _main_vals.append({'text':'', 'is_link':False, 'hid':b['tid'], 'lid':b['id']})
            else:
                _h_count = 0
                for y in range(len(b['col'][i])):
                    _payload_response['headers'].append({'text':f'{b["label"]}({y}){"("+str(i)+")" if i else ""}' if y else f'{b["label"]}{"("+str(i)+")" if i else ""}', 'tid':b['tid'], 'id':b['id'], 'is_link':False, 'is_first':not i and not _h_count, 'has_groupby':(groupby is not None and not y and __eq_gb(b, groupby)), 'tableid':b['tableid']})
                    _main_vals.append({'text':b['col'][i][y]['text'], 'is_link':False, 'hid':b['tid'], 'lid':b['id']})
                    
                    if b['col'][i][y]['is_a']:
                        _payload_response['headers'].append({'text':f'{b["label"]}(url)({y}){"("+str(i)+")" if i else ""}' if y else f'{b["label"]}(url){"("+str(i)+")" if i else ""}', 'is_link':True, 'is_first':False, 'has_groupby':False})
                        _main_vals.append({'is_link':True, 'text':b['col'][i][y]['href'], 'hid':b['tid'], 'lid':b['id']})
                    
                    _h_count += 1

    _payload_response['headers'] = [{'data':_payload_response['headers'], 'ind':1}]
    _payload_response['vals'].append({'data':_main_vals, 'ind':1})
    return _payload_response

def apply_group_block(data:typing.List[dict], is_offical_group:bool, groupby=None, flatten:bool=False) -> typing.Iterator:
    if flatten:
        yield flatten_group_block(data, groupby = groupby)

    elif groupby is None:
        yield tabular_structure_display(data, groupby = groupby)

    else:
        _t_ind = next((i for i in range(len(data)) if __eq_gb(data[i], groupby)))
        if len(set([len(i['col']) for i in data])) > 1:
            _left_flat = None if not _t_ind else flatten_group_block(data[:_t_ind], groupby=groupby)
            _formed_tabular_center = tabular_structure_display([data[_t_ind]], groupby=groupby)
            _right_flat = flatten_group_block(data[_t_ind+1:], groupby=groupby) if _t_ind + 1 < len(data) else None
            for x in range(len(_formed_tabular_center['vals'][0]['data'])-1):
                if _left_flat is not None:
                    _left_flat['vals'].append(_left_flat['vals'][0]) #may need a deep copy of _left_flat['vals'][0]
                
                if _right_flat is not None:
                    _right_flat['vals'].append(_right_flat['vals'][0])
            
            if _left_flat is not None:
                yield _left_flat

            yield _formed_tabular_center
            if _right_flat is not None:
                yield _right_flat
    
        else:
            _max_col_l = max([len(x) for x in data[_t_ind]['col']])
            _new_data = [{**x, 'col':[]} for x in data]
            for i in range(len(data[0]['col'])):
                _slice_cols = [x['col'][i] for x in data]
                if _max_col_l == 1:
                    for j in range(len(_slice_cols)):
                        _new_data[j]['col'].append(_slice_cols[j])
                else:
                    _max_grouped_height = max([len(x) for x in _slice_cols])
                    for j in range(len(_slice_cols)):
                        for c in _slice_cols[j]:
                            _new_data[j]['col'].append([c])

                        for k in range(_max_grouped_height - len(_slice_cols[j])):
                            
                            _new_data[j]['col'].append([_slice_cols[j][0] if data[j]['is_group_key'] or len(_slice_cols[j]) == 1 else {'is_a':False, 'is_empty':True, 'text':''}])
                    
            yield tabular_structure_display(_new_data, groupby=groupby)


def display_table_data_raw(tableid:str, data:list, table_grouping_ids:dict) -> typing.Any:
    data = list(filter(lambda x:x['col'], data))
    _grouped_data, _flattened_results = [i for i in run_generic_flattening(data) if i['data']], None
    #print('_grouped_data', _grouped_data)
    if table_grouping_ids[tableid] is None:
        '''
        if any(len(x['col']) == 1 for x in data) or len(set([int(x['tableid']) for x in data])) > 1:
            _flattened_results = [j for k in _grouped_data for j in apply_group_block(k['data'], k['is_group'], groupby=None, flatten=True)]
        else:
            #_flattened_results = _grouped_data.map(function(x){return [...apply_group_block(x.data, x.is_group)]}).flat(1)
            _flattened_results = [j for k in _grouped_data for j in apply_group_block(k['data'], k['is_group'])]
        '''
        if sum(len(x['col']) == 1 for x in data) == 1 and any(len(x['col']) > 1 for x in data):
            _flattened_results = [j for k in _grouped_data for j in apply_group_block(k['data'], k['is_group'])]

        elif any(len(x['col']) == 1 for x in data):
            _flattened_results = [j for k in _grouped_data for j in apply_group_block(k['data'], k['is_group'], groupby=None, flatten=True)]
        
        else:
            _flattened_results = [j for k in _grouped_data for j in apply_group_block(k['data'], k['is_group'])]


    else:
        _group_block_ind = [i for i in range(len(_grouped_data)) if any(__eq_gb(x, table_grouping_ids[tableid]) for x in _grouped_data[i]['data'])][0]
        _left_flattened_side = [j for k in _grouped_data[:_group_block_ind] for j in apply_group_block(k['data'], k['is_group'], groupby=None, flatten=True)] if _group_block_ind else []
        _applied_flattening = [*apply_group_block(_grouped_data[_group_block_ind]['data'], _grouped_data[_group_block_ind]['is_group'], groupby=table_grouping_ids[tableid])]
        _right_flattened_side = [j for k in _grouped_data[_group_block_ind+1:] for j in apply_group_block(k['data'], k['is_group'], groupby=None, flatten=True)] if _group_block_ind + 1 < len(_grouped_data) else []
        for x in range(len(_applied_flattening[0]['vals'][0]['data']) - 1 if _applied_flattening[0]['is_tabular'] else len(_applied_flattening[0]['vals']) - 1):
            for l in _left_flattened_side:
                l['vals'].append(copy.deepcopy(l['vals'][0]))
            for r in _right_flattened_side:
                r['vals'].append(copy.deepcopy(r['vals'][0]))
        
        
        _flattened_results = [*_left_flattened_side, *_applied_flattening, *_right_flattened_side]
    
    #return {'raw':_flattened_results}
    return _flattened_results

def combine_data(*dicts:typing.List[dict]) -> dict:
    mapping = collections.defaultdict(list)
    for d in dicts:
        for a, b in d.items():
            mapping[a].append(b)
    
    return {str(a):combine_data(*b) if b and isinstance(b[0], dict) else [j for k in b for j in k] for a, b in mapping.items()}



def generate_dummy_t_data(params:typing.List[list]) -> dict:
    return dict(params[0]) if len(params) == 1 else {str(i):generate_dummy_t_data(params[1:]) for i in params[0]}

def run_compression(header_vals:typing.List[dict], id_keys:typing.List[str]=['tid', 'id']) -> list:
    running_set, current_non_a = {}, None
    for i in header_vals:
        if not i['is_link']:
            current_non_a = tuple(int(i[j]) for j in id_keys)
        _k = (*current_non_a, int(i['is_link']))
        #need basic dict for order preservation (Py >= 3.7)
        if _k in running_set:
            running_set[_k].append(i)
        else:
            running_set[_k] = [i]

    return running_set


def max_template_h(vals:typing.List[dict]) -> dict:
    return {i:max([len(k.get(i, [])) for k in vals]) for i in list(max(vals, key=len))}

def get_nontabular_flattened(headers:dict, data:typing.Tuple[dict]) -> typing.List[list]:
    results = []
    for i in data:
        _start = [i.get(a, [])+([{'text': '', 'is_link': False}]*(b - len(i.get(a, [])))) for a, b in headers.items()]
        results.append([j for k in zip(*_start) for j in k])

    return results

class RunningChild:
    def __init__(self, _c:int=0) -> None:
        self._c = _c
        
    @property
    def count(self) -> int:
        return self._c

    def __next__(self) -> int:
        self._c += 1
        return self._c - 1

def get_nontabular_flattened_headers(template, headers:dict) -> typing.List[list]:
    _start = [[{'text':f'{template[str(a)][str(b)]["label"]}'+('' if not c else '(url)')+('' if not k else f'({k})'), 'is_link':bool(c)} for k in range(d)] for (a, b, c), d in headers.items()]
    return [i for j in zip(*_start) for i in j]

def non_tabular_collection_merge(template:dict, group:typing.Tuple[dict]) -> dict:
    headers_compressed = [max_template_h(k) for k in itertools.zip_longest(*[[run_compression(i['data']) for i in b.get('headers', [])] for b in group], fillvalue={})]
    data_compressed = [k for k in itertools.zip_longest(*[[run_compression(i['data'], id_keys=['hid', 'lid']) for i in b.get('vals', [])] for b in group], fillvalue={})]
    full_result = [get_nontabular_flattened(a, b) for a, b in zip(headers_compressed, data_compressed)]
    _headers = [get_nontabular_flattened_headers(template, i) for i in headers_compressed]
    return {'headers':[{'data':i, 'ind':1} for i in _headers], 'vals':[{'data':i, 'ind':1} for i in full_result],'is_tabular':True}

def run_tabular_compression(header_compressed:dict, data:typing.List[list], id_keys=['hid', 'lid']) -> list:
    new_d_row = []
    for row in data:
        _r = run_compression(row, id_keys= id_keys)
        _start = [_r.get(a, [])+([{'text': '', 'is_link': False}]*(b - len(_r.get(a, [])))) for a, b in header_compressed.items()]
        new_d_row.append([j for k in zip(*_start) for j in k])

    return new_d_row

def tabular_collection_merge(template:dict, group:typing.Tuple[dict]) -> dict:
    headers_compressed = [max_template_h(k) for k in itertools.zip_longest(*[[run_compression(i['data']) for i in b.get('headers', [])] for b in group], fillvalue={})]
    _group_compression = [[j for k in i for j in k] for i in zip(*[[run_tabular_compression(j, k.get('data', []), id_keys=['hid', 'lid']) for j, k in itertools.zip_longest(headers_compressed, b.get('vals', []), fillvalue={})] for b in group])]
    _headers = [get_nontabular_flattened_headers(template, i) for i in headers_compressed]
    return {'headers':[{'data':i, 'ind':1} for i in _headers], 'vals':[{'data':i, 'ind':1} for i in _group_compression if i],'is_tabular':True}

def flattened_group_tabify(vals:typing.List[dict]) -> typing.List[list]:
    full_tabs, r_key, r_vals = collections.defaultdict(list), None, []
    for i in vals:
        for b in i['data']:
            if not b['is_link']:
                k1, k2 = tuple(b.get(j) for j in ['tid', 'id']), tuple(b.get(j) for j in ['hid', 'lid'])
                r_temp = k1 if any(k1) else k2
                if r_key is None:
                    r_key = r_temp
                if r_key != r_temp:
                    full_tabs[r_key].append(r_vals)
                    r_key = r_temp
                    r_vals = []

            r_vals.append(b)
    
    full_tabs[r_key].append(r_vals)
    return full_tabs

def to_tabular_header(template:dict, x:str, y:str, r_vals:typing.List[dict]) -> typing.List[dict]:
    r = RunningChild()
    return [{**j, 'text':f'{template[str(x)][str(y)]["label"]}{"(url)" if j["is_link"] else ""}{("" if not r.count-1 else "("+str(r.count-1)+")") if j["is_link"] else (lambda x:"" if not x else "("+str(x)+")")(next(r))}'} for j in r_vals]

def to_tabular(template:dict, block:dict) -> dict:
    _headers, _vals = flattened_group_tabify(block['headers']), flattened_group_tabify(block['vals'])
    full_headers = [{'data':to_tabular_header(template, j, k, max(b, key=len)), 'ind':1} for (j, k), b in _headers.items()]
    full_vals = [{'data':(lambda x:[t+([{'text':'', 'is_link':False, 'hid':j, 'lid':k}]*(x - len(t))) for t in b])(max(map(len, b))), 'ind':1} for (j, k), b in _vals.items()]
    return {'headers':full_headers, 'vals':full_vals, 'is_tabular':True}


def merge_table_group(template:dict, group:typing.List[dict]) -> dict:
    _options, tab_type = list(filter(None, group)), {1:[], 0:[]}
    for i, a in enumerate(_options):
        tab_type[a['is_tabular']].append((i, a))
        
    if not tab_type[0] or tab_type[1]:
        return tabular_collection_merge(template, [b for _, b in (tab_type[1] if not tab_type[0] else sorted([(i, to_tabular(template, j)) for i, j in tab_type[0]]+tab_type[1], key=lambda x:x[0]))])

    return non_tabular_collection_merge(template, _options)

def merge_collection(template:dict, collections:typing.List[list]) -> typing.List[dict]:
    if len(collections) == 1:
        return collections[0]
    
    return [merge_table_group(template, i) for i in itertools.zip_longest(*collections, fillvalue={})]
