import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser(description="Preemptive Priority Scheduling Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    args = parser.parse_args()

    input_path = args.input_file
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    output_filename = f"sonuc_preemptive_priority_{raw_name}.txt"

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

        # Öncelik Dönüştürme Fonksiyonu (High=1, Normal=2, Low=3)
        def map_priority(val):
            s = str(val).lower().strip()
            if s == 'high': return 1
            if s == 'normal': return 2
            if s == 'low': return 3
            # Eğer sayısal verilmişse olduğu gibi al
            try:
                return float(val)
            except:
                return 999 # Bilinmeyen değer en düşük öncelik olsun

        processes = []
        for idx, row in df.iterrows():
            processes.append({
                'id': row['Process_ID'],
                'arrival': float(row['Arrival_Time']),
                'burst': float(row[burst_col]),
                'remaining': float(row[burst_col]),
                'priority_val': map_priority(row['Priority']), # Sayısal öncelik değeri
                'completion': 0.0,
                'waiting': 0.0,
                'turnaround': 0.0
            })

        n = len(processes)
        CONTEXT_SWITCH = 0.001
        current_time = 0.0
        completed_count = 0
        
        timeline_data = [] # {start, id, end}
        last_process_id = None 
        
        # Simülasyon Döngüsü
        while completed_count < n:
            # Hazır ve bitmemiş işlemleri bul
            available_processes = [p for p in processes if p['arrival'] <= current_time and p['remaining'] > 0]
            
            if not available_processes:
                # IDLE durumu
                future_processes = [p for p in processes if p['arrival'] > current_time]
                if future_processes:
                    next_arrival = min(p['arrival'] for p in future_processes)
                    
                    # Merge IDLE
                    if timeline_data and timeline_data[-1]['id'] == 'IDLE' and abs(timeline_data[-1]['end'] - current_time) < 1e-9:
                         timeline_data[-1]['end'] = next_arrival
                    else:
                         timeline_data.append({'start': current_time, 'id': 'IDLE', 'end': next_arrival})
                    
                    current_time = next_arrival
                    last_process_id = None
                    continue
                else:
                    break

            # SEÇİM KRİTERİ: En düşük 'priority_val' (En yüksek öncelik)
            # Eşitlik durumunda Varış Zamanı (Arrival)
            highest_priority_process = min(available_processes, key=lambda x: (x['priority_val'], x['arrival']))
            
            # Bağlam Değiştirme Kontrolü
            if last_process_id != highest_priority_process['id']:
                start_cs = current_time
                end_cs = current_time + CONTEXT_SWITCH
                current_time = end_cs
                last_process_id = highest_priority_process['id']
            
            # Ne kadar çalışacak? (Bir sonraki olay anına kadar)
            future_arrivals = [p['arrival'] for p in processes if p['arrival'] > current_time]
            if future_arrivals:
                next_event_time = min(future_arrivals)
                time_slice = next_event_time - current_time
            else:
                time_slice = highest_priority_process['remaining']

            # İşlem bitişi olaydan önceyse
            run_time = min(time_slice, highest_priority_process['remaining'])
            
            # Tolerans kontrolü
            if run_time <= 1e-9:
                if highest_priority_process['remaining'] < 1e-9:
                     highest_priority_process['remaining'] = 0
                     completed_count += 1
                     highest_priority_process['completion'] = current_time
                     highest_priority_process['turnaround'] = highest_priority_process['completion'] - highest_priority_process['arrival']
                     highest_priority_process['waiting'] = highest_priority_process['turnaround'] - highest_priority_process['burst']
                if future_arrivals:
                     current_time = next_event_time
                continue

            start_exec = current_time
            end_exec = start_exec + run_time
            
            # Timeline Merge Mantığı
            if timeline_data and timeline_data[-1]['id'] == highest_priority_process['id'] and abs(timeline_data[-1]['end'] - start_exec) < 1e-9:
                timeline_data[-1]['end'] = end_exec
            else:
                timeline_data.append({'start': start_exec, 'id': highest_priority_process['id'], 'end': end_exec})
            
            # Güncelleme
            highest_priority_process['remaining'] -= run_time
            current_time = end_exec
            
            # Tamamlanma kontrolü
            if highest_priority_process['remaining'] <= 1e-9:
                highest_priority_process['remaining'] = 0
                completed_count += 1
                highest_priority_process['completion'] = current_time
                
                highest_priority_process['turnaround'] = highest_priority_process['completion'] - highest_priority_process['arrival']
                highest_priority_process['waiting'] = highest_priority_process['turnaround'] - highest_priority_process['burst']

        # Çıktı Hazırlama
        timeline_lines = []
        for item in timeline_data:
            line = f"[{item['start']:.4g}] -- {item['id']} -- [{item['end']:.4g}]"
            timeline_lines.append(line)

        avg_wait = sum(p['waiting'] for p in processes) / n
        max_wait = max(p['waiting'] for p in processes)
        
        avg_turnaround = sum(p['turnaround'] for p in processes) / n
        max_turnaround = max(p['turnaround'] for p in processes)
        
        completion_times = [p['completion'] for p in processes]
        check_points = [50, 100, 150, 200]
        throughput_results = {}
        for t in check_points:
            throughput_results[t] = sum(1 for c in completion_times if c <= t)
            
        total_burst = sum(p['burst'] for p in processes)
        cpu_efficiency = total_burst / current_time if current_time > 0 else 0
        total_context_switches = sum(1 for item in timeline_data if item['id'] != 'IDLE')

        # Dosyaya Yazma
        output_content = []
        output_content.append(f"Preemptive Priority Scheduling Sonuçları - {base_name}")
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
