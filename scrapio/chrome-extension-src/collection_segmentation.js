function unique_paths_collections(all_nodes){
    console.log('all nodes in unique_paths_collections')
    console.log(all_nodes)
    var inner_result = {'match':false, 'rows':[]};
    if (all_nodes.length <= 1){
        return {'result':inner_result, 'nodes':all_nodes};
    }
    var _len_groups = {};
    for (var i = 0; i < all_nodes.length; i++){
        var _l = all_nodes[i].ind_path.length;
        if (_l in _len_groups){
            _len_groups[_l].push({ind:i, n:all_nodes[i]});
        }
        else{
            _len_groups[_l] = [{ind:i, n:all_nodes[i]}]
        }
    }
    console.log('len groups')
    console.log(_len_groups)
    var g_1 = Object.keys(_len_groups).filter(function(x){return _len_groups[x].length > 1});
    var e_1 = Object.keys(_len_groups).filter(function(x){return _len_groups[x].length === 1});
    if (!g_1.length){
        g_1 = e_1;
        e_1 = []
    }
    for (var e of e_1){
        var _r_diff = null;
        var _r_key = null;
        for (var g of g_1){
            if (_r_diff === null || Math.abs(e - g) < _r_diff){
                _r_diff = Math.abs(e - g);
                _r_key = g
            }
        }
        for (var j of _len_groups[e]){
            _len_groups[_r_key].push(j)
        }
    }
    var _groups_inds = g_1.map(function(x){return get_subnodes_unique_ind(_len_groups[x])})
    console.log('new groups_inds test')
    console.log(_groups_inds)
    if (_groups_inds.every(function(x){return x.result})){
        var _full_mapping = {};
        for (var g of _groups_inds){
            for (var s of g.nodes){
                _full_mapping[s.ind] = s.n.ind_path[g.ind];
            }
        }
        inner_result['match'] = true;
        console.log('full rows after new groupby')

        console.log((new Set(Object.keys(_full_mapping).map(function(x){return _full_mapping[x].id})).size))
        for (var i = 0; i < all_nodes.length; i++){
            inner_result['rows'].push(_full_mapping[i]);
        }
    }
    return {'result':inner_result, 'nodes':all_nodes};
}
function group_results_collections(cols){
    console.log('group_results_collections test cols')
    console.log(cols)
    var _chosen = [];
    var _col_key = 0;
    for (var col of cols){
        if (col.unique.result.match){
            _chosen = col.unique.result.rows;
            break;
        }
        _col_key++;
    }
    //console.log('beforehand cols');
    //console.log(cols);
    console.log('chosen in group_results_collection')
    console.log(_chosen)
    if (_chosen.length === 0){
        //something that goes here to format results
        //alert('got in here');
        var _new_payload = {'result':false, 'data':cols.map(function(obj){
            return {...obj, 'label':obj.label, 'col':obj.unique.nodes.map(function(node){return [node]}), 'id':obj.id, 'has_group':false};
        })}
        //console.log('new payload in here');
        //console.log(_new_payload);
        return _new_payload;
    }
    var group_mapper = Object.fromEntries(new Map(_chosen.map(function(obj){return [obj.id, Object.fromEntries(new Map(cols.map(function (l){return [l.lid, []]})))]})))
    console.log('group mapper in group_results_collections')
    console.log(group_mapper)
    var unmatched_mapper = Object.fromEntries(new Map(cols.map(function(l){return [l.lid, []]})));
    
    for (var col of cols){
        for (node of col.unique.nodes){
            var _matches = node.ind_path.filter(function(v){return v.id in group_mapper});
            if (_matches.length > 0){
                group_mapper[_matches[_matches.length-1].id][parseInt(col.lid)].push(node);
            }
            else{
                unmatched_mapper[parseInt(col.lid)].push(node);
            }
        }
    }
    console.log('after grouping op');
    console.log(group_mapper);
    console.log(unmatched_mapper);
    /*
    var _final_result = Object.keys(group_mapper).map(function (id){
        return Object.keys(_selectors).map(function(inner_id){return group_mapper[id][inner_id]});
    });
    */
    var _chosen_id_set = _chosen.map(function(x){return x.id}).join(',');
    var _col_key_count_check = 0;
    var _final_result = cols.map(function(obj){
        var _first_lookup = Object.keys(group_mapper).map(function(uni_id){return group_mapper[uni_id][obj.lid]});
        _col_key_count_check++;
        return {...obj, 'is_group_key':_col_key === _col_key_count_check-1, 'label':obj.label, 'col':[...(_first_lookup.filter(function(n_obj){return n_obj.length > 0}).length > 0 ? _first_lookup : []), ...unmatched_mapper[obj.lid].map(function(v){return [v]})], 'id':obj.lid, 'has_group':true, 'group_id_row':_chosen_id_set};
    });
    //console.log('final_result object here');
    //console.log(_final_result);
    return {'result':true, 'data':_final_result};
}
function* get_all_nodes(content){
    for (var i of content){
        for (var c of i.nodes){
            yield c;
        }
    }
}
function get_common_path(node_paths){
    var _full_common_path = [];
    while (node_paths.filter(function (x){return x.length}).length === node_paths.length){
        var _c_ids = new Set(node_paths.map(function(x){return x.shift().id}));
        if (_c_ids.size > 1){
            return _full_common_path;
        }
        _full_common_path.push([..._c_ids][0])

    }
    return _full_common_path;
}
function _get_diff_level(paths){
    var _m_l = null;
    for (var i of paths){
        if (_m_l === null || i.length < _m_l){
            _m_l = i.length;
        }
    }
    var _last_seen_dev = null;
    for (var i = 0; i < _m_l; i++){
        var _c_ids = new Set(paths.map(function(x){return x[i]}));
        if (_c_ids.size > 1){
            //return i;
            _last_seen_dev = i;
        }
    }
    if (_last_seen_dev != null){
        return _last_seen_dev;
    }
    return _m_l-1;
}


function* get_collections_groups(table, range){
    //console.log('range in get collections')
    //console.log(range);
    //console.log('table in get_cols recursive')
    //console.log(table);
    var _temp_grouped = {};
    for (var i of range){
        if (table[0][parseInt(i)].id in _temp_grouped){
            _temp_grouped[table[0][parseInt(i)].id].push(table[0][parseInt(i)]);
        }
        else{
            _temp_grouped[table[0][parseInt(i)].id] = [table[0][parseInt(i)]];
        }
    }
    var _singletons = Object.keys(_temp_grouped).filter(function(k){return _temp_grouped[k].length === 1});
    var _main_groups = Object.keys(_temp_grouped).filter(function(k){return _temp_grouped[k].length > 1});
    if (_singletons.length > 0){
        if (table.slice(1).length > 0){
            if (_main_groups.length > 0){
                for (var i of _singletons){
                    yield _temp_grouped[i];
                }
                
            }
            else{
                var _grouped_singletons = [];
                for (var i of _singletons){
                    if (!_temp_grouped[i][0].id.match(/^DATAFLOW\-ID\d+/g)){
                        yield _temp_grouped[i];
                    }
                    else{
                        _grouped_singletons.push(_temp_grouped[i][0]);
                    }
                }
                if (_grouped_singletons.length > 0){
                    yield _grouped_singletons;
                }

            }
        }
        else{
            var _grouped_singletons = (function(t_g){return t_g.length > 0 ? t_g.reduce(function(x, y){return [...x, ...y]}) : []})(_main_groups.map(function(x){return _temp_grouped[x]}));
            for (var i of _singletons){
                if (!_temp_grouped[i][0].id.match(/DATAFLOW\-ID\d+/g)){
                    yield _temp_grouped[i];
                }
                else{
                    _grouped_singletons.push(_temp_grouped[i][0]);
                }
            }
            if (_grouped_singletons.length > 0){
                yield _grouped_singletons;
            }

        }
        
    }
    for (var i of _main_groups){
        if (table.slice(1).length > 0){
            yield* get_collections_groups(table.slice(1), _temp_grouped[i].map(function(x){return parseInt(x.path)}));
        }
        else if (_singletons.length === 0){
            yield _temp_grouped[i]
        }
    }
}
function* get_new_collections_groups(groups, range){
    console.log('get_new_collections_groups')
    console.log(groups)
    var _starting_row = groups[groups.length-1]
    var _row_chunks = [];
    var _running_chunk = [];
    var _last_id = null;
    for (var i of range){
        if (_last_id === null){
            _last_id = _starting_row[i].id;
            _running_chunk.push(_starting_row[i])
        }
        else if (_starting_row[i].id === "DATAFLOW-DUMMY-ID"){
            _row_chunks.push(_running_chunk)
            _running_chunk = [_starting_row[i]];
            _last_id = _starting_row[i].id;
        }
        else if (_starting_row[i].id === _last_id){
            _running_chunk.push(_starting_row[i])
        }
        else{
            _row_chunks.push(_running_chunk)
            _running_chunk = [_starting_row[i]];
            _last_id = _starting_row[i].id;
        }
    }
    _row_chunks.push(_running_chunk);
    console.log('row chunks test in here')
    console.log(_row_chunks)
    var _apply_rec_chunks = [];
    var _current_rec_chunk = [];
    for (var i of _row_chunks){
        if (i.length > 1){
            if (_current_rec_chunk.length > 0){
                _apply_rec_chunks.push(_current_rec_chunk.flat(1))
                _current_rec_chunk = [];
            }
            yield i
        }
        else{
            _current_rec_chunk.push(i);
        }
    }
    if (_current_rec_chunk.length > 0){
        _apply_rec_chunks.push(_current_rec_chunk.flat(1))
        _current_rec_chunk = [];
    }
    for (var i of _apply_rec_chunks){
        if (i.length > 1){
            yield* get_new_collections_groups(groups.slice(0, groups.length-1), i.map(function(x){return x.path}));
        }
        else{
            yield i
        }
    }
                                                                     
}
function get_diff_level(paths){
    var _m_l = null;
    for (var i of paths){
        if (_m_l === null || i.length < _m_l){
            _m_l = i.length;
        }
    }
    
    var _group_history = [];
    for (var i = 0; i < _m_l; i++){
        var _flattened_row = [];
        for (var j in paths){
            var j = parseInt(j);
            _flattened_row.push({'id':paths[j][i], 'path':j, 'level':i})      
        } 
        _group_history.push(_flattened_row);
    }
    console.log('full tree printout')
    console.log(JSON.parse(JSON.stringify(_group_history)));
    return [...get_new_collections_groups(_group_history, _group_history.length > 0 ? _group_history[_group_history.length-1].map(function(x){return parseInt(x.path)}) : [])]
    

}
function contains_singletons(flattened){
    if (flattened.some(function(x){return ('is_new_entry' in x) && x.is_new_entry})){
        return false;
    }
    var _lens = flattened.map(function(x){return ('col' in x ? x.col : x.cols).length});
    var _ge_lens = Array.from(Array(flattened.length).keys()).filter(function(ind){return ('col' in flattened[ind] ? flattened[ind].col : flattened[ind].cols).length > 1});
    if (_ge_lens.length > 0){
        var _min_loc = Math.min(..._ge_lens);
        var _max_loc = Math.max(..._ge_lens);
        if (_min_loc > 0 && _max_loc < _lens.length-1 && _lens.slice(0, _min_loc).every(function(x){return x < 2}) && _lens.slice(_max_loc+1).every(function(x){return x < 2})){
            return true
        }
    }
    if (_lens.reduce(function(x, y){return x + y}, 0)/_lens.length <= 1.5){
        return true;
    }
    return false;
}
function level_common_paths(paths){
    var _max_height = Math.max(...paths.map(function(x){return x.length}));
    return paths.map(function(x){return [...x, ...Array.from(Array(Math.abs(_max_height - x.length)).keys()).map(function(_){return "DATAFLOW-DUMMY-ID"})]})
}
function compute_collection(levels){
    /*forms collection from single template */
    var _flattened_cols = Object.fromEntries(Object.keys(levels['levels'][1]['labels']).filter(function(lid){return levels['levels'][1]['labels'][lid].content.length > 0}).map(function(lid){return [lid, {'label':levels['levels'][1]['labels'][lid].label, 'lid':lid, 'cols':[...get_all_nodes(levels['levels'][1]['labels'][lid].content)]}]}))
    var _empty_cells = Object.keys(levels['levels'][1]['labels']).filter(function(lid){return levels['levels'][1]['labels'][lid].content.length === 0}).map(function(lid){return {'label':levels['levels'][1]['labels'][lid].label, 'col':[], 'id':lid}});
    var _normalized_cols = Object.keys(_flattened_cols).map(function(x){return {..._flattened_cols[x], 'common_path':get_common_path(_flattened_cols[x].cols.map(function(node){return node.ind_path.slice()}))}})
    console.log('normalized_cols in compute collection')
    console.log(_normalized_cols)
    var _diff_results;
    var _grouped_results;
    if (contains_singletons(_normalized_cols)){
        _grouped_results = [_normalized_cols];
    }
    else{
        _diff_results = get_diff_level(level_common_paths(_normalized_cols.map(function(x){return x.common_path.slice()})));
        _grouped_results = _diff_results.map(function(x){return x.map(function(g_ob){return _normalized_cols[parseInt(g_ob.path)]})});
    }
    console.log('get_collections_groups printout results in here')
    console.log(_diff_results);
    console.log('all grouped results');
    console.log(_grouped_results);
    var _all_grouped_collections = Object.keys(_grouped_results).map(function(_key){
        var _full_array = _grouped_results[_key].map(function(r_obj){return {...r_obj, 'id':r_obj.lid, 'unique':unique_paths_collections(r_obj.cols)}});
        console.log('full array check')
        console.log(_full_array)
        return group_results_collections(_full_array);

    });
    /*
    for (var e of _empty_cells){
        _all_grouped_collections.push({'data':[e]});
    }
    */
    console.log('all grouped results collections')
    console.log(_all_grouped_collections)
    //var _full_array = Object.keys(label_block).map(function(id){return {'id':id, 'unique':unique_paths(label_block[id].content)}});
    //var _grouped_data = group_results(_full_array, label_block);
    
    return _all_grouped_collections;

}
function compute_collections(template){
    /*groups each subtemplate, with levels, into main view*/
    var _starting_collections = Object.keys(template).filter(function(x){return Object.keys(template[x]['levels'][1]['labels']).length > 0}).map(function(tid){return compute_collection(template[tid]).map(function(col){return {...col, 'data':col.data.map(function(col_d){return {...col_d, 'tid':tid}})}})})
    console.log('all starting collections')
    console.log(_starting_collections);
    return _starting_collections;
}
function* flatten_collections(all_collections){
    for (var i of all_collections){
        for (var b of i){
            yield b.data;
        }
    }
}
function* flatten_new_collections(all_collections){
    for (var i of all_collections){
        yield i.data;
    }
}
function max_cutoff_ind(seg, ind){
    var _seg_count = 0;
    var _last_i = null;
    for (var i = 0; i < seg.length; i++){
        if (!('is_dummy' in seg[i]) || !seg[i].is_dummy){
            if (!seg[i].is_link){
                _seg_count++;
                if (_seg_count > ind){
                    return _last_i;
                }
            }
            _last_i = i;
        }
    }
    if (_seg_count === ind){
        return _last_i;
    }
    return -1;
}
function block_limits_left(seg){
    var _seg_count = 0;
    for (var i of seg){
        if (!('is_dummy' in i) || !i.is_dummy){
            if (!i.is_link){
                _seg_count++;
            }
        }
    }
    return _seg_count;
}
function compute_option1_limit(c){
    return c > 0 ? 1 : 0;
}

function get_pairwise_row(header, row){
    var _payload = {};
    for (var i in row){
        _payload[header[parseInt(i)]] = row[parseInt(i)];
    }
    return _payload;
}
var _cp_csv;
function add_t(row){
    var _r = []
    for (var i = 0; i < row.length; i++){
        var _nv = row[i];
        if (i < row.length-1){
            _nv = `${_nv}\t`
        }
        _r.push(_nv);
    }
    return _r;
}
function load_download_output(header, rows){
    generate_scrape_name();
    _json_view = JSON.stringify(rows.map(function(x){return get_pairwise_row(header, x)}), null, 4)
    arr_form = [header, ...rows];
    _cp_csv = [header, ...rows].map(function(x){return x.join('\t')}).join('\n');
    _csv_view = [header, ...rows].map(function(x){return x.join(',')}).join('\n');
    var _file = new Blob([_csv_view], {type: 'text/csv'});
    var a = document.getElementById("dataflow-download-data");
    a.href = URL.createObjectURL(_file);
    a.download = `${running_flow_name}.csv`;
}



var preview_collections_result;
function form_results_from_collections(template, collections){
    console.log('in form_results_from_collections')
    console.log(collections)
    console.log(template);
    /*
    var _all_grouped_collections = Object.keys(_grouped_results).map(function(_key){
        var _full_array = _grouped_results[_key].map(function(r_obj){return {...r_obj, 'id':r_obj.lid, 'unique':unique_paths_collections(r_obj.cols)}});
        console.log('full array check')
        console.log(_full_array)
        return group_results_collections(_full_array);
    });
    {"tables":[{'clct_id':"1", 'name':'Table 1'}, {'clct_id':"2", 'name':'Table 2'},{'clct_id':"3", 'name':'Table 3'}],"table_records":{"1":[{"id":"1","tid":"1"},{"id":"2","tid":"1"},{"id":"3","tid":"1"},{"id":"4","tid":"1"}],"2":[{"id":"8","tid":"1"}],"3":[{"id":"5","tid":"1"},{"id":"6","tid":"1"},{"id":"7","tid":"1"}]}};
    */
    var _pre_return_stuff = collections.tables.map(function(t){
        var _full_array = collections.table_records[t.clct_id].map(function(x){
            var _temp_payload = {...x, 'label':template[x.tid]['levels']['1']['labels'][x.id].label, 'lid':parseInt(x.id), 'cols':[...get_all_nodes(template[x.tid]['levels']['1']['labels'][x.id].content)].map(function(k){return {...k, 'tid':x.tid}})};
            _temp_payload['unique'] = unique_paths_collections(_temp_payload.cols)
            return _temp_payload;
        });
        return group_results_collections(_full_array);
    });
    console.log('form_results_from_collections pre_return')
    console.log(_pre_return_stuff)
    return _pre_return_stuff;
}
function* get_all_level_content(levels, lid){
    for (var level of Object.keys(levels)){
        if (lid in levels[level]['labels']){
            for (var c of levels[level]['labels'][lid].content){
                yield c
            }
        }
    }
}
function form_table_vals(tableid, template, vals){
    console.log('template in form_table_vals')
    console.log(JSON.parse(JSON.stringify(template)));
    console.log('vals in form_table_vals')
    console.log(vals)
    var _grouped_table_forms = {};
    for (var i of vals){
        if (i.tableid in _grouped_table_forms){
            _grouped_table_forms[i.tableid].push(i);
        }
        else{
            _grouped_table_forms[i.tableid] = [i]
        }
    }
    var _final_results = [];
    for (var k of Object.keys(_grouped_table_forms)){
        var _full_array = _grouped_table_forms[k].map(function(x){
            var _temp_payload = {...x, 'label':template[x.tid]['levels']['1']['labels'][x.id].label, 'lid':parseInt(x.id), 'cols':[...get_all_nodes([...get_all_level_content(template[x.tid]['levels'], x.id)])].map(function(k){return {...k, 'tid':x.tid}})};
            console.log('temp payload in form_table_vals')
            console.log(_temp_payload)
            _temp_payload['unique'] = unique_paths_collections(_temp_payload.cols)
            return _temp_payload;
        });
        _final_results = [..._final_results, ...group_results_collections(_full_array).data];

    }
    return _final_results;
}
function* get_singleton_runs(run){
    _singleton_locs = Array.from(Array(run.length).keys()).filter(function(x){return run[x].is_singleton});
    if (_singleton_locs.length === 0){
        for (var i of run){
            yield i
        } 
    }
    else{
        _min_loc = Math.min(..._singleton_locs)
        _max_loc = Math.max(..._singleton_locs);
        if (_min_loc > 0){
            for (var i of run.slice(0, _min_loc)){
                yield i
            }
        }
        yield {data:run.slice(_min_loc, _max_loc+1).map(function(x){return x.data}).flat(1), is_singleton:true}
        if (_max_loc+1 < run.length){
            for (var i of run.slice(_max_loc+1)){
                yield i;
            }
        }
    }
}
function* get_table_joins(collections, clct_id){
    for (var i of collections['tables']){
        if (i.parent != null && parseInt(clct_id) === parseInt(i.parent)){
            for (var k of collections['table_records'][i.clct_id]){
                yield {...k, 'tableid':i.clct_id};

            }
            yield* get_table_joins(collections, i.clct_id);
        }
    }
}
function form_display_tables(collections, template){
    console.log('collections form_display_tables chekcing test')
    console.log(collections);
    console.log('template form_display_tables chekcing test')
    console.log(JSON.parse(JSON.stringify(template)))
    var _joined_tables = Object.fromEntries(collections['tables'].filter(function(x){return x.parent === null}).map(function(x){return [x.clct_id, [...collections['table_records'][x.clct_id].map(function(k){return {...k, 'tableid':x.clct_id}}), ...get_table_joins(collections, x.clct_id)]]}))
    console.log('joined tables in form_display_tables')
    console.log(_joined_tables)
    return _joined_tables
}
function tabular_structure_display(data, groupby=null){
    console.log('data in tabular_structure_display')
    console.log(data)
    var _max_col_length = Math.max(...data.map(function(x){return x.col.length}))
    var full_obj_results = {headers:[], vals:[], is_tabular:true};
    for (var i of data){
        var _href_vals = i.col.filter(function(x){return x.filter(function(y){return y.is_a}).length > 0}).map(function(x){return x.map(function(y){return y.is_a ? 1 :0}).reduce(function(x, y){return x + y})});
        var _max_href = _href_vals.length > 0 ? Math.max(..._href_vals) : 0
        var _max_text = Math.max(...i.col.map(function(x){return x.length}));
        var _structured_col_payload = {'labels':[], 'id':i.id, 'tid':i.tid, 'vals_by_row':[], 'ind':1};
        for (var c of i.col){
            var _temp_href_m = _max_href;
            var _temp_text_m = _max_text;
            var _temp_header_c = [];
            var _temp_row_c = [];
            var _h_count = 0;
            for (var j of c.filter(function(x){return x.is_a})){
                _temp_header_c.push({'text':_h_count === 0 ? i.label : `${i.label}(${_h_count})`, 'is_link':false, 'is_first':_h_count === 0, 'has_groupby':(groupby != null && __eq_gb(i, groupby)), tableid:i.tableid, 'id':i.id, 'tid':i.tid});
                _temp_header_c.push({'text':_h_count === 0 ? `${i.label}(url)` : `${i.label}(url)(${_h_count})`, 'is_link':true, 'is_first':false})
                _temp_row_c.push({'is_link':false, 'text':!j.is_drag ? j.text : j.drag_text, 'show_more_vals':false});
                _temp_row_c.push({'is_link':true, 'text':j.href, 'show_more_vals':false});
                _temp_href_m--;
                _temp_text_m--;
                _h_count++;

            }
            for (var j of c.filter(function(x){return !x.is_a})){
                _temp_header_c.push({'text':_h_count === 0 ? i.label : `${i.label}(${_h_count})`, 'is_link':false, 'is_first':_h_count === 0, 'has_groupby':(groupby != null && __eq_gb(i, groupby)), tableid:i.tableid, 'id':i.id, 'tid':i.tid});
                _temp_row_c.push({'is_link':false, 'text':!j.is_drag ? j.text : j.drag_text, 'show_more_vals':false});
                if (_temp_href_m > 0){
                    _temp_header_c.push({'text':_h_count === 0 ? `${i.label}(url)` : `${i.label}(url)(${_h_count})`, 'is_link':true})
                    _temp_row_c.push({'is_link':false, 'text':'', 'show_more_vals':false, 'is_dummy':true});
                    _temp_href_m--;
                }
                _temp_text_m--;
                _h_count++;
            }
            while (_temp_text_m > 0){
                _temp_header_c.push({'text':_h_count === 0 ? i.label : `${i.label}(${_h_count})`, 'is_link':false, 'is_first':_h_count === 0, 'has_groupby':(groupby != null && __eq_gb(i, groupby)), tableid:i.tableid, 'id':i.id, 'tid':i.tid});
                _temp_row_c.push({'is_link':false, 'text':'', 'show_more_vals':false, 'is_dummy':true});
                if (_temp_href_m > 0){
                    _temp_header_c.push({'text':_h_count === 0 ? `${i.label}(url)` : `${i.label}(url)(${_h_count})`, 'is_link':true})
                    _temp_row_c.push({'is_link':false, 'text':'', 'show_more_vals':false, 'is_dummy':true});
                    _temp_href_m--;
                }
                _temp_text_m--;
                _h_count++;
            }
            //{'text':val === 0 ? i.label : `${i.label}(${val})`, 'is_link':false}
            _structured_col_payload['vals_by_row'].push(_temp_row_c);
            _structured_col_payload['labels'] = _temp_header_c

        }
        console.log('_max_col_length - i.col.length: '+(_max_col_length - i.col.length).toString());
        for (var j = 0; j < _max_col_length - i.col.length; j++){
            _structured_col_payload['vals_by_row'].push(Array.from(Array(_max_text+_max_href > 0 ? _max_text+_max_href : 1).keys()).map(function(x){return {'is_link':false, 'text':""}}))
        }
        full_obj_results.vals.push({data:_structured_col_payload.vals_by_row, ind:1});
        full_obj_results.headers.push({data:_structured_col_payload.labels, ind:1});

    }
    console.log('full obj results')
    console.log(full_obj_results)
    return full_obj_results;
    
}
function __eq_gb(col, gb){
    return parseInt(col.tableid) === parseInt(gb.tableid) && parseInt(col.tid) === parseInt(gb.tid) && parseInt(col.id) === parseInt(gb.id) 
}
function flatten_non_group_block(data, groupby=null){
    var _payload_response = {headers:[], vals:[], is_tabular:false};
    var _main_vals = [];
    for (var i of data){
        var _h_count = 0;
        for (var b of i.col){
            for (var c of b){
                _payload_response.headers.push({'text':_h_count > 0 ? `${i.label}(${_h_count})` : i.label, 'is_link':false, 'tid':i.tid, 'id':i.id, 'is_first':_h_count === 0, 'has_groupby':(groupby != null && __eq_gb({...b, tableid:i.tableid}, groupby)), tableid:i.tableid})
                _main_vals.push({'is_link':false, 'text':c.text})
                if (c.is_a){
                    _payload_response.headers.push({'text':_h_count === 0 ? `${i.label}(url)` : `${i.label}(url)(${_h_count})`, 'is_link':true})
                    _main_vals.push({'is_link':true, 'text':c.href})
                }
                _h_count++;
            }
        }
    }
    _payload_response.headers = [{data:_payload_response.headers, ind:4}]
    _payload_response.vals.push({data:_main_vals, ind:4});
    return _payload_response;
}
function flatten_group_block(data, groupby=null){
    console.log('in flatten_group_block')
    console.log(data);
    var _payload_response = {headers:[], vals:[], is_tabular:false};
    var _main_vals = [];
    var _max_col_len = Math.max(...data.map(function(x){return x.col.length}));
    for (var i = 0; i < _max_col_len; i++){
        for (var b of data){
            if (i >= b.col.length){
                _payload_response.headers.push({'text':i > 0 ? `${b.label}(${i})` : `${b.label}`, 'is_link':false, 'tid':b.tid, 'id':b.id, 'is_first':i === 0, 'has_groupby':(groupby != null && __eq_gb(b, groupby)), tableid:b.tableid});
                _main_vals.push({'text':'', 'is_link':false, 'hid':b.tid, 'lid':b.id});
            }
            else{
                var _h_count = 0;
                for (var y in b.col[i]){
                    _payload_response.headers.push({'text':y > 0 ? `${b.label}(${y})${i > 0 ? `(${i})` : ""}` : `${b.label}${i > 0 ? `(${i})` : ""}`,'tid':b.tid, 'id':b.id, 'is_link':false, 'is_first':i === 0 && _h_count === 0, 'has_groupby':(groupby != null && y === 0 && __eq_gb(b, groupby)), tableid:b.tableid});
                    _main_vals.push({'text':!b.col[i][y].is_drag ? b.col[i][y].text : b.col[i][y].drag_text, 'is_link':false, 'hid':b.tid, 'lid':b.id});
                    if (b.col[i][y].is_a){
                        _payload_response.headers.push({'text':y > 0 ? `${b.label}(url)(${y})${i > 0 ? `(${i})` : ""}` : `${b.label}(url)${i > 0 ? `(${i})` : ""}`, 'is_link':true, 'is_first':false, 'has_groupby':false});
                        _main_vals.push({'is_link':true, 'text':b.col[i][y].href, 'hid':b.tid, 'lid':b.id})
                    }
                    _h_count++;
                }
            }
        }
    }
    _payload_response.headers = [{data:_payload_response.headers, ind:1}]
    _payload_response.vals.push({data:_main_vals, ind:1});
    return _payload_response;


}
function* apply_group_block(data, is_offical_group, groupby=null, flatten=false){
    console.log('in apply_group_block signature')
    console.log(data);
    console.log(groupby)
    console.log(flatten)
    if (flatten){
        console.log('apply_group_block in flatten condition yes')
        yield flatten_group_block(data, groupby = groupby)
    }
    else if (groupby === null){
        yield tabular_structure_display(data, groupby = groupby)
    }
    else{
        console.log('in necessary conditional')
        console.log(data)
        var _t_ind = Array.from(Array(data.length).keys()).filter(function(ind){return __eq_gb(data[ind], groupby)})[0]
        console.log(_t_ind);
        if ((new Set(data.map(function(x){return x.col.length}))).size > 1){
            var _left_flat = _t_ind > 0 ? flatten_group_block(data.slice(0, _t_ind), groupby=groupby) : null;
            var _formed_tabular_center = tabular_structure_display([data[_t_ind]], groupby=groupby)
            var _right_flat = _t_ind + 1 < data.length ? flatten_group_block(data.slice(_t_ind+1), groupby=groupby) : null
            //var _cutoff_y = Math.abs(_formed_tabular_center.vals[0].data - _left_flat.vals.length)
            for (var x = 0; x < _formed_tabular_center.vals[0].data.length - 1; x++){
                if (_left_flat != null){
                    _left_flat.vals.push(JSON.parse(JSON.stringify(_left_flat.vals[0])))
                }
                if (_right_flat != null){
                    _right_flat.vals.push(JSON.parse(JSON.stringify(_right_flat.vals[0])))
                }

            }
            if (_left_flat != null){
                yield _left_flat
            }
            yield _formed_tabular_center;
            if (_right_flat != null){
                yield _right_flat;
            }
        }
        else{
            var _max_col_l = Math.max(...data[_t_ind].col.map(function(x){return x.length}))
            var _new_data = data.map(function(x){return {...x, col:[]}})
            for (var i = 0; i < data[0].col.length; i++){
                var _slice_cols = data.map(function(x){return x.col[i]});
                if (_max_col_l === 1){
                    for (var j in _slice_cols){
                        j = parseInt(j);
                        _new_data[j].col.push(_slice_cols[j]);
                    }
                }
                else{
                    var _max_grouped_height = Math.max(..._slice_cols.map(function(x){return x.length}))
                    for (var j in _slice_cols){
                        j = parseInt(j);
                        for (var c of _slice_cols[j]){
                            _new_data[j].col.push([c]);
                        }
                        for (var k = 0; k < _max_grouped_height - _slice_cols[j].length; k++){
                            _new_data[j].col.push([(data[j].is_group_key || _slice_cols[j].length === 1) ? _slice_cols[j][0] : {is_a:false, is_empty:true, text:''}]);
                        }
                    }
                }
            }
            console.log('new data with grouping tabular applied')
            console.log(_new_data)
            yield tabular_structure_display(_new_data, groupby=groupby)
        }
    }

}
function run_generic_flattening(data){
    console.log('data in run_generic_flattening')
    console.log(data);
    var _grouped_container_data = [];
    var _current_group = [];
    var _current_group_type = null;
    var _current_group_similarity = null;
    for (var i of data){
        if (_current_group_type === null){
            _current_group_type = i.has_group;
            if (i.has_group){
                _current_group_similarity = i.group_id_row;
            }
            _current_group.push(i);
        }
        else if (_current_group_type === i.has_group){
            if (i.has_group){
                if (_current_group_similarity === i.group_id_row){
                    _current_group.push(i);
                }
                else{
                    _grouped_container_data.push({'is_group':true, 'data':_current_group});
                    _current_group = [i];
                    _current_group_similarity = i.group_id_row
                }
            }
            else{
                _current_group.push(i);
            }
        }
        else{
            _grouped_container_data.push({'is_group':_current_group_type, 'data':_current_group});
            _current_group_type = i.has_group;
            if (i.has_group){
                _current_group_similarity = i.group_id_row
            }
            _current_group = [i];

        }

    }
    _grouped_container_data.push({'is_group':_current_group_type, 'data':_current_group});
    console.log('_grouped_container_data up in here')
    console.log(_grouped_container_data);
    return _grouped_container_data;
    
}
var _cached_flattened_results
function get_tabular_values(component, cf_ind){
    //block_limits_left
    //max_cutoff_ind
    var _headers = []
    var _body = {}
    var _temp_body = [];
    var _raw_headers = [];
    var _raw_body = {}
    var _raw_temp_body = [];
    for (var i = 0; i < component.vals.length; i++){
        var _max_obj_l = Math.max(...component.vals[i].data.map(function(x){return max_cutoff_ind(x, parseInt(component.vals[i].ind))})) + 1
        _temp_body.push(component.vals[i].data.map(function(x){
            if (_max_obj_l === -1){
                return [...x.slice(0, x.length-1), {...x[x.length-1], show_more_vals:false}]
            }
            var lim_left = block_limits_left(x.slice(_max_obj_l)) > 0
            return [...x.slice(0, _max_obj_l-1), {...x[_max_obj_l-1], show_more_vals:lim_left, limit:lim_left ? 1 :0, cf_r_id:cf_ind, p_id:i}]
        }));
        _raw_temp_body.push(component.vals[i].data.map(function(x){
            return x 
        }));
        if (_max_obj_l === -1){
            _headers = [..._headers, ...component.headers[i].data]
        }
        else{
            _headers = [..._headers, ...component.headers[i].data.slice(0, _max_obj_l)]
        }
        _raw_headers = [..._raw_headers, ...component.headers[i].data]
    }
    for (var i = 0; i < _temp_body[0].length; i++){
        _body[i] = _temp_body.map(function(x){return x[i]}).flat(1)
    }
    for (var i = 0; i < _raw_temp_body[0].length; i++){
        _raw_body[i] = _raw_temp_body.map(function(x){return x[i]}).flat(1)
    }
    return {headers:_headers, body:_body, raw_headers:_raw_headers, raw_body:_raw_body}
}
function _get_flattend_body(body_row, cf_r_id, p_id=0){
    var _offset_ind = parseInt(body_row.ind)*4;
    /*
    if (_offset_ind >= body_row.data.length){
        return {body:[...body_row.data.slice(0, body_row.data.length-1), {...body_row.data[body_row.data.length-1], 'show_more_vals':false, cf_r_id:cf_r_id, p_id:p_id}], raw_body:[...body_row.data]}
    }
    return {body:[...body_row.data.slice(0, _offset_ind-1), {...body_row.data[_offset_ind-1], 'show_more_vals':true, 'limit':body_row.data.length - _offset_ind >= 4 ? 4 : body_row.data.length - _offset_ind, cf_r_id:cf_r_id, p_id:p_id}], raw_body:[...body_row.data]}
    */
    return {body:[...body_row.data], raw_body:[...body_row.data]}
}
function get_flattened_values(component, cf_ind){
    var _headers = [];
    var _body = {}
    var _raw_headers = [];
    var _raw_body = {}
    for (var i = 0; i < component.headers.length; i++){
        //_headers = [..._headers, ...component.headers[i].data.slice(0, component.headers[i].ind*4)]
        _headers = [..._headers, ...component.headers[i].data]
        _raw_headers = [..._raw_headers, ...component.headers[i].data]
    }
    for (var b = 0; b < component.vals.length; b++){
        var _flattened_body_t =  _get_flattend_body(component.vals[b], cf_ind)
        _body[b] = _flattened_body_t.body
        _raw_body[b] = _flattened_body_t.raw_body
    }
    return {headers:_headers, body:_body, raw_headers:_raw_headers, raw_body:_raw_body}
}
