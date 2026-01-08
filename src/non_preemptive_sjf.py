import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser(description="Non-Preemptive SJF Çizelgeleme Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    args = parser.parse_args()

    input_path = args.input_file
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    output_filename = f"sonuc_nonpreemptive_sjf_{raw_name}.txt"

    try:
        # 1. Veriyi Yükle
        df = pd.read_csv(input_path)
        df.columns = df.columns.str.strip()
        
        # Sütun eşleştirme
        if 'CPU_Burst_Time' in df.columns:
            burst_col = 'CPU_Burst_Time'
        elif 'Burst_Time' in df.columns:
            burst_col = 'Burst_Time'
        else:
            raise KeyError("Sütun hatası: 'CPU_Burst_Time' veya 'Burst_Time' bulunamadı.")
            
        if 'Arrival_Time' not in df.columns:
             raise KeyError("Sütun hatası: 'Arrival_Time' bulunamadı.")

        # İşlemleri sözlük listesi haline getir (Statü takibi için)
        processes = []
        for idx, row in df.iterrows():
            processes.append({
                'id': row['Process_ID'],
                'arrival': float(row['Arrival_Time']),
                'burst': float(row[burst_col]),
                'completed': False,
                'completion_time': 0.0,
                'turnaround': 0.0,
                'waiting': 0.0
            })

        # Toplam işlem sayısı
        n = len(processes)
        completed_count = 0
        current_time = 0.0
        CONTEXT_SWITCH = 0.001

        timeline_lines = []

        # 2. Simülasyon Döngüsü
        while completed_count < n:
            # Şu anki zamanda veya öncesinde gelmiş ve HENÜZ TAMAMLANMAMIŞ işlemleri bul
            available_processes = [p for p in processes if p['arrival'] <= current_time and not p['completed']]

            if not available_processes:
                # Eğer hazırda işlem yoksa, CPU boşta (IDLE) kalır.
                # Gelecek İLK işlemin varış zamanını bul.
                remaining_processes = [p for p in processes if not p['completed']]
                if remaining_processes:
                    # En yakın varış zamanı
                    next_arrival = min(p['arrival'] for p in remaining_processes)
                    
                    # Zaman tablosuna IDLE yaz
                    timeline_lines.append(f"[{current_time:.4g}] -- IDLE -- [{next_arrival:.4g}]")
                    
                    # Zamanı ilerlet
                    current_time = next_arrival
                    continue
                else:
                    break

            # Hazır işlemler arasından BURST süresi EN KISA olanı seç (SJF Mantığı)
            # Eşitlik durumunda Varış Zamanına (Arrival) bak (FCFS kuralı)
            shortest_process = min(available_processes, key=lambda x: (x['burst'], x['arrival']))

            # -- BAĞLAM DEĞİŞTİRME ve ÇALIŞTIRMA --
            # Non-Preemptive olduğu için işlem bir kere başlar ve bitene kadar sürer.
            
            start_exec = current_time + CONTEXT_SWITCH
            end_exec = start_exec + shortest_process['burst']
            
            # Zaman tablosuna ekle
            timeline_lines.append(f"[{start_exec:.4g}] -- {shortest_process['id']} -- [{end_exec:.4g}]")
            
            # Zamanı güncelle
            current_time = end_exec
            
            # İşlemi tamamlandı işaretle ve metrikleri hesapla
            shortest_process['completed'] = True
            completed_count += 1
            shortest_process['completion_time'] = end_exec
            
            # Turnaround = Completion - Arrival
            shortest_process['turnaround'] = shortest_process['completion_time'] - shortest_process['arrival']
            
            # Waiting = Turnaround - Burst
            shortest_process['waiting'] = shortest_process['turnaround'] - shortest_process['burst']

        # 3. İstatistiksel Hesaplamalar
        avg_wait = sum(p['waiting'] for p in processes) / n
        max_wait = max(p['waiting'] for p in processes)
        
        avg_turnaround = sum(p['turnaround'] for p in processes) / n
        max_turnaround = max(p['turnaround'] for p in processes)
        
        # Throughput
        completion_times = [p['completion_time'] for p in processes]
        check_points = [50, 100, 150, 200]
        throughput_results = {}
        for t in check_points:
            count = sum(1 for c in completion_times if c <= t)
            throughput_results[t] = count
            
        # CPU Verimliliği
        total_burst = sum(p['burst'] for p in processes)
        cpu_efficiency = total_burst / current_time if current_time > 0 else 0
        
        # Toplam Bağlam Değiştirme
        # Non-Preemptive'de her işlem tam olarak 1 kez çalışır.
        # Dolayısıyla toplam işlem sayısı kadar bağlam değiştirme yapılmıştır.
        total_context_switches = n

        # 4. Çıktıyı Dosyaya Yazma
        output_content = []
        output_content.append(f"Non-Preemptive SJF Sonuçları - {base_name}")
        output_content.append("-" * 40)
        
        output_content.append("a) Zaman Tablosu")
        output_content.extend(timeline_lines)
        output_content.append("")
        
        output_content.append("b) Maksimum ve Ortalama Bekleme Süresi [Waiting Time]")
        output_content.append(f"   Maksimum: {max_wait:.4f}")
        output_content.append(f"   Ortalama: {avg_wait:.4f}")
        output_content.append("")
        
        output_content.append("c) Maksimum ve Ortalama Tamamlanma Süresi [Turnaround Time]")
        output_content.append(f"   Maksimum: {max_turnaround:.4f}")
        output_content.append(f"   Ortalama: {avg_turnaround:.4f}")
        output_content.append("")
        
        output_content.append("d) T=[50, 100, 150, 200] için İş Tamamlama Sayısı [Throughput]")
        for t in check_points:
            output_content.append(f"   T={t}: {throughput_results[t]}")
        output_content.append("")
        
        output_content.append("e) Ortalama CPU Verimliliği")
        output_content.append(f"   {cpu_efficiency:.4%}")
        output_content.append("")
        
        output_content.append("f) Toplam Bağlam Değiştirme Sayısı")
        output_content.append(f"   {total_context_switches}")
        
        # Dosyayı Kaydet
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(output_content))
            
        print(f"İşlem Tamamlandı. Sonuçlar '{output_filename}' dosyasına yazıldı.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
