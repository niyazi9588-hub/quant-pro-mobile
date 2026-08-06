import json
import logging
import sqlite3
import urllib.parse
import urllib.request
import threading
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock

class DatabaseManager:
    def __init__(self, db_dosya='quant_pro_v11_hafiza.db'):
        self.db_dosya = db_dosya
        self.baglanti = sqlite3.connect(self.db_dosya, check_same_thread=False)
        self._veritabani_baslat()

    def _veritabani_baslat(self):
        try:
            cursor = self.baglanti.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS v11_adaptif_hafiza (
                    fon_kodu TEXT PRIMARY KEY,
                    ogrenme_katsayisi REAL,
                    son_tahmin REAL,
                    onceki_fon_fiyati REAL
                )
            """)
            self.baglanti.commit()
        except Exception as e:
            logging.error(f"Veritabanı başlatma hatası: {e}")

    def hafiza_yukle(self, fon_kodu):
        try:
            cursor = self.baglanti.cursor()
            cursor.execute("SELECT ogrenme_katsayisi, son_tahmin, onceki_fon_fiyati FROM v11_adaptif_hafiza WHERE fon_kodu = ?", (fon_kodu,))
            row = cursor.fetchone()
            if row:
                return {'ogrenme_katsayisi': row[0], 'son_tahmin': row[1], 'onceki_fon_fiyati': row[2]}
        except Exception as e:
            logging.error(f"Hafıza yükleme hatası ({fon_kodu}): {e}")
        return {'ogrenme_katsayisi': 1.0, 'son_tahmin': 0.0, 'onceki_fon_fiyati': 0.0}

    def hafiza_kaydet(self, fon_kodu, veri):
        try:
            cursor = self.baglanti.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO v11_adaptif_hafiza 
                (fon_kodu, ogrenme_katsayisi, son_tahmin, onceki_fon_fiyati)
                VALUES (?, ?, ?, ?)
            """, (fon_kodu, veri['ogrenme_katsayisi'], veri['son_tahmin'], veri['onceki_fon_fiyati']))
            self.baglanti.commit()
        except Exception as e:
            logging.error(f"Hafıza kaydetme hatası ({fon_kodu}): {e}")

class QuantProMobilMotor:
    def __init__(self):
        self.db = DatabaseManager()
        self.fon_portfoyleri = {
            'TLY': {
                'tam_ad': 'TLY (Tera Portföy Serbest)', 
                'hisseler': {
                    'OZATD': 34.27, 'DSTKF': 12.02, 'TEHOL': 9.22, 'PEKGY': 8.76, 
                    'HMV': 5.62, 'TERA': 4.11, 'TRHOL': 4.01, 'ANELE': 2.20,
                    'ALKLC': 1.92, 'SELEC': 1.70, 'BIGEN': 1.55, 'HEDEF': 0.57,
                    'SVGYO': 0.52, 'EUPWR': 0.40, 'MANAS': 0.28, 'SARAE': 0.12,
                    'DAPGM': 0.05, 'GESAN': 0.04, 'TMPOL': 0.03, 'YKBNK': 0.03,
                    'METEN': 0.02, 'EFOR': 0.01, 'T3B': 0.01
                }, 
                'nakit_oran': 11.72, 
                'nakit_getiri_orani': 50.0
            },
            'DFI': {
                'tam_ad': 'DFI (Atlas Portföy Serbest)', 
                'hisseler': {
                    'IEYHO': 64.78, 'ABG': 36.00, 'ISKPL': 4.93, 
                    'LIDER': 0.34, 'KVR': 0.21, 'PFS': 0.06
                }, 
                'nakit_oran': -6.32, 
                'nakit_getiri_orani': 50.0
            },
            'TMV': {
                'tam_ad': 'TMV (Tera Algoritmik)', 
                'hisseler': {
                    'OZATD': 17.45, 'TEHOL': 10.54, 'TRHOL': 7.28, 'ANELE': 6.52,
                    'SELEC': 3.74, 'PEKGY': 2.67, 'DSTKF': 2.08, 'ALKLC': 1.89,
                    'EUPWR': 1.68, 'TERA': 1.15, 'GESAN': 0.42, 'TURSG': 0.34,
                    'YKBNK': 0.25, 'AKSEN': 0.21, 'KORDS': 0.21, 'HEDEF': 0.18,
                    'SVGYO': 0.06, 'MANAS': 0.05, 'TMM': 0.03
                }, 
                'nakit_oran': 56.84, 
                'nakit_getiri_orani': 50.0
            }
        }

    def borsa_durumu_kontrol(self):
        simdi = datetime.now()
        haftanin_gunu = simdi.weekday()
        saat = simdi.hour
        dakika = simdi.minute
        toplam_dakika = saat * 60 + dakika

        if haftanin_gunu < 5 and (600 <= toplam_dakika <= 1080):
            return "Borsa Açık", "00FF00"
        else:
            return "Borsa Kapalı", "FF0000"

    def piyasa_verilerini_cek(self, tum_hisseler):
        tickers = [f"BIST:{h}" for h in tum_hisseler]
        tickers.append("BIST:XU100")
        url = "https://scanner.tradingview.com/turkey/scan"
        payload = {"symbols": {"tickers": tickers}, "columns": ["close", "change", "volume", "RSI", "volatilite"]}
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'User-Agent': 'Mozilla/5.0'}, method='POST')
            with urllib.request.urlopen(req, timeout=5) as res:
                res_json = json.loads(res.read().decode('utf-8'))
                bist = {'puan': 13687.93, 'degisim': 2.07}
                fiyatlar = {}
                for item in res_json.get('data', []):
                    s = item.get('s', '').replace('BIST:', '')
                    d = item.get('d', [0.0, 0.0, 0.0, 50.0, 3.0])
                    if s == 'XU100':
                        bist['puan'] = float(d[0]) if d[0] else 13687.93
                        bist['degisim'] = float(d[1]) if d[1] else 2.07
                    else:
                        fiyatlar[s] = {'degisim': float(d[1]) if d[1] else 0.0, 'rsi': float(d[3]) if d[3] else 50.0}
                return bist, fiyatlar
        except Exception as e:
            logging.error(f"Piyasa verileri çekilemedi: {e}")
            return {'puan': 13687.93, 'degisim': 2.07}, {}

    def analiz_yap(self):
        tum_hisseler = {h for f in self.fon_portfoyleri.values() for h in f['hisseler'].keys()}
        bist, fiyatlar = self.piyasa_verilerini_cek(list(tum_hisseler))
        
        borsa_metni, borsa_renk = self.borsa_durumu_kontrol()
        
        bist_renk = "00FF00" if bist['degisim'] >= 0 else "FF0000"
        rapor = f"[b]Borsa Durumu:[/b] [color={borsa_renk}]{borsa_metni}[/color]\n"
        rapor += f"[b]BIST 100:[/b] {bist['puan']:,.2f} ([color={bist_renk}]%{bist['degisim']:+.2f}[/color])\n" + "="*30 + "\n\n"
        
        fon_sonuclari = []
        for fon_kodu, fon_bilgi in self.fon_portfoyleri.items():
            ham_getiri = 0.0
            for hisse, oran in fon_bilgi['hisseler'].items():
                h_degisim = fiyatlar.get(hisse, {}).get('degisim', 0.0)
                ham_getiri += h_degisim * (oran / 100.0)
            
            nakit = fon_bilgi['nakit_oran']
            yillik_faiz = fon_bilgi.get('nakit_getiri_orani', 50.0)
            gunluk_nakit = (((1.0 + (yillik_faiz / 100.0)) ** (1.0 / 365.0)) - 1.0) * (nakit / 100.0) * 100.0
            ham_getiri += gunluk_nakit

            hafiza = self.db.hafiza_yukle(fon_kodu)
            akilli_getiri = ham_getiri * hafiza['ogrenme_katsayisi']
            self.db.hafiza_kaydet(fon_kodu, {'ogrenme_katsayisi': hafiza['ogrenme_katsayisi'], 'son_tahmin': akilli_getiri, 'onceki_fon_fiyati': 100.0})

            skor = akilli_getiri * 1.2
            fon_sonuclari.append((fon_bilgi['tam_ad'], akilli_getiri, skor))

        fon_sonuclari.sort(key=lambda x: x[2], reverse=True)
        for i, (ad, getiri, skor) in enumerate(fon_sonuclari, 1):
            renk = "00FF00" if skor > 0 else "FF0000"
            rapor += f"[b]{i}) {ad}[/b]\n  Skor: [color={renk}]{skor:+.2f}[/color] | Beklenen: %{getiri:>+5.2f}\n\n"
            
        return rapor

class QuantProApp(App):
    def build(self):
        self.motor = QuantProMobilMotor()
        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        self.baslik = Label(text="[b]Fon Tahmin Analiz Programı[/b]\nAkıllı Portföy Takip Sistemi", markup=True, font_size='18sp', size_hint=(1, 0.12), halign='center', valign='middle')
        layout.add_widget(self.baslik)
        
        scroll = ScrollView(size_hint=(1, 0.60))
        self.sonuc_etiketi = Label(text="Analizi başlatmak için butona tıklayın...", markup=True, font_size='13sp', halign='left', valign='top')
        self.sonuc_etiketi.bind(size=lambda s, w: setattr(s, 'text_size', (w[0], None)))
        scroll.add_widget(self.sonuc_etiketi)
        layout.add_widget(scroll)
        
        self.buton = Button(text="Piyasayı ve Fonları Tara", size_hint=(1, 0.12), background_color=(0.1, 0.6, 0.3, 1))
        self.buton.bind(on_press=self.analizi_tetikle)
        layout.add_widget(self.buton)
        
        self.kayan_metin = "[ DİKKAT: YATIRIM TAVSİYESİ DEĞİLDİR ]   |   " * 5
        self.kayan_etiket = Label(text=self.kayan_metin, font_size='12sp', size_hint=(1, 0.08), color=(1, 0.8, 0.2, 1))
        layout.add_widget(self.kayan_etiket)
        
        Clock.schedule_interval(self.akan_yaziyi_guncelle, 0.1)
        
        return layout

    def akan_yaziyi_guncelle(self, dt):
        self.kayan_metin = self.kayan_metin[1:] + self.kayan_metin[0]
        self.kayan_etiket.text = self.kayan_metin

    def analizi_tetikle(self, instance):
        self.buton.disabled = True
        self.sonuc_etiketi.text = "Veriler çekiliyor ve hesaplanıyor, lütfen bekleyin..."
        threading.Thread(target=self._arkaplanda_analiz_yap, daemon=True).start()

    def _arkaplanda_analiz_yap(self):
        try:
            sonuc_metni = self.motor.analiz_yap()
        except Exception as e:
            sonuc_metni = f"[color=FF0000]Hata Oluştu:[/color] {str(e)}"
        
        Clock.schedule_once(lambda dt: self.arayuzu_guncelle(sonuc_metni), 0)

    def arayuzu_guncelle(self, sonuc_metni):
        self.sonuc_etiketi.text = sonuc_metni
        self.buton.disabled = False

if __name__ == '__main__':
    QuantProApp().run()
