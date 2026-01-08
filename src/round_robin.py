import argparse
import pandas as pd
import os
from collections import deque

def main():
    parser = argparse.ArgumentParser(description="Round Robin (RR) Çizelgeleme Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    # Varsayılan Quantum süresini 10 olarak belirledik, isterseniz çalıştırırken değiştirebilirsiniz.
    parser.add_argument('--quantum', type=int, default=10, help='Zaman Dilimi (Quantum) süresi (Varsayılan: 10)')
    
    args = parser.parse_args()

    input_path = args.input_file
    quantum = args.quantum
    
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    output_filename = f"sonuc_roundrobin_{raw_name}.txt"

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

        # İşlemleri listeye al
        # Round Robin'de kuyruk yapısı (Queue) çok önemlidir.
        processes = []
        for idx, row in df.iterrows():
            processes.append({
                'id': row['Process_ID'],
                'arrival': float(row['Arrival_Time']),
                'burst': float(row[burst_col]),
                'remaining': float(row[burst_col]),
                'completion': 0.0,
                'waiting': 0.0,
                'turnaround': 0.0,
                'first_start': -1 # İlk başlama zamanı (opsiyonel analiz için)
            })

        # Varış zamanına göre sırala (İlk ekleme sırası için önemli)
        processes.sort(key=lambda x: x['arrival'])

        # Hazır Kuyruğu (Ready Queue)
        queue = deque()
        
        # Hangi işlemlerin kuyruğa eklendiğini takip etmek için indeks
        added_indices = [False] * len(processes)
        
        current_time = 0.0
        completed_count = 0
        n = len(processes)
        CONTEXT_SWITCH = 0.001
        
        timeline_data = [] # {start, id, end}
        last_process_id = None

        # İlk anda (t=0) gelmiş olanları kuyruğa ekle
        # Not: Genellikle t=0'da başlanır ama ilk işlemin arrival'ı > 0 olabilir.
        
        # Simülasyon Döngüsü
        while completed_count < n:
            # 1. Henüz kuyruğa girmemiş ama şu anki zamana kadar gelmiş işlemleri kuyruğa ekle
            # DİKKAT: Round Robin'de yeni gelenler, o an süresi bitip arkaya geçen işlemden ÖNCE sıraya girer mi?
            # Genellikle: Süresi biten işlem en arkaya atılır. Yeni gelenler de arkaya eklenir.
            # Ancak "Context Switch" süresince geçen zamanda yeni gelenler olabilir.
            
            # Öncelikle, eğer kuyruk boşsa ve işlenmemiş süreçler varsa zamanı ileri sar
            if not queue:
                # Henüz eklenmemişlerin en küçüğünü bul
                remaining_indices = [i for i, x in enumerate(added_indices) if not x]
                if remaining_indices:
                    next_arrival_idx = remaining_indices[0] # Sorted olduğu için ilki en yakındır
                    next_arrival_time = processes[next_arrival_idx]['arrival']
                    
                    if next_arrival_time > current_time:
                         # IDLE ekle
                         if timeline_data and timeline_data[-1]['id'] == 'IDLE':
                             timeline_data[-1]['end'] = next_arrival_time
                         else:
                             timeline_data.append({'start': current_time, 'id': 'IDLE', 'end': next_arrival_time})
                         
                         current_time = next_arrival_time
                         last_process_id = None # IDLE sonrası CS gerekir
                else:
                    break # Hepsi bitti
            
            # Şimdi varış zamanı gelmiş olanları kuyruğa ekle
            for i in range(n):
                if not added_indices[i] and processes[i]['arrival'] <= current_time:
                    queue.append(processes[i])
                    added_indices[i] = True
            
            if not queue:
                continue

            # Kuyruktan sıradaki işlemi al
            current_process = queue.popleft()
            
            # Bağlam Değiştirme (Eğer işlem değiştiyse)
            if last_process_id != current_process['id']:
                current_time += CONTEXT_SWITCH
                last_process_id = current_process['id']
            
            # Ne kadar çalışacak? (Quantum vs Kalan Süre)
            run_time = min(quantum, current_process['remaining'])
            
            start_exec = current_time
            end_exec = start_exec + run_time
            
            # Timeline Ekleme (Merge Mantığıyla)
            if timeline_data and timeline_data[-1]['id'] == current_process['id'] and abs(timeline_data[-1]['end'] - start_exec) < 1e-9:
                timeline_data[-1]['end'] = end_exec
            else:
                timeline_data.append({'start': start_exec, 'id': current_process['id'], 'end': end_exec})
            
            # Verileri güncelle
            current_process['remaining'] -= run_time
            current_time = end_exec
            
            # -- KRİTİK NOKTA --
            # İşlem çalışırken (run_time süresince) yeni işlemler gelmiş olabilir.
            # İşlemi kuyruğa geri atmadan önce YENİ GELENLERİ kuyruğa almalıyız.
            for i in range(n):
                if not added_indices[i] and processes[i]['arrival'] <= current_time:
                    queue.append(processes[i])
                    added_indices[i] = True
            
            # İşlem bitti mi?
            if current_process['remaining'] <= 1e-9:
                current_process['remaining'] = 0
                completed_count += 1
                current_process['completion'] = current_time
                
                current_process['turnaround'] = current_process['completion'] - current_process['arrival']
                current_process['waiting'] = current_process['turnaround'] - current_process['burst']
            else:
                # Bitmediyse kuyruğun sonuna geri ekle
                queue.append(current_process)

        # -- ÇIKTI OLUŞTURMA --
        
        # 1. Timeline Stringleri
        timeline_lines = []
        for item in timeline_data:
            line = f"[{item['start']:.4g}] -- {item['id']} -- [{item['end']:.4g}]"
            timeline_lines.append(line)

        # 2. İstatistikler
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
        
        # Toplam Bağlam Değiştirme (Timeline'daki işlem blok sayısı)
        # IDLE olmayan blokları say
        total_context_switches = sum(1 for item in timeline_data if item['id'] != 'IDLE')

        # Dosyaya Yazma
        output_content = []
        output_content.append(f"Round Robin (Quantum={quantum}) Sonuçları - {base_name}")
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
