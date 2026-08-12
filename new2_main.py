import flet as ft
import time
import math
import random
import traceback

def get_ip():
    import requests
    url = "http://metadata.google.internal/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip"
    headers = {"Metadata-Flavor": "Google"}
    try:
        return requests.get(url, headers=headers, timeout=2).text
    except:
        return "localhost"

def main(page: ft.Page):

    page.title = "Hamburger Game"

    page.window_width = 900
    page.window_height = 650

    page.padding = 20

    # -------------------------
    # 画面サイズ
    # -------------------------

    WIDTH = 800
    HEIGHT = 450

    # -------------------------
    # 物理パラメータ
    # -------------------------

    G_ACC = 300   # 重力
    DT = 0.02     # 時間刻み
    POWER = 5     # 投げる強さ
    K = 0.5       # 空気抵抗

    # -------------------------
    # 何回失敗したらゲームオーバーか
    # -------------------------

    MAX_FAILS = 10

    # -------------------------
    # 画像パス
    # -------------------------

    waitress_path = "waitress_transparent.png"
    table_path = "table_transparent.png"

    # -------------------------
    # レシピ定義
    # -------------------------

    RECIPES = {
        "tomato_burger_transparent.png": [
            "bun_transparent.png",
            "patty_transparent.png",
            "lettuce_transparent.png",
            "tomato_transparent.png",
            "pan_transparent.png",
        ],
        "cheese_burger_transparent.png": [
            "bun_transparent.png",
            "patty_transparent.png",
            "cheese_transparent.png",
            "lettuce_transparent.png",
            "tomato_transparent.png",
            "pan_transparent.png",
        ],
        "meet_burger_transparent.png": [
            "bun_transparent.png",
            "patty_transparent.png",
            "tomato_transparent.png",
            "bacon_transparent.png",
            "tomato_transparent.png",
            "pickle_transparent.png",
            "pan_transparent.png",
        ],
        "Wcheese_burger_transparent.png": [
            "bun_transparent.png",
            "patty_transparent.png",
            "cheese_transparent.png",
            "patty_transparent.png",
            "cheese_transparent.png",
            "pan_transparent.png",
        ],
        "monster_transparent.png": [
            "bun_transparent.png",
            "lettuce_transparent.png",
            "tomato_transparent.png",
            "pickle_transparent.png",
            "patty_transparent.png",
            "cheese_transparent.png",
            "bacon_transparent.png",
            "patty_transparent.png",
            "cheese_transparent.png",
            "bacon_transparent.png",
            "egg_burger_transparent.png",
            "tomato_transparent.png",
            "lettuce_transparent.png",
            "pan_transparent.png",
        ],
    }

    order_sequence = [
        "tomato_burger_transparent.png",
        "cheese_burger_transparent.png",
        "meet_burger_transparent.png",
        "Wcheese_burger_transparent.png",
        "monster_transparent.png",
    ]

    bad_ingredients = [
        "ball_transparent.png",
        "bug_transparent.png",
        "cake_transparent.png",
        "ice_transparent.png",
    ]

    rare_bad_ingredients = [
        "G_transparent.png",
    ]

    # -------------------------
    # 状態
    # -------------------------

    dragging = False
    flying = False
    round_over = False

    order_index = 0
    table_stage = True
    recipe_index = 0
    stack_count = 0
    fail_count = 0

    START_X = 100
    START_Y = 220

    cheese_x = START_X
    cheese_y = START_Y

    drag_x = cheese_x
    drag_y = cheese_y

    vx = 0
    vy = 0

    waitress_x = 650
    waitress_y = 180

    hand_x = waitress_x - 20
    hand_y = waitress_y + 80

    current_order = order_sequence[order_index]
    current_recipe = RECIPES[current_order]

    # -------------------------
    # 画像・テキストコントロール
    # -------------------------

    waitress_img = ft.Image(
        src=waitress_path,
        width=120,
        height=180,
        left=waitress_x,
        top=waitress_y,
    )

    order_preview_label = ft.Text(
        "お題",
        size=14,
        weight=ft.FontWeight.BOLD,
        left=10,
        top=5,
    )

    order_preview_img = ft.Image(
        src=current_order,
        width=100,
        height=100,
        left=10,
        top=28,
    )

    status_text = ft.Text(
        "",
        size=20,
        weight=ft.FontWeight.BOLD,
    )

    fail_text = ft.Text(
        f"失敗: 0 / {MAX_FAILS}",
        size=14,
        color=ft.Colors.GREY_700,
    )

    order_bg = ft.Container(
        width=WIDTH,
        height=HEIGHT,
        bgcolor=ft.Colors.with_opacity(0.6, ft.Colors.BLACK),
        left=0,
        top=0,
        visible=False,
    )

    order_text = ft.Text(
        "",
        size=24,
        color=ft.Colors.WHITE,
        weight=ft.FontWeight.BOLD,
        left=WIDTH / 2 - 120,
        top=HEIGHT / 2 - 30,
        width=240,
        text_align=ft.TextAlign.CENTER,
        visible=False,
    )

    # 常に画面に残しておきたいコントロール(積み上げ具材は含まない)
    def base_controls():
        return [
            waitress_img,
            order_preview_label,
            order_preview_img,
            order_bg,
            order_text,
            next_btn,
        ]

    def next_round(e):
        nonlocal stack_count, round_over, table_stage, recipe_index
        nonlocal order_index, current_order, current_recipe, fail_count, current_img
        nonlocal flying

        flying = False

        # 具材(積み上げ画像)を含め、いったん全部リストから除去してまっさらにする
        # base_controls() に入っていない物は、直前ラウンドの積み上げ具材とみなして全部消す
        keep = base_controls()
        stack.controls = [c for c in stack.controls if c in keep]

        # 前ラウンドの投擲物への参照も完全に切っておく
        current_img = None

        stack_count = 0
        table_stage = True
        recipe_index = 0
        fail_count = 0
        fail_text.value = f"失敗: 0 / {MAX_FAILS}"
        status_text.value = ""

        cheese_x = START_X
        cheese_y = START_Y
        drag_x =START_X
        drag_Y =START_Y

        order_index = (order_index + 1) % len(order_sequence)
        current_order = order_sequence[order_index]
        current_recipe = RECIPES[current_order]
        order_preview_img.src = current_order

        order_bg.visible = False
        order_text.visible = False
        next_btn.visible = False
        round_over = False

        new_throw_object(START_X, START_Y)
        draw_scene()

        page.update()

    next_btn = ft.ElevatedButton(
        "次のお題へ",
        left=WIDTH / 2 - 60,
        top=HEIGHT / 2 + 50,
        visible=False,
        on_click=next_round,
    )

    stack = ft.Stack(
        controls=[
            waitress_img,
            order_preview_label,
            order_preview_img,
            order_bg,
            order_text,
            next_btn,
        ],
        width=WIDTH,
        height=HEIGHT,
    )

    debug_container = ft.Container(
        content=stack,
        width=WIDTH,
        height=HEIGHT,
    )

    current_img = None
    current_target = None

    # -------------------------
    # 新しい投擲物を生成
    # -------------------------

    def new_throw_object(x, y):
        nonlocal current_img, current_target

        if table_stage:
            src = table_path
            current_target = table_path

        else:
            target = current_recipe[recipe_index]
            current_target = target

            decoy_pool = list(set(current_recipe) - {target}) + bad_ingredients
            decoy_weights = [1] * len(decoy_pool)

            pool = [target] + decoy_pool + rare_bad_ingredients
            weights = [4] + decoy_weights + [0.3] * len(rare_bad_ingredients)

            src = random.choices(pool, weights=weights, k=1)[0]

        current_img = ft.Image(
            src=src,
            width=60,
            height=60,
            left=x,
            top=y,
        )

        stack.controls.append(current_img)

    # -------------------------
    # ラウンド終了演出
    # -------------------------

    def end_round(success):
        nonlocal round_over
        round_over = True

        for c in [order_bg, order_text, next_btn]:
            if c in stack.controls:
                stack.controls.remove(c)
            stack.controls.append(c)

        order_bg.visible = True

        if success:
            order_text.value = "🎉 完成！\n" + current_order.replace("_transparent.png", "")
        else:
            order_text.value = "💥 ゲームオーバー…\n次のお題に挑戦しよう！"

        order_text.visible = True
        next_btn.visible = True

        page.update()

    # -------------------------
    # 描画
    # -------------------------

    def draw_scene():
        waitress_img.left = waitress_x
        waitress_img.top = waitress_y

        if current_img is not None:
            current_img.left = cheese_x
            current_img.top = cheese_y

    # -------------------------
    # マウス押した
    # -------------------------

    def on_pan_start(e: ft.DragStartEvent):

        nonlocal dragging

        if round_over:
            return

        

        distance = math.sqrt(
            (e.local_x - cheese_x)**2
            +
            (e.local_y - cheese_y)**2
        )

        if distance < 60 and not flying:

            dragging = True

    # -------------------------
    # ドラッグ中
    # -------------------------

    def on_pan_update(e: ft.DragUpdateEvent):

        nonlocal drag_x, drag_y
        nonlocal cheese_x, cheese_y

        if dragging:

            drag_x += e.delta_x
            drag_y += e.delta_y

            cheese_x = drag_x
            cheese_y = drag_y

            draw_scene()
            page.update()

    # -------------------------
    # 離した
    # -------------------------

    def on_pan_end(e: ft.DragEndEvent):

        nonlocal dragging
        nonlocal flying
        nonlocal vx, vy

        if dragging:

            dragging = False

            flying = True

            vx = (START_X - cheese_x) * POWER
            vy = (START_Y - cheese_y) * POWER

            simulate()

    # -------------------------
    # 物理シミュレーション
    # -------------------------

    def simulate():

        nonlocal flying
        nonlocal cheese_x, cheese_y
        nonlocal vx, vy
        nonlocal drag_x, drag_y
        nonlocal stack_count
        nonlocal round_over
        nonlocal table_stage
        nonlocal recipe_index
        nonlocal fail_count
        
        try:

            while flying:

                ax = -K * vx
                ay = G_ACC - K * vy

                vx += ax * DT
                vy += ay * DT

                cheese_x += vx * DT
                cheese_y += vy * DT

                cheese_center_x = cheese_x + 30
                cheese_center_y = cheese_y + 30

                distance = math.sqrt(
                    (cheese_center_x - hand_x)**2
                    +
                    (cheese_center_y - hand_y)**2
                )

                caught = distance < 90
                out_of_screen = cheese_x > WIDTH or cheese_y > HEIGHT

                if caught:

                    is_correct = (current_img.src == current_target)

                    if not is_correct:

                        # ---- 失敗(間違った物をキャッチした) ----
                        fail_count += 1

                        status_text.value = "❌ 失敗！(違う具材・テーブルをキャッチした)"
                        status_text.color = ft.Colors.RED

                        flying = False

                        if current_img in stack.controls:
                            stack.controls.remove(current_img)

                        fail_text.value = f"失敗: {fail_count} / {MAX_FAILS}"

                        if fail_count >= MAX_FAILS:
                            flying=False
                            end_round(success=False)
                            page.update()
                            return

                    else:

                        # ---- 成功 ----
                        status_text.value = "✅ キャッチ成功！"
                        status_text.color = ft.Colors.GREEN

                        flying = False

                        cheese_x = hand_x - 30
                        cheese_y = hand_y - 40 - (stack_count * 20)
                        draw_scene()

                        stack_count += 1

                        if table_stage:
                            table_stage = False
                        else:
                            recipe_index += 1

                            if recipe_index >= len(current_recipe):
                                flying=False
                                end_round(success=True)
                                page.update()
                                return

                    # 次の1投を生成
                    cheese_x = START_X
                    cheese_y = START_Y
                    drag_x = START_X
                    drag_y = START_Y
                    new_throw_object(START_X, START_Y)

                elif out_of_screen:

                    is_correct_target = (current_img.src == current_target)

                    if is_correct_target:

                        # ---- 本当の失敗(正解の具材を逃した) ----
                        fail_count += 1

                        status_text.value = "❌ 失敗！(正しい具材を落としてしまった)"
                        status_text.color = ft.Colors.RED

                        fail_text.value = f"失敗: {fail_count} / {MAX_FAILS}"

                    else:

                        # ---- 回避(違う具材を正しく避けられた) ----
                        status_text.value = "😌 回避！(違う具材を避けられた)"
                        status_text.color = ft.Colors.BLUE

                    flying = False

                    if current_img in stack.controls:
                        stack.controls.remove(current_img)

                    if is_correct_target and fail_count >= MAX_FAILS:
                        end_round(success=False)
                        page.update()
                        return

                    cheese_x = START_X
                    cheese_y = START_Y
                    drag_x = START_X
                    drag_y = START_Y
                    new_throw_object(START_X, START_Y)

                draw_scene()

                page.update()

                time.sleep(DT)

        except Exception:
            print("=== simulate()内でエラーが発生しました ===")
            traceback.print_exc()

            flying = False
            status_text.value = "⚠️ エラーが発生しました。もう一度投げてみてください。"
            status_text.color = ft.Colors.ORANGE

            if current_img is not None and current_img in stack.controls:
                stack.controls.remove(current_img)

            try:
                cheese_x = START_X
                cheese_y = START_Y
                drag_x = START_X
                drag_y = START_Y
                new_throw_object(START_X,START_Y)
                draw_scene()
                page.updata()
            except Exception:
                print("=== 復旧処理でもエラーが発生しました ===")
                traceback.print_exc()
                status_text.valu="復旧できませんでした。ページを再読み込みしてください。"
                page.updata()

            
    # -------------------------
    # 起動
    # -------------------------

    new_throw_object(START_X, START_Y)
    draw_scene()

    gesture = ft.GestureDetector(
        content=debug_container,
        on_pan_start=on_pan_start,
        on_pan_update=on_pan_update,
        on_pan_end=on_pan_end,
        width=WIDTH,
        height=HEIGHT,
    )
    page.add(
    ft.Column(
        [
            ft.Row(
                [
                    ft.Text(
                        "🍔 Hamburger Game",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "Shibata Ikumi & Kikuchi Mii",
                        size=18,
                    ),
                ],
                spacing=10,
            ),

            ft.Row(
                [status_text, fail_text],
                spacing=20,
            ),

            gesture,
        ]
    )
)

        

    page.update()


    
   

print("Open the app at browser: http://%s" % (get_ip() + ":8550"))
ft.app(target=main, view=ft.WEB_BROWSER, port=8550, host="0.0.0.0", assets_dir="images")
