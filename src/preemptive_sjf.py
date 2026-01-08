import argparse
import pandas as pd
import os
import sys

def main():
    parser = argparse.ArgumentParser(description="Preemptive SJF (SRTF) Çizelgeleme Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    args = parser.parse_args()

    input_path = args.input_file
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    output_filename = f"sonuc_preemptive_sjf_{raw_name}.txt"

    try:
        # 1. Veriyi Yükle
        df = pd.read_csv(input_path)
        df.columns = df.columns.str.strip()
        
        # Sütun Eşleştirme
        if 'CPU_Burst_Time' in df.columns:
            burst_col = 'CPU_Burst_Time'
        elif 'Burst_Time' in df.columns:
            burst_col = 'Burst_Time'
        else:
            raise KeyError("Sütun hatası: 'CPU_Burst_Time' veya 'Burst_Time' bulunamadı.")
            
        if 'Arrival_Time' not in df.columns:
             raise KeyError("Sütun hatası: 'Arrival_Time' bulunamadı.")

        processes = []
        for idx, row in df.iterrows():
            processes.append({
                'id': row['Process_ID'],
                'arrival': float(row['Arrival_Time']),
                'burst': float(row[burst_col]),
                'remaining': float(row[burst_col]),
                'completion': 0,
                'waiting': 0,
                'turnaround': 0
            })

        n = len(processes)
        CONTEXT_SWITCH = 0.001
        current_time = 0.0
        completed_count = 0
        
        # Ham zaman çizelgesi verilerini tutacak liste (String değil, veri olarak)
        # Yapı: {'start': 0.0, 'id': 'P001', 'end': 4.0}
        timeline_data = []
        
        last_process_id = None 
        
        # SİMÜLASYON DÖNGÜSÜ
        while completed_count < n:
            # Şu anki zamanda hazır olan ve bitmemiş işlemler
            available_processes = [p for p in processes if p['arrival'] <= current_time and p['remaining'] > 0]
            
            if not available_processes:
                # IDLE durumu: Gelecek ilk işlemi bul
                future_processes = [p for p in processes if p['arrival'] > current_time]
                if future_processes:
                    next_arrival = min(p['arrival'] for p in future_processes)
                    
                    # IDLE ekle (Merge mantığı: Önceki de IDLE ise birleştir)
                    if timeline_data and timeline_data[-1]['id'] == 'IDLE' and abs(timeline_data[-1]['end'] - current_time) < 1e-9:
                         timeline_data[-1]['end'] = next_arrival
                    else:
                         timeline_data.append({'start': current_time, 'id': 'IDLE', 'end': next_arrival})
                    
                    current_time = next_arrival
                    last_process_id = None
                    continue
                else:
                    break

            # En kısa kalana (SRTF) karar ver
            # Eşitlik durumunda Arrival Time'a bak (FCFS mantığıyla tie-break)
            shortest_process = min(available_processes, key=lambda x: (x['remaining'], x['arrival']))
            
            # Bağlam Değiştirme (Context Switch) Kontrolü
            # Eğer CPU'daki işlem değiştiyse
            if last_process_id != shortest_process['id']:
                start_cs = current_time
                end_cs = current_time + CONTEXT_SWITCH
                current_time = end_cs
                last_process_id = shortest_process['id']
            
            # Ne kadar süre çalışacak? (Bir sonraki olaya kadar)
            future_arrivals = [p['arrival'] for p in processes if p['arrival'] > current_time]
            if future_arrivals:
                next_event_time = min(future_arrivals)
                time_slice = next_event_time - current_time
            else:
                time_slice = shortest_process['remaining']

            # İşlem bitişi olaydan önceyse, sadece bitişe kadar çalışır
            run_time = min(time_slice, shortest_process['remaining'])
            
            # Eğer run_time çok çok küçükse (0'a yakınsa) döngüyü tıkamamak için atla
            if run_time <= 1e-9:
                # Bazen floating point hatasıyla remaining 0.000000001 kalabilir, onu bitir.
                if shortest_process['remaining'] < 1e-9:
                     shortest_process['remaining'] = 0
                     completed_count += 1
                     shortest_process['completion'] = current_time
                     shortest_process['turnaround'] = shortest_process['completion'] - shortest_process['arrival']
                     shortest_process['waiting'] = shortest_process['turnaround'] - shortest_process['burst']
                # Sonsuz döngüden kaçınmak için bir sonraki evente atla veya remaining kadar ilerlet
                if future_arrivals:
                     current_time = next_event_time
                continue

            start_exec = current_time
            end_exec = start_exec + run_time
            
            # --- MERGE (BİRLEŞTİRME) MANTIĞI ---
            # Eğer listedeki son işlem ile şu anki işlem aynıysa VE arada zaman farkı yoksa süresini uzat.
            if timeline_data and timeline_data[-1]['id'] == shortest_process['id'] and abs(timeline_data[-1]['end'] - start_exec) < 1e-9:
                timeline_data[-1]['end'] = end_exec
            else:
                timeline_data.append({'start': start_exec, 'id': shortest_process['id'], 'end': end_exec})
            
            # Verileri güncelle
            shortest_process['remaining'] -= run_time
            current_time = end_exec
            
            # İşlem Bitti mi?
            if shortest_process['remaining'] <= 1e-9: # Float toleransı
                shortest_process['remaining'] = 0
                completed_count += 1
                shortest_process['completion'] = current_time
                
                # Metrik hesapla
                shortest_process['turnaround'] = shortest_process['completion'] - shortest_process['arrival']
                shortest_process['waiting'] = shortest_process['turnaround'] - shortest_process['burst']

        # ÇIKTILARI OLUŞTURMA
        
        # 1. Timeline Stringlerini Oluştur
        timeline_lines = []
        for item in timeline_data:
            line = f"[{item['start']:.4g}] -- {item['id']} -- [{item['end']:.4g}]"
            timeline_lines.append(line)

        # 2. İstatistikler
        avg_wait = sum(p['waiting'] for p in processes) / n
        max_wait = max(p['waiting'] for p in processes)
        
        avg_turnaround = sum(p['turnaround'] for p in processes) / n
        max_turnaround = max(p['turnaround'] for p in processes)
        
        completed_times_list = [p['completion'] for p in processes]
        check_points = [50, 100, 150, 200]
        throughput_results = {}
        for t in check_points:
            throughput_results[t] = sum(1 for c in completed_times_list if c <= t)
            
        total_burst = sum(p['burst'] for p in processes)
        cpu_efficiency = total_burst / current_time if current_time > 0 else 0
        
        # Toplam Bağlam Değiştirme (IDLE olmayan her blok bir işlem koşusudur)
        # Ancak Merge yaptığımız için artık timeline'daki blok sayısı (IDLE hariç) yaklaşık CS sayısını verir.
        # İlk işlem için CS maliyeti ekledik mi? Kodda last_process_id None iken ekledik.
        # Bu yüzden timeline'daki her Pxxx bloğu bir CS sonucu oluşmuştur (veya başlangıçtır).
        total_context_switches = sum(1 for item in timeline_data if item['id'] != 'IDLE')

        # DOSYAYA YAZMA
        output_content = []
        output_content.append(f"Preemptive SJF Sonuçları - {base_name}")
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
            
        print(f"İşlem Tamamlandı. Temizlenmiş sonuçlar '{output_filename}' dosyasına yazıldı.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
