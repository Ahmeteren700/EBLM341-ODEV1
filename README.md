# EBLM341-Odev1

# İşletim Sistemleri - İşlemci Zamanlama

Bu proje, farklı CPU çizelgeleme (Scheduling) algoritmalarını simüle etmek ve performanslarını karşılaştırmak amacıyla Python dilinde geliştirilmiştir. Proje kapsamında FCFS, SJF (Preemptive/Non-Preemptive), Round Robin ve Priority (Preemptive/Non-Preemptive) algoritmaları test edilmiştir.

Proje aşağıdaki 6 algoritmayı içermektedir:
1.  **FCFS** (First-Come, First-Served)
2.  **SJF - Preemptive** (Shortest Job First / SRTF)
3.  **SJF - Non-Preemptive**
4.  **Round Robin** (Time Quantum ile)
5.  **Priority - Preemptive**
6.  **Priority - Non-Preemptive**

## 📂 Proje İçeriği

* `src/`: Algoritma kaynak kodları (`.py` dosyaları).
* `data/`: Test veri setleri (`case1.csv`, `case2.csv`).
* `outputs/`: Test veri setlerine göre kodların çıktıları (`.txt` dosyaları).
* `reports/`: Algoritma karşılaştırmaları ve analiz raporları (`CASE1_PROJE_RAPORU.pdf`, `CASE2_PROJE_RAPORU.pdf` dosyaları).
* `README.md`: Kullanım kılavuzu.

## ⚙️ Gereksinimler

Projenin çalışması için bilgisayarınızda **Python 3.x** ve **Pandas** kütüphanesinin yüklü olması gerekmektedir.

Gerekli kütüphaneyi yüklemek için terminalde şu komutu çalıştırın:

```bash
pip install pandas
```

## 🚀 Kullanım

Her algoritma ayrı bir Python betiği (`.py`) olarak hazırlanmıştır. Komut satırından (Terminal/CMD) çalıştırılırken veri seti argüman olarak verilmelidir.

Aşağıdaki komutları terminale yazarak algoritmaları çalıştırabilirsiniz:

### 1. FCFS (First-Come, First-Served)

```bash
python fcfs.py case1.csv
```

### 2. Preemptive SJF (Shortest Job First / SRTF)

```bash
python preemptive_sjf.py case1.csv
```

### 3. Non-Preemptive SJF

```bash
python non_preemptive_sjf.py case1.csv
```

### 4. Round Robin

Varsayılan Zaman Dilimi (Quantum) süresi **10**'dur.

**Standart Çalıştırma (q=10):**

```bash
python round_robin.py case1.csv
```

**Özel Quantum Değeri ile Çalıştırma (Örn: q=20):**

```bash
python round_robin.py case1.csv --quantum 20
```

### 5. Preemptive Priority Scheduling

```bash
python preemptive_priority.py case1.csv
```

### 6. Non-Preemptive Priority Scheduling

```bash
python non_preemptive_priority.py case1.csv
```

*(Not: `case1.csv` yerine `case2.csv` yazarak diğer veri setini test edebilirsiniz.)*

---

## 📄 Girdi Dosyası Formatı (CSV)

Kodların hatasız çalışması için kullanılacak CSV dosyalarının aşağıdaki sütun başlıklarına sahip olması gerekmektedir:

| Process_ID | Arrival_Time | CPU_Burst_Time | Priority |
| :--- | :--- | :--- | :--- |
| P001 | 0 | 4 | high |
| P002 | 2 | 7 | normal |

---

## 📊 Çıktılar

Her algoritma çalıştırıldığında, bulunduğu dizine `sonuc_[algoritma_adi]_[dosya_adi].txt` isminde bir metin dosyası oluşturur.

**Örnek Dosya Adı:** `sonuc_fcfs_case1.txt`

Bu sonuç dosyaları, ödevde istenen şu 6 metriği detaylı olarak içerir:

1.  **a) Zaman Tablosu:** Süreçlerin CPU üzerindeki çalışma aralıklarını gösteren liste (Gantt Şeması).
    * *Format:* `[Başlangıç] -- Process_ID -- [Bitiş]`
2.  **b) Bekleme Süresi (Waiting Time):** Maksimum ve Ortalama değerler.
3.  **c) Tamamlanma Süresi (Turnaround Time):** Maksimum ve Ortalama değerler.
4.  **d) İş Tamamlama Sayısı (Throughput):** T=50, 100, 150 ve 200 anlarında tamamlanan toplam işlem sayısı.
5.  **e) Ortalama CPU Verimliliği:** (Toplam Burst Süresi / Toplam Geçen Süre) oranı.
6.  **f) Toplam Bağlam Değiştirme (Context Switch) Sayısı.**

### Örnek Çıktı Görünümü:

```text
FCFS Sonuçları - case1.csv
----------------------------------------
a) Zaman Tablosu
[0] -- P001 -- [4]
[4] -- P002 -- [11]
[11] -- IDLE -- [12]
...

b) Maksimum ve Ortalama Bekleme Süresi [Waiting Time]
   Maksimum: 125.0000
   Ortalama: 45.2300

c) Maksimum ve Ortalama Tamamlanma Süresi [Turnaround Time]
   Maksimum: 135.0000
   Ortalama: 55.2300

d) T=[50, 100, 150, 200] için İş Tamamlama Sayısı [Throughput]
   T=50: 8
   T=100: 15
   T=150: 22
   T=200: 30

e) Ortalama CPU Verimliliği
   98.5000%

f) Toplam Bağlam Değiştirme Sayısı
   45
```

---

## 👤 Hazırlayan

**Ad Soyad:** Ahmet Eren Kavan
**Ders:** EBLM341 - İşletim Sistemleri
**Tarih:** Ocak 2026
