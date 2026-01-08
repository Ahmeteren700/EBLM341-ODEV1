import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser(description="Non-Preemptive Priority Scheduling Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    args = parser.parse_args()

    input_path = args.input_file
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    output_filename = f"sonuc_nonpreemptive_priority_{raw_name}.txt"

    try:
        # 1. Veriyi Yükle
        df = pd.read_csv(input_path)
        df.columns = df.columns.str.strip()
        
        # Sütun Kontrolleri
        if 'CPU_Burst_Time' in df.columns:
            burst_col = 'CPU_Burst_Time'
        elif 'Burst_Time' in df.columns:
            burst_col = 'Burst_Time'
        else:
            raise KeyError("Sütun hatası: 'CPU_Burst_Time' veya 'Burst_Time' bulunamadı.")
            
        if 'Arrival_Time' not in df.columns:
             raise KeyError("Sütun hatası: 'Arrival_Time' bulunamadı.")

        if 'Priority' not in df.columns:
             raise KeyError("Sütun hatası: 'Priority' bulunamadı.")

        # Öncelik Dönüştürme (High=1, Normal=2, Low=3)
        def map_priority(val):
            s = str(val).lower().strip()
            if s == 'high': return 1
            if s == 'normal': return 2
            if s == 'low': return 3
            try:
                return float(val)
            except:
                return 999 

        processes = []
        for idx, row in df.iterrows():
            processes.append({
                'id': row['Process_ID'],
                'arrival': float(row['Arrival_Time']),
                'burst': float(row[burst_col]),
                'priority_val': map_priority(row['Priority']),
                'completed': False,
                'completion_time': 0.0,
                'turnaround': 0.0,
                'waiting': 0.0
            })

        n = len(processes)
        completed_count = 0
        current_time = 0.0
        CONTEXT_SWITCH = 0.001

        timeline_lines = []

        # 2. Simülasyon Döngüsü
        while completed_count < n:
            # Hazır ve bitmemiş işlemleri bul
            available_processes = [p for p in processes if p['arrival'] <= current_time and not p['completed']]

            if not available_processes:
                # IDLE Durumu: Hazırda iş yoksa bir sonraki geliş zamanına atla
                remaining_processes = [p for p in processes if not p['completed']]
                if remaining_processes:
                    next_arrival = min(p['arrival'] for p in remaining_processes)
                    
                    timeline_lines.append(f"[{current_time:.4g}] -- IDLE -- [{next_arrival:.4g}]")
                    current_time = next_arrival
                    continue
                else:
                    break

            # SEÇİM KRİTERİ: En düşük priority_val (En yüksek öncelik)
            # Eşitlik durumunda Varış Zamanı (Arrival Time)
            selected_process = min(available_processes, key=lambda x: (x['priority_val'], x['arrival']))

            # -- BAĞLAM DEĞİŞTİRME ve ÇALIŞTIRMA --
            # Non-Preemptive olduğu için işlem bitene kadar çalışır.
            
            start_exec = current_time + CONTEXT_SWITCH
            end_exec = start_exec + selected_process['burst']
            
            # Zaman tablosuna ekle
            timeline_lines.append(f"[{start_exec:.4g}] -- {selected_process['id']} -- [{end_exec:.4g}]")
            
            # Zamanı güncelle
            current_time = end_exec
            
            # İşlemi bitir ve metrikleri hesapla
            selected_process['completed'] = True
            completed_count += 1
            selected_process['completion_time'] = end_exec
            
            selected_process['turnaround'] = selected_process['completion_time'] - selected_process['arrival']
            selected_process['waiting'] = selected_process['turnaround'] - selected_process['burst']

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
        # Her işlem tam bir blok halinde çalışır, yani N adet işlem için N adet CS vardır.
        total_context_switches = n

        # 4. Dosyaya Yazma
        output_content = []
        output_content.append(f"Non-Preemptive Priority Scheduling Sonuçları - {base_name}")
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
        
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(output_content))
            
        print(f"İşlem Tamamlandı. Sonuçlar '{output_filename}' dosyasına yazıldı.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
