# pyrefly: ignore [missing-import]
import inkex# inkexというパッケージをインポートする

class ChangeFillExtension(inkex.extensions.EffectExtension):
                                         # ↑EffectExtensionクラスを継承
    def add_arguments(self, pars):
        pass   # パラメーターが渡されるけれどこのサンプルでは無視

    def effect(self):  # 実行されると必ず呼び出される
        for elem in self.svg.selection:
            elem.style['fill'] = '#00ff00'  # フィルに緑をセット

if __name__ == '__main__':# エクステンションはここから実行される
    ChangeFillExtension().run()