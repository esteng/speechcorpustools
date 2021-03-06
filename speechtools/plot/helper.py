import numpy as np

max_sig = 1
min_sig = -1

def get_histogram_mesh_data(data, bins=100, color='k', orientation='h'):
    # shamlessly stolen from vispy.visuals.histogram.__init__()
    data = np.asarray(data)
    if data.ndim != 1:
        raise ValueError('Only 1D data currently supported')
    X, Y = (0, 1) if orientation == 'h' else (1, 0)

    # do the histogramming
    data, bin_edges = np.histogram(data, bins)
    # construct our vertices
    rr = np.zeros((3 * len(bin_edges) - 2, 3), np.float32)
    rr[:, X] = np.repeat(bin_edges, 3)[1:-1]
    rr[1::3, Y] = data
    rr[2::3, Y] = data
    bin_edges.astype(np.float32)
    # and now our tris
    tris = np.zeros((2 * len(bin_edges) - 2, 3), np.uint32)
    offsets = 3 * np.arange(len(bin_edges) - 1,
                            dtype=np.uint32)[:, np.newaxis]
    tri_1 = np.array([0, 2, 1])
    tri_2 = np.array([2, 0, 3])
    tris[::2] = tri_1 + offsets
    tris[1::2] = tri_2 + offsets
    return (rr, tris)

def generate_boundaries(annotations, hierarchy, min_time, max_time):
    num_types = len(hierarchy.keys())
    lowest = hierarchy.lowest
    size = max_sig / (num_types)
    line_outputs = {x: [] for x in hierarchy.keys()}
    text_pos = {x: [] for x in hierarchy.keys()}
    text_labels = {x: [] for x in hierarchy.keys()}
    subannotation_keys = []
    for k,v in hierarchy.subannotations.items():
        for s in v:
            line_outputs[k,s] = []
            text_pos[k,s] = []
            text_labels[k,s] = []
            subannotation_keys.append((k,s))
    subannotation_keys.sort()

    try:
        sub_size = max_sig/len(subannotation_keys)
    except ZeroDivisionError:
        sub_size = max_sig
    subannotation_keys = {s: i for i, s in enumerate(subannotation_keys)}
    cur = 0
    main_vert_min = max_sig - size
    main_vert_max = max_sig
    main_vert_mid = (main_vert_max - main_vert_min)/2 + main_vert_min

    vis_mid = (max_time - min_time) /2 + min_time

    for a in annotations:
        #if a.end < min_time:
        #    continue
        #if a.begin > max_time:
        #    continue
        end = a.end
        begin = a.begin
        midpoint = ((end - begin) / 2) + begin
        #if midpoint > max_time or midpoint < min_time:
        #    midpoint = vis_mid
        text = a.label
        if text is None:
            text = ''
        text_labels[a._type].append(text)
        text_pos[a._type].append((midpoint, main_vert_mid))

        line_outputs[a._type].append([begin,main_vert_min])
        line_outputs[a._type].append([begin,main_vert_max])
        line_outputs[a._type].append([end,main_vert_min])
        line_outputs[a._type].append([end,main_vert_max])
        if a._type in hierarchy.subannotations:
            for stype in hierarchy.subannotations[a._type]:
                subs = getattr(a, stype)
                ind = subannotation_keys[a._type,stype]
                lines, text_poses, texts = generate_subannotation_lines(subs,
                                                ind, sub_size, min_time, max_time)
                line_outputs[a._type, stype].extend(lines)
                text_pos[a._type, stype].extend(text_poses)
                text_labels[a._type, stype].extend(texts)

        for i, t in enumerate(hierarchy.get_lower_types(a._type)):
            elements = getattr(a, t)
            i += 1
            if t == lowest:
                vert_min = 0
                vert_max = size
            else:
                vert_min = max_sig - size * (i+1)
                vert_max = vert_min + size
            vert_mid = (vert_max - vert_min)/2 + vert_min
            for e in elements:
                end = e.end
                begin = e.begin
                if end < min_time:
                    continue
                if begin > max_time:
                    continue
                midpoint = ((end - begin) /2) + begin
                #if (midpoint > max_time or midpoint < min_time) and (begin < min_time and end > max_time):
                #    midpoint = vis_mid
                text = e.label
                if text is None:
                    text = ''
                text_labels[t].append(text)
                text_pos[t].append((midpoint, vert_mid))

                line_outputs[t].append([begin,vert_min])
                line_outputs[t].append([begin,vert_max])
                line_outputs[t].append([end,vert_min])
                line_outputs[t].append([end,vert_max])
                if t in hierarchy.subannotations:
                    for stype in hierarchy.subannotations[t]:
                        subs = getattr(e, stype)
                        ind = subannotation_keys[t,stype]
                        lines, text_poses, texts = generate_subannotation_lines(subs,
                                                ind, sub_size, min_time, max_time)
                        line_outputs[t, stype].extend(lines)
                        text_pos[t, stype].extend(text_poses)
                        text_labels[t, stype].extend(texts)

    text_outputs = {}
    for t in hierarchy.highest_to_lowest:
        line_outputs[t] = np.array(line_outputs[t])
        text_outputs[t] = (text_labels[t], np.array(text_pos[t]))
    for k in subannotation_keys.keys():
        line_outputs[k] = np.array(line_outputs[k])
        text_outputs[k] = (text_labels[k], np.array(text_pos[k]))

    return line_outputs, text_outputs


def rescale(value, oldmax, newmax):
    return value * newmax/oldmax

def generate_subannotation_lines(subs, ind, sub_size, min_time, max_time):
    vis_mid = (max_time - min_time) /2 + min_time
    output = []
    text_output = []
    text_labels = []
    if len(subs) > 1:
        rel_sub_size = sub_size / len(subs)
    else:
        rel_sub_size = sub_size
    for i,s in enumerate(subs):
        sub_vert_min = 0 - sub_size * (ind + 1) + rel_sub_size * i
        sub_vert_max = sub_vert_min + rel_sub_size
        sub_vert_mid = (sub_vert_max - sub_vert_min)/2 + sub_vert_min
        end = s.end
        begin = s.begin
        if end < min_time:
            continue
        if begin > max_time:
            break
        midpoint = ((end - begin) / 2) + begin
        if midpoint > max_time or midpoint < min_time:
            midpoint = vis_mid
        text = s.label
        if text is None:
            text = ''
        text_output.append((midpoint, sub_vert_mid))
        try:
            text = s.label
        except AttributeError:
            text = None
        if text is None:
            text = ''
        text_labels.append(text)
        output.append([begin,sub_vert_min])
        output.append([begin,sub_vert_max])
        output.append([begin, sub_vert_min])
        output.append([end, sub_vert_min])
        output.append([end,sub_vert_min])
        output.append([end,sub_vert_max])
    return output, text_output, text_labels
