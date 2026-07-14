import base64  # 【追加】画像を埋め込むためのライブラリ
# pyrefly: ignore [missing-import]
from PIL import Image
import numpy as np
# pyrefly: ignore [missing-import]
import cv2
# pyrefly: ignore [missing-import]
import svgwrite

# ==========================
# 設定
# ==========================

DEFAULT_SIMPLIFY_RATIO = 0.0005
DEFAULT_OFFSET_PX = 15
DEFAULT_BASE_OFFSET = 5

def create_svg(
        input_png,
        output_svg,
        simplify_ratio=DEFAULT_SIMPLIFY_RATIO,
        offset_px=DEFAULT_OFFSET_PX,
        base_offset_px=DEFAULT_BASE_OFFSET,
        tab_width=60,
        tab_height=20,
        base_rx=100,
        base_ry=60,
        bottom_width=200,
):

    # ==========================
    # PNG読み込み & Base64埋め込み用データ変換
    # ==========================
    img = Image.open(input_png).convert("RGBA")
    img_np = np.array(img)

    height, width = img_np.shape[:2]
    alpha = img_np[:, :, 3]

    # 【追加】画像をInkscape等で確実に表示させるため、Base64形式のデータURIに変換する
    with open(input_png, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode("utf-8")
    image_data_uri = f"data:image/png;base64,{encoded_string}"

    # ==========================
    # 台座サイズの計算と余白（パディング）の追加
    # ==========================
    x_orig, y_orig, w_orig, h_orig = cv2.boundingRect(alpha)
    if w_orig == 0: w_orig = width
    if h_orig == 0: h_orig = height

    rx = base_rx
    ry = base_ry

    pad_top = offset_px + base_offset_px + 20
    pad_left = pad_right = max(pad_top, rx + 50, bottom_width // 2 + 50)
    pad_bottom = pad_top + tab_height + 30 + ry * 2 + 50

    alpha_padded = cv2.copyMakeBorder(alpha, pad_top, pad_bottom, pad_left, pad_right, cv2.BORDER_CONSTANT, value=0)

    # ==========================
    # 輪郭抽出
    # ==========================
    blurred = cv2.GaussianBlur(alpha_padded, (5, 5), 0)
    _, alpha_smooth = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY)

    contours_white, _ = cv2.findContours(alpha_smooth, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    base_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * base_offset_px + 1, 2 * base_offset_px + 1))
    alpha_base = cv2.dilate(alpha_smooth, base_kernel, iterations=1)

    contours_base, _ = cv2.findContours(alpha_base, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    if offset_px > 0:
        cut_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * offset_px + 1, 2 * offset_px + 1))
        alpha_cut = cv2.dilate(alpha_base, cut_kernel, iterations=1)
    else:
        alpha_cut = alpha_base.copy()

    # --- 本体の下部を埋めて真っ直ぐにする ---
    cnts_tmp, _ = cv2.findContours(alpha_cut, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if cnts_tmp:
        all_pts = np.vstack(cnts_tmp)
        bx, by, bw, bh = cv2.boundingRect(all_pts)
        cx = bx + bw // 2
        bottom_y = by + bh

        fill_h = max(20, int(bh * 0.15))
        
        cv2.rectangle(
            alpha_cut,
            (cx - bottom_width // 2, bottom_y - fill_h),
            (cx + bottom_width // 2, bottom_y),
            255, -1
        )

        cv2.rectangle(
            alpha_cut, 
            (cx - tab_width // 2, bottom_y - 2), 
            (cx + tab_width // 2, bottom_y + tab_height), 
            255, -1
        )

    contours_cut, _ = cv2.findContours(alpha_cut, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    # --- 台座（穴あき楕円） ---
    contours_stand = []
    if cnts_tmp:
        base_mask = np.zeros_like(alpha_padded)
        base_cx = cx
        base_cy = bottom_y + tab_height + 30 + ry

        cv2.ellipse(base_mask, (base_cx, base_cy), (rx, ry), 0, 0, 360, 255, -1)
        cv2.rectangle(
            base_mask, 
            (base_cx - tab_width // 2, base_cy - tab_height // 2), 
            (base_cx + tab_width // 2, base_cy + tab_height // 2), 
            0, -1
        )
        contours_stand, _ = cv2.findContours(base_mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

    # ==========================
    # SVG作成
    # ==========================
    new_width = width + pad_left + pad_right
    new_height = height + pad_top + pad_bottom

    dwg = svgwrite.Drawing(output_svg, size=(new_width, new_height), viewBox=f"0 0 {new_width} {new_height}")

    def make_svg_path(contours):
        d_list = []
        for contour in contours:
            arc = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon=simplify_ratio * arc, closed=True)
            pts = approx.squeeze()
            if len(pts.shape) == 1 or len(pts) < 3: continue
            segment = f"M {pts[0][0]} {pts[0][1]}"
            for p in pts[1:]: segment += f" L {p[0]} {p[1]}"
            segment += " Z"
            d_list.append(segment)
        return " ".join(d_list)

    d_white = make_svg_path(contours_white)
    d_base = make_svg_path(contours_base)
    d_cut = make_svg_path(contours_cut)
    d_stand = make_svg_path(contours_stand)

    d_cut_combined = d_cut + " " + d_stand
    
    cut_layer = dwg.g(id="Cut")
    cut_layer.add(dwg.path(d=d_cut_combined, fill="none", stroke="red", stroke_width=5))
    white_layer = dwg.g(id="White")
    white_layer.add(dwg.path(d=d_white, fill="white", stroke="none"))
    
    image_layer = dwg.g(id="CMYKRe")
    # 【変更】href にファイルのパスではなく、生成した image_data_uri を指定します
    image_layer.add(dwg.image(href=image_data_uri, insert=(pad_left, pad_top), size=(width, height)))
    image_layer.add(dwg.path(d=d_base, fill="none", stroke="red", stroke_width=5))

    dwg.add(cut_layer)
    dwg.add(white_layer)
    dwg.add(image_layer)
    dwg.save()