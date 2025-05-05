import maya.cmds as cmds


def create_uv_position_list(body_map_list):
    """
    指定されたUVコンポーネントのリストからUV座標情報を含む辞書のリストを作成します。

    Args:
        body_map_list (list of str): UVコンポーネント名のリスト。
            例: ["pCube1.map[0]", "pCube1.map[1]"]

    Returns:
        list of dict: UV座標情報を含む辞書のリスト。各辞書には以下のキーが含まれます:
            - "uvNumber" (str): UVコンポーネントの名前。
            - "uValue" (float): UVのU座標。
            - "vValue" (float): UVのV座標。
    """
    # 検索対象のUV座標を取得
    uv_positions = []
    for body_map in body_map_list:
        pos = cmds.polyEditUV(body_map, q=True)

        _ = {}
        _["uvNumber"] = body_map
        _["uValue"] = pos[0]
        _["vValue"] = pos[1]

        uv_positions.append(_)

    return uv_positions


def compare_uv_position(src, dst):
    """
    2つのUV座標リストを比較し、`dst`リスト内の各UVに最も近い`src`リストのUV座標を割り当てます。

    Args:
        src (list of dict): 検索元のUV座標リスト。
            各辞書には以下のキーが含まれます:
            - "uValue" (float): UVのU座標。
            - "vValue" (float): UVのV座標。
        dst (list of dict): 検索対象のUV座標リスト。
            各辞書には以下のキーが含まれます:
            - "uValue" (float): UVのU座標。
            - "vValue" (float): UVのV座標。

    Returns:
        list of dict: 更新された`dst`リスト。
            各辞書には、元のデータに加えて以下のキーが追加されます:
            - "closest_u" (float): 最も近い`src`のU座標。
            - "closest_v" (float): 最も近い`src`のV座標。

    Note:
        検索の際、しきい値（`threshold`）は、GUIのスライダーグループ
        "threshold_slider"の値から取得されます。
        UV間の距離がしきい値を超える場合、そのペアは無視されます。
        処理の高速化のために設けています。
    """

    threshold = cmds.floatSliderGrp("threshold_slider", q=True, value=1)

    for dst_item in dst:
        # 最も近い座標を見つけるための初期設定
        min_distance = float('inf')  # 非常に大きい初期値

        target_u = dst_item["uValue"]
        target_v = dst_item["vValue"]

        # 各座標の距離を計算し、最も近い座標を検索
        for src_item in src:
            coord_u = src_item["uValue"]
            coord_v = src_item["vValue"]

            if threshold < abs(coord_u - target_u):
                continue

            if threshold < abs(coord_v - target_v):
                continue

            distance = ((coord_u - target_u) ** 2 +
                        (coord_v - target_v) ** 2) ** 0.5  # ユークリッド距離
            if distance < min_distance:
                min_distance = distance
                dst_item["closest_u"] = coord_u
                dst_item["closest_v"] = coord_v

    return dst


def overlap_uv(*args):
    # ========================================
    # 検索対象のUVを取得
    # ========================================
    # 選択中のUVアイランドのUV頂点を取得
    selected_uvs = cmds.ls(sl=True, flatten=True)
    cmds.ConvertSelectionToUVShell(selected_uvs)
    selected_uv_island = cmds.ls(sl=True, flatten=True)
    cmds.select(selected_uvs)

    # 選択中のシェイプのUV座標をすべて取得
    search_shape = cmds.listRelatives(selected_uvs, p=True, type="shape")[0]
    search_uv_set = cmds.polyUVSet(search_shape, q=True, currentUVSet=True)
    all_uvs = cmds.ls(f"{search_shape}.map[*]", flatten=True)

    # 集合演算で選択中のアイランドだけ検索対象から除外する（自分自身にヒットしないように）
    search_uvs = list(set(all_uvs) - set(selected_uv_island))

    # 検索対象のUV座標を取得する
    src_uv_pos = create_uv_position_list(search_uvs)

    # 選択中のUV座標を取得する
    dst_uv_pos = create_uv_position_list(selected_uvs)

    # 近傍UVスナップ処理
    dst_uv_pos = compare_uv_position(src_uv_pos, dst_uv_pos)

    # UVを移動
    for item in dst_uv_pos:
        try:
            cmds.polyEditUV(item["uvNumber"],
                            uValue=item["closest_u"], vValue=item["closest_v"],
                            relative=False)
        except KeyError:
            cmds.warning("近傍の頂点が見つかりませんでした。しきい値が小さすぎる可能性があります。")
            return

def overlap_uv_island(*args):
    threshold = cmds.floatSliderGrp("threshold_slider", q=True, value=1)

    # ========================================
    # trackSelectionOrderが無効化されていたら、一時的に有効化する
    # ========================================
    if not cmds.selectPref(q=True, trackSelectionOrder=True):
        tso = "False"
        cmds.selectPref(trackSelectionOrder=True)
    else:
        tso = "True"

    # ========================================
    # 検索対象のUVを取得
    # ========================================
    # 選択中のUVアイランドを取得してUV頂点リストに変換
    sel_shell = cmds.ls(os=True, flatten=True)
    converted_uvs = cmds.polyListComponentConversion(sel_shell, toUV=True)
    sel_uvs = cmds.ls(converted_uvs, flatten=True)

    all_uvs = {}
    for sel_uv in sel_uvs:
        sel_id = cmds.polyEvaluate(sel_uv, uvShellIds=True)[0]
        key = f"uvshell_{sel_id}"
        if key in all_uvs:
            all_uvs[key].append(sel_uv)
        else:
            all_uvs[key] = [sel_uv]

    # srcを抜き出す
    search_uvs = list(all_uvs.values())[:-1]  # 最後以外
    if len(search_uvs) >= 2:
        search_uvs = [item for sublist in search_uvs for item in sublist]

    # dstを抜き出す
    selected_uvs = list(all_uvs.values())[-1]  # 最後だけ

    # 検索対象のUV座標を取得する
    src_uv_pos = create_uv_position_list(search_uvs)

    # 選択中のUV座標を取得する
    dst_uv_pos = create_uv_position_list(selected_uvs)

    # 近傍UVスナップ処理
    dst_uv_pos = compare_uv_position(src_uv_pos, dst_uv_pos)

    # UVを移動
    for item in dst_uv_pos:
        cmds.polyEditUV(item["uvNumber"],
                        uValue=item["closest_u"], vValue=item["closest_v"],
                        relative=False)

    # ========================================
    # trackSelectionOrderの設定をもとに戻す     
    # 
    # ToDo 取得の瞬間だけプリファレンスをオフにして取得が終わったらすぐ戻す 位置変更
    # ========================================
    if tso == "False":
        cmds.selectPref(trackSelectionOrder=False)


def gui():
    if cmds.window("gui_overlap_uv", exists=True):
        cmds.deleteUI("gui_overlap_uv")

    col = 2
    window_w = 240
    window_h = 100
    slider_h = 0.3
    slider_label = 0.25
    slider_field = 0.15
    slider_slider = 0.6

    window = cmds.window("gui_overlap_uv", title="uwe_overlap_uv",
                         width=window_w, height=window_h)

    cmds.columnLayout(adjustableColumn=2)
    cmds.floatSliderGrp("threshold_slider", label='Threshold', field=True, value=0.025,
                        minValue=0.025, maxValue=0.1,
                        fieldMinValue=0.001, fieldMaxValue=0.1, sliderStep=0.001,
                        width=window_w, height=window_h * slider_h,
                        cw3=(window_w * slider_label, window_w * slider_field, window_w * slider_slider))

    cmds.rowLayout(numberOfColumns=col, adj=1)
    cmds.button(label="Overlap UV", command=overlap_uv,
                width=window_w / col, height=window_h * (1 - slider_h))
    # cmds.button(label="Overlap UV Island", command=overlap_uv_island,
    #            width=window_w/col, height=window_h*(1-slider_h))
    cmds.setParent('..')  # row
    cmds.setParent('..')  # column

    cmds.showWindow(window)
