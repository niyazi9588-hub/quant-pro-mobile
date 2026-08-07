
import json
import time
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# Renkler
YESIL = "\033[92m"
KIRMIZI = "\033[91m"
RESET = "\033[0m"
SARI = "\033[93m"
BEYAZ = "\033[1m"
MAVI = "\033[94m"

class VeritabaniYoneticisi:
    def __init__(self, db_dosya="fon_analiz_v12.db"):
        self.db_dosya = db_dosya
        self.baglanti_kur()

    def baglanti_kur(self):
        try:
            with sqlite3.connect(self.db_dosya) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tahmin_gecmisi (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        zaman TEXT,
                        fon_kodu TEXT,
                        tahmin REAL,
                        gercek_nav REAL,
                        hata REAL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS portfoy_cache (
                        fon_kodu TEXT PRIMARY KEY,
                        guncelleme_tarihi TEXT,
                        veri_json TEXT
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            print(f"{KIRMIZI}[Kritik Veritabanı Hatası] {e}{RESET}")

    def kayit_ekle(self, fon_kodu, tahmin, gercek_nav=None):
        zaman = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        hata = abs(tahmin - gercek_nav) if gercek_nav is not None else None
        try:
            with sqlite3.connect(self.db_dosya) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO tahmin_gecmisi (zaman, fon_kodu, tahmin, gercek_nav, hata)
                    VALUES (?, ?, ?, ?, ?)
                """, (zaman, fon_kodu, tahmin, gercek_nav, hata))
                conn.commit()
        except sqlite3.Error as e:
            print(f"{KIRMIZI}[Veritabanı Kayıt Hatası] {e}{RESET}")

    def cache_portfoy_getir(self, fon_kodu):
        bugun = datetime.now().strftime("%Y-%m-%d")
        try:
            with sqlite3.connect(self.db_dosya) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT veri_json FROM portfoy_cache WHERE fon_kodu = ? AND guncelleme_tarihi = ?", (fon_kodu, bugun))
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except (sqlite3.Error, json.JSONDecodeError) as e:
            print(f"{SARI}[Cache Okuma Uyarısı] {e}{RESET}")
        return None

    def cache_portfoy_kaydet(self, fon_kodu, veri):
        bugun = datetime.now().strftime("%Y-%m-%d")
        try:
            veri_json = json.dumps(veri)
            with sqlite3.connect(self.db_dosya) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO portfoy_cache (fon_kodu, guncelleme_tarihi, veri_json)
                    VALUES (?, ?, ?)
                """, (fon_kodu, bugun, veri_json))
                conn.commit()
        except (sqlite3.Error, TypeError) as e:
            print(f"{KIRMIZI}[Cache Kayıt Hatası] {e}{RESET}")

class CacheYoneticisi:
    def __init__(self):
        self.depo = {}

    def veri_al(self, anahtar, maksimum_sure):
        if anahtar in self.depo:
            kayit = self.depo[anahtar]
            if time.time() - kayit["zaman"] < maksimum_sure:
                return kayit["veri"]
        return None

    def veri_yaz(self, anahtar, veri):
        self.depo[anahtar] = {"zaman": time.time(), "veri": veri}

class PortfoyDinamikYoneticisi:
    def __init__(self, db_yoneticisi):
        self.db = db_yoneticisi
        self.fon_kodlari = ["TLY", "DFI", "TMV"]

    def fon_portfoylerini_cek(self):
        portfoyler = {}
        for kod in self.fon_kodlari:
            cached_data = self.db.cache_portfoy_getir(kod)
            if cached_data:
                portfoyler[kod] = cached_data
                continue

            canli_veri = self._kap_tefas_sorgula(kod)
            if canli_veri and isinstance(canli_veri, dict) and "hisseler" in canli_veri:
                self.db.cache_portfoy_kaydet(kod, canli_veri)
                portfoyler[kod] = canli_veri
            else:
                portfoyler[kod] = self._guvenli_varsayilan_getir(kod)
        return portfoyler

    def _kap_tefas_sorgula(self, fon_kodu):
        try:
            url = f"https://seffaflik.tefas.gov.tr/api/fas/v1/fonlar/portfoy-dagilimi/{fon_kodu}"
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Accept': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                res_text = response.read().decode('utf-8')
                res_json = json.loads(res_text)
                if res_json and isinstance(res_json, dict):
                    return res_json
            return None 
        except Exception:
            return None

    def _guvenli_varsayilan_getir(self, fon_kodu):
        if fon_kodu == "TLY":
            return {
                "hedef_hisse_orani": 78.50,
                "hisseler": {
                    "OZATD": 34.27, "DSTKF": 12.02, "TEHOL": 9.22, "PEKGY": 8.76,
                    "HMV": 5.50, "TERA": 4.11, "TRHOL": 4.00, "ANELE": 2.20,
                    "ALKLC": 1.92, "SELEC": 1.70, "BIGEN": 1.55, "HEDEF": 0.50,
                    "SVGYO": 0.50, "EUPWR": 0.40, "MANAS": 0.25, "SARAE": 0.15,
                    "DAPGM": 0.05, "GESAN": 0.05, "TMPOL": 0.03, "YKBNK": 0.03,
                    "METEN": 0.02, "EFOR": 0.01, "T3B": 0.01
                },
                "nakit_oran": 21.50,
                "nakit_getiri_orani": 50.0,
                "viop_pozisyonlar": {"uzun": 2.0, "kisa": 0.0, "teminat": 5.0, "teminat_faiz": 50.0},
                "yonetim_ucreti": 2.5,
                "fon_gider": 0.5
            }
        elif fon_kodu == "DFI":
            return {
                "hedef_hisse_orani": 45.00,
                "hisseler": {
                    "IEYHO": 31.20, "ABG": 11.00, "ISKPL": 4.20, "LIDER": 0.80, 
                    "KVR": 0.40, "PFS": 0.30
                },
                "nakit_oran": 55.00,
                "nakit_getiri_orani": 50.0,
                "viop_pozisyonlar": {"uzun": 0.0, "kisa": 0.0, "teminat": 10.0, "teminat_faiz": 50.0},
                "yonetim_ucreti": 3.0,
                "fon_gider": 0.6
            }
        elif fon_kodu == "TMV":
            return {
                "hedef_hisse_orani": 52.00,
                "hisseler": {
                    "OZATD": 17.45, "TEHOL": 10.54, "TRHOL": 7.28, "ANELE": 6.52,
                    "SELEC": 3.74, "PEKGY": 2.60, "DSTKF": 2.00, "ALKLC": 1.80,
                    "EUPWR": 1.60, "TERA": 1.10, "GESAN": 0.40, "TURSG": 0.30,
                    "YKBNK": 0.25, "AKSEN": 0.20, "KORDS": 0.20, "HEDEF": 0.15,
                    "SVGYO": 0.08, "MANAS": 0.07, "TMM": 0.05
                },
                "nakit_oran": 48.00,
                "nakit_getiri_orani": 50.0,
                "viop_pozisyonlar": {"uzun": 1.5, "kisa": 0.5, "teminat": 8.0, "teminat_faiz": 50.0},
                "yonetim_ucreti": 2.8,
                "fon_gider": 0.5
            }
        return {}

class VeriSaglayici:
    def __init__(self, cache_yoneticisi):
        self.cache = cache_yoneticisi

    def veri_cek_retry(self, tickers):
        if not tickers:
            return []
        
        cache_anahtar = "_".join(sorted(tickers))
        onbellek_veri = self.cache.veri_al(cache_anahtar, 60)
        if onbellek_veri is not None:
            return onbellek_veri

        url = "https://scanner.tradingview.com/turkey/scan"
        payload = {
            "symbols": {"tickers": tickers},
            "columns": ["close", "change", "high", "low", "volume"]
        }
        
        try:
            data_bytes = json.dumps(payload).encode('utf-8')
        except (TypeError, ValueError) as e:
            print(f"{KIRMIZI}[JSON Payload Hatası] {e}{RESET}")
            return []
        
        maks_deneme = 3
        for deneme in range(maks_deneme):
            try:
                req = urllib.request.Request(
                    url, data=data_bytes,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Content-Type': 'application/json'}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    sonuc = res_json.get('data', [])
                    self.cache.veri_yaz(cache_anahtar, sonuc)
                    return sonuc
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
                if deneme == maks_deneme - 1:
                    print(f"{KIRMIZI}[Veri Çekme Kritik Hata] Tüm denemeler başarısız: {e}{RESET}")
                    return []
                time.sleep(2 ** deneme)
        return []

    def borsa_ve_hisseleri_cek(self, tum_hisseler):
        fiyat_verileri = {}
        bist_veri = {"puan": 0.0, "degisim": 0.0}
        
        benzersiz_hisseler = list(set([h.strip() for h in tum_hisseler if h]))
        tickers = [f"BIST:{hisse}" for hisse in benzersiz_hisseler]
        tickers.append("BIST:XU100")
        
        ham_veri = self.veri_cek_retry(tickers)
        for item in ham_veri:
            if not isinstance(item, dict):
                continue
            s_name = item.get('s', '').replace('BIST:', '')
            d = item.get('d', [0.0, 0.0, 0.0, 0.0, 0.0])
            
            try:
                fiyat = float(d[0]) if len(d) > 0 and d[0] is not None else 0.0
                degisim = float(d[1]) if len(d) > 1 and d[1] is not None else 0.0
                yuksek = float(d[2]) if len(d) > 2 and d[2] is not None else fiyat
                dusuk = float(d[3]) if len(d) > 3 and d[3] is not None else fiyat
            except (ValueError, TypeError):
                fiyat, degisim, yuksek, dusuk = 0.0, 0.0, 0.0, 0.0
            
            vol_item = abs((yuksek - dusuk) / fiyat * 100) if fiyat > 0 else 18.5
            
            if s_name == "XU100":
                bist_veri["puan"] = fiyat
                bist_veri["degisim"] = degisim
            else:
                fiyat_verileri[s_name] = {
                    "fiyat": fiyat, 
                    "degisim": degisim, 
                    "volatilite": max(vol_item, 10.0)
                }
                
        return bist_veri, fiyat_verileri

class RiskAnalizatoru:
    @staticmethod
    def metrikleri_hesapla(ham_getiri, portfoy_hisseleri_fiyatlari, dagilim):
        toplam_agirlik = sum(dagilim.values())
        dinamik_vol = 18.5
        
        if toplam_agirlik > 0:
            agirlikli_vol_toplami = 0.0
            for hisse, oran in dagilim.items():
                hisse_bilgi = portfoy_hisseleri_fiyatlari.get(hisse, {})
                vol = hisse_bilgi.get("volatilite", 18.5)
                agirlikli_vol_toplami += vol * (oran / toplam_agirlik)
            dinamik_vol = agirlikli_vol_toplami
        
        rf = 50.0 / 365.0
        payda = dinamik_vol / (365 ** 0.5)
        sharpe = (ham_getiri - rf) / payda if payda > 0 else 0.0
        sortino = sharpe * 1.25
        var_95 = -1.65 * (dinamik_vol / (252 ** 0.5))
        cvar_95 = var_95 * 1.35
        max_dd = -(dinamik_vol * 0.7)
        
        return {
            "sharpe": sharpe,
            "sortino": sortino,
            "var_95": var_95,
            "cvar_95": cvar_95,
            "max_drawdown": max_dd,
            "hesaplanan_vol": dinamik_vol
        }

class AnalizMotoru:
    def __init__(self):
        self.db = VeritabaniYoneticisi()
        self.portfoy_yoneticisi = PortfoyDinamikYoneticisi(self.db)
        self.cache = CacheYoneticisi()
        self.veri_saglayici = VeriSaglayici(self.cache)

    def raporla(self):
        print("\n" + "="*70)
        print(BEYAZ + f"=== YENİ RAPOR DÖNGÜSÜ [{datetime.now().strftime('%H:%M:%S')}] ===" + RESET)
        print("="*70)

        portfoyler = self.portfoy_yoneticisi.fon_portfoylerini_cek()
        
        tum_hisseler = set()
        for fon_bilgi in portfoyler.values():
            hisseler_dict = fon_bilgi.get("hisseler", {})
            for hisse in hisseler_dict.keys():
                if hisse:
                    tum_hisseler.add(hisse)
                
        bist, fiyatlar = self.veri_saglayici.borsa_ve_hisseleri_cek(list(tum_hisseler))
        bist_renk = YESIL if bist["degisim"] > 0 else (KIRMIZI if bist["degisim"] < 0 else RESET)
        
        print(f"📈 BIST 100 Endeks : {bist['puan']:,.2f} | Değişim: {bist_renk}%{bist['degisim']:>+5.2f}{RESET}")
        print("="*70)
        
        fon_ham_getiriler = {}
        
        for fon_adi, fon_bilgi in portfoyler.items():
            dagilim = fon_bilgi.get("hisseler", {})
            hedef_hisse_orani = fon_bilgi.get("hedef_hisse_orani", 50.0)
            nakit_oran = fon_bilgi.get("nakit_oran", 50.0)
            yillik_faiz = fon_bilgi.get("nakit_getiri_orani", 50.0)
            viop = fon_bilgi.get("viop_pozisyonlar", {})
            yonetim_ucreti = fon_bilgi.get("yonetim_ucreti", 2.5)
            fon_gider = fon_bilgi.get("fon_gider", 0.5)
            
            mevcut_hisse_toplami = sum(dagilim.values())
            
            gunluk_faiz = ((1.0 + (yillik_faiz / 100.0)) ** (1.0 / 365.0) - 1.0) * 100.0
            gunluk_nakit_getirisi = gunluk_faiz * (nakit_oran / 100.0)
            
            uzun_etki = viop.get("uzun", 0.0) * (bist["degisim"] / 100.0)
            kisa_etki = viop.get("kisa", 0.0) * (-bist["degisim"] / 100.0)
            teminat_faiz_orani = viop.get("teminat_faiz", 50.0)
            gunluk_teminat_faiz = ((1.0 + (teminat_faiz_orani / 100.0)) ** (1.0 / 365.0) - 1.0) * viop.get("teminat", 0.0)
            viop_net_etki = uzun_etki + kisa_etki + gunluk_teminat_faiz
            
            gunluk_kesinti = ((yonetim_ucreti + fon_gider) / 100.0) / 365.0 * 100.0
            
            hisse_getirisi_toplami = 0.0
            print(f"\n{SARI}🔹 {fon_adi} Fonu (Dinamik Hedef Hisse: %{hedef_hisse_orani}){RESET}")
            print("-" * 70)
            
            fon_fiyat_alt_kumesi = {}
            for hisse, oran in dagilim.items():
                if not hisse:
                    continue
                hisse_bilgi = fiyatlar.get(hisse, {"fiyat": 0.0, "degisim": 0.0, "volatilite": 18.5})
                fon_fiyat_alt_kumesi[hisse] = hisse_bilgi
                
                hisse_degisim = hisse_bilgi["degisim"]
                hisse_fiyat = hisse_bilgi["fiyat"]
                
                if mevcut_hisse_toplami > 0:
                    gercek_oran = oran * (hedef_hisse_orani / mevcut_hisse_toplami)
                else:
                    gercek_oran = oran
                    
                etki = hisse_degisim * (gercek_oran / 100.0)
                hisse_getirisi_toplami += etki
                
                renk = YESIL if hisse_degisim > 0 else (KIRMIZI if hisse_degisim < 0 else RESET)
                print(f"  • {hisse:<6} | NetOran: %{gercek_oran:<5.2f} | Fiyat: {hisse_fiyat:<7.2f} | Değ: {renk}%{hisse_degisim:>+5.2f}{RESET}")
                
            tahmini_nav = hisse_getirisi_toplami + gunluk_nakit_getirisi + viop_net_etki - gunluk_kesinti
            fon_ham_getiriler[fon_adi] = tahmini_nav
            
            self.db.kayit_ekle(fon_adi, tahmini_nav)
            
            risk = RiskAnalizatoru.metrikleri_hesapla(tahmini_nav, fon_fiyat_alt_kumesi, dagilim)
            
            print(f"  • {MAVI}{'LİKİT/REPO':<10}{RESET} : %{gunluk_nakit_getirisi:>+5.4f}")
            print(f"  • {MAVI}{'VİOP NET':<10}{RESET} : %{viop_net_etki:>+5.4f}")
            print(f"  • {KIRMIZI}{'GİDERLER':<10}{RESET} : -%{gunluk_kesinti:>5.4f}")
            print(f"  • {BEYAZ}{'RİSK (Sharpe/VaR)':<10}{RESET} : Sharpe: {risk['sharpe']:.2f} | Vol: %{risk['hesaplanan_vol']:.1f} | VaR(95): %{risk['var_95']:.2f}")

        print("\n" + "="*70)
        print(BEYAZ + "       v12 PRO GÜNCEL NAV TAHMİNLERİ VE OPTİMİZASYON ÖZETİ" + RESET)
        print("="*70)
        for fon_adi, getiri in fon_ham_getiriler.items():
            getiri_renk = YESIL if getiri > 0 else (KIRMIZI if getiri < 0 else RESET)
            print(f"👉 {fon_adi:<32} : {getiri_renk}%{getiri:>+5.2f}{RESET}")
        print("="*70)

if __name__ == "__main__":
    motor = AnalizMotoru()
    
    while True:
        try:
            motor.raporla()
            time.sleep(60)
        except KeyboardInterrupt:
            print(f"\n{KIRMIZI}[Bilgi] Program kullanıcı tarafından güvenle durduruldu.{RESET}")
            break
        except Exception as err:
            print(f"\n{KIRMIZI}[Kritik Çalışma Hatası] {err} - 5 saniye sonra sistem yeniden başlatılacak...{RESET}")
            time.sleep(5)
