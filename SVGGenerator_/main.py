from pathlib import Path

import numpy as np
from PIL import Image
import cv2

#基本設定
DPI = 350
#1インチは25.4mmなので、350dpiをmmに換算する
PX_PER_MM = DPI/25.4 #およそ13.78px/mm
ALPHA_THRESHOLD = 1 #少しでも色がある部分を検知
OFFSET_MM = 2.0 #絵からカット線までの余白　およそ28px

#main.pyのあるフォルダーを基準にする
BASE_DIR = Path(__file__).resolve().parent #SVGGenerator_フォルダーを基準にする
INPUT_PATH = BASE_DIR / "input.png"
OUTPUT_DIR = BASE_DIR / "output"

#mmを画像処理用の整数ピクセル数に変換する
def mm_to_px(mm: float) -> int: # 引数にfloat 戻り値にintを想定することを示す
    return round(mm * PX_PER_MM)

#透過画像前提で読み込む
#画像を読み込み透明度だけを取り出す
def load_alpha(image_path: Path) -> np.ndarray:
    with Image.open(image_path) as image:
        rgba = image.convert("RGBA")
        alpha = np.array(rgba.getchannel("A"))

    return alpha

def create_mask(alpha: np.ndarray, threshold: int) -> np.ndarray:
    #np.where(条件,条件を満たす場合の値,満たさない場合の値)
    mask = np.where(alpha >= threshold, 255, 0).astype(np.uint8)
    return mask

#マスクの白い部分を指定したmmだけ外側に広げる
def expand_mask(mask: np.ndarray, offset_mm: float) -> np.ndarray:
    if offset_mm <= 0:
        raise ValueError("余白は0mm以上にしてください")

    radius_px = mm_to_px(offset_mm)

    #膨張した形が画面端で切れないよう、黒い余白をつける
    padding = radius_px + 1
    padded_mask = np.pad(
        mask,
        pad_width=padding, #配列の両端にpadding分の余白をつける
        mode="constant",
        constant_values=0
    )

    #中心から上下左右にradius_pxだけ届くサイズにする
    kernel_size = radius_px * 2 + 1

    #膨張に使う、円に近い形の型を作る
    kernel = cv2.getStructuringElement( #モルフォロジー変換にて膨張させる
        cv2.MORPH_ELLIPSE, #楕円型カーネル
        (kernel_size, kernel_size),
    )

    #白い領域を広げる
    expanded_mask = cv2.dilate(
        padded_mask,
        kernel,
        iterations=1,#膨張処理一回
    )

    return expanded_mask


#輪郭の座標を抽出する
def extract_contours(mask: np.ndarray) -> list[np.ndarray]:
    #輪郭ごとの座標配列
    contours, _ = cv2.findContours( #境界線を見つける関数
        mask, #輪郭を探す白黒画像
        cv2.RETR_EXTERNAL, #外周だけを取得する。輪郭内部の穴の輪郭は取得しない
        cv2.CHAIN_APPROX_SIMPLE, #直線状に並ぶ中間点を省略する 角の点を残すイメージ
    )

    return list(contours)


#白黒マスクに赤い輪郭を重ねて保存する
def save_contour_preview(
        mask: np.ndarray,
        contours: list[np.ndarray],
        output_path: Path,
) -> None:
    
    #白黒画像を色づけられるRGBに変換する
    preview = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

    #すべての輪郭を赤色で描く
    cv2.drawContours(
        preview,
        contours,
        contourIdx=-1,
        color=(255,0,0),
        thickness=1,
    )

    Image.fromarray(preview).save(output_path)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    #透明度を取り出す
    alpha = load_alpha(INPUT_PATH)

    #白黒マスクに変換する
    mask = create_mask(alpha, ALPHA_THRESHOLD)

    if not np.any(mask):
        raise ValueError("閾値以上の不当明度を持つ部分がありません")

    #NumPy配列をPillowの画像オブジェクトへ変換 画像として保存できるようにする
    Image.fromarray(alpha).save(OUTPUT_DIR / "01_alpha.png")
    Image.fromarray(mask).save(OUTPUT_DIR / "02_mask.png")

    #カット線用の余白を作る
    expanded_mask = expand_mask(mask, OFFSET_MM)
    #膨張後のマスクを保存する
    Image.fromarray(expanded_mask).save(
        OUTPUT_DIR / "03_expanded_mask.png"
    )
    print(f"余白: {OFFSET_MM}mm → {mm_to_px(OFFSET_MM)}px")

    #膨張したマスクから外周を取り出す
    contours = extract_contours(expanded_mask)

    #輪郭を赤線で描いて保存する
    save_contour_preview(
        expanded_mask,
        contours,
        OUTPUT_DIR / "04_contours.png",
    )

    print(f"輪郭の数: {len(contours)}個の点")
    for index, contour in enumerate(contours, start=1): #輪郭を順に取り出しながら、１から始まる番号もつける
        print(f"輪郭{index}: {len(contour)}個の点")


    #350dpiで配置した場合の画像全体の寸法
    height_px, width_px = mask.shape

    print(
        f"350dpiでのサイズ："
        f"{width_px / PX_PER_MM:.2f} x"
        f"{height_px / PX_PER_MM:.2f} mm"
    )

if __name__ == "__main__":
    main()