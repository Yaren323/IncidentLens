# IncidentLens v3: Yerel makine öğrenmesi geliştirme paketi

## İçerik
- `data/tickets_labeled.csv`: 1900 **sentetik** ticket (16 BT kategorisi, 1 BT-dışı sınıf). Gerçek müşteri kayıtları değildir.
- `data/manual_challenge.csv`: 54 bağımsız yazılmış değerlendirme örneği.
- `scripts/train_model.py`: kapsam (BT / BT dışı) ve teknik kategori modellerini eğitir, test eder.
- `models/incidentlens_models.joblib`: önceden eğitilmiş model; **yalnızca güvenilir kaynaktan** yüklenmeli.
- `models/metrics.json`: ayrılmış sentetik doğrulama ve manuel challenge raporları.
- `app/services/classifier.py`: v2 ile aynı `predict()` sözleşmesi.
- `app/services/knowledge.py`: yedi yeni BT kategorisi için güvenli, salt-okunur ilk inceleme rehberleri.

## Kurulum (v2 çalışan klasörüne uygulama)
1. Mevcut proje klasörünün bir kopyasını al; `.env` dosyasını ve PostgreSQL volume'unu koru.
2. Bu paketten `data/`, `scripts/`, `models/`, `app/services/classifier.py`, `app/services/knowledge.py`, `Dockerfile` dosyalarını v2 projesine kopyala.
3. VS Code terminalinde proje kökünde `docker compose up --build -d` çalıştır. **`docker compose down -v` kullanma.**
4. `docker compose ps` ile `db` healthy ve `web` up durumunu kontrol et.
5. Web arayüzünde `VPN bağlantısı yaparken permission denied hatası aldım` metnini dene.

## Modeli yeniden eğitme (ücretsiz, Docker içinde)
`docker compose exec web python scripts/train_model.py`

**Not:** Bu komutun Docker içinde çalışabilmesi için Dockerfile'da `COPY data ./data` ve `COPY scripts ./scripts` satırları bulunmalıdır. Önceden eğitilmiş modeli kullanmak için yeniden eğitim gerekmez. Docker içinde eğitilen model konteynerin geçici dosya sisteminde kalır; kalıcı yapmak için yerelde eğitip yeniden build etmek daha güvenlidir.

Windows'ta Python ve bağımlılıklar kuruluysa proje kökünden `python scripts/train_model.py` çalıştır, ardından `docker compose up --build -d` yap.

## Önemli sınırlamalar
- Eğitim seti sentetik ve şablon türevidir; gerçek dünyadaki başarıyı temsil etmez.
- 54 manuel challenge örneği de küçük ve bağımsız denetim gerektirir.
- Model **olası BT kategorisini** tahmin eder, kök nedeni kanıtlamaz.
- `permission denied` ifadesi bağlama göre VPN, dosya, DB veya bulut yetkisi olabilir.
- BT dışı filtre bir güvenlik garantisi değildir; kullanıcı metninden hiçbir komut çalıştırılmaz.
- Yeni kategorilerin rehberleri başlangıç düzeyindedir; ayrıntılı üretim prosedürü değildir.
- Kullanıcı girdisine parola, token, kişisel veri veya gizli log eklemeyin.

## Kaynaklar
- Microsoft VPN troubleshooting: https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/troubleshoot-remote-access-vpn-and-aovpn-guidance
- Microsoft AOVPN: https://learn.microsoft.com/en-us/troubleshoot/windows-server/networking/troubleshoot-always-on-vpn
- scikit-learn data leakage: https://scikit-learn.org/stable/common_pitfalls.html
- scikit-learn grouped validation: https://scikit-learn.org/stable/modules/cross_validation.html
