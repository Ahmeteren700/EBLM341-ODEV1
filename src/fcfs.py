import argparse
import pandas as pd
import os

def main():
    parser = argparse.ArgumentParser(description="FCFS Çizelgeleme Algoritması")
    parser.add_argument('input_file', type=str, help='İşlenecek CSV dosyasının yolu')
    args = parser.parse_args()

    input_path = args.input_file
    base_name = os.path.basename(input_path)
    raw_name = os.path.splitext(base_name)[0]
    
    # Çıktı dosya ismi formatı: sonuc_fcfs_case1.txt
    output_filename = f"sonuc_fcfs_{raw_name}.txt"

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

        # Sıralama (FCFS için Varış Zamanına göre)
        df = df.sort_values(by='Arrival_Time')

        # 2. Değişkenler
        CONTEXT_SWITCH = 0.001
        current_time = 0.0
        
        # İstatistik listeleri
        turnaround_times = []
        waiting_times = []
        completed_processes = [] # (Bitiş zamanlarını tutar)

        # Zaman tablosu satırları
        timeline_lines = []

        # 3. Simülasyon
        for index, row in df.iterrows():
            p_id = row['Process_ID']
            arrival = row['Arrival_Time']
            burst = row[burst_col]
            
            # -- IDLE DURUMU --
            if current_time < arrival:
                # Format: [ Başlangıç ] -- IDLE -- [ Bitiş ]
                line = f"[{current_time:.4g}] -- IDLE -- [{arrival:.4g}]"
                timeline_lines.append(line)
                current_time = arrival
            
            # -- BAĞLAM DEĞİŞTİRME ve İŞLEM --
            start_exec = current_time + CONTEXT_SWITCH
            end_exec = start_exec + burst
            
            # Format: [ Başlangıç ] -- Pxxx -- [ Bitiş ]
            line = f"[{start_exec:.4g}] -- {p_id} -- [{end_exec:.4g}]"
            timeline_lines.append(line)
            
            # Süre güncelle
            current_time = end_exec
            
            # Metrikler
            turnaround = end_exec - arrival
            waiting = turnaround - burst
            
            turnaround_times.append(turnaround)
            waiting_times.append(waiting)
            completed_processes.append(end_exec)

        # 4. Hesaplamalar
        avg_wait = sum(waiting_times) / len(waiting_times)
        max_wait = max(waiting_times)
        
        avg_turnaround = sum(turnaround_times) / len(turnaround_times)
        max_turnaround = max(turnaround_times)
        
        # Throughput
        check_points = [50, 100, 150, 200]
        throughput_results = {}
        for t in check_points:
            count = sum(1 for end_time in completed_processes if end_time <= t)
            throughput_results[t] = count

        # CPU Verimliliği
        total_burst = df[burst_col].sum()
        cpu_efficiency = total_burst / current_time if current_time > 0 else 0
        total_context_switches = len(df)

        # 5. Çıktı Oluşturma
        output_content = []
        output_content.append(f"FCFS Sonuçları - {base_name}")
        output_content.append("-" * 40)
        
        # a) Zaman Tablosu
        output_content.append("a) Zaman Tablosu")
        output_content.extend(timeline_lines) 
        output_content.append("")
        
        # b) Bekleme Süresi
        output_content.append("b) Maksimum ve Ortalama Bekleme Süresi [Waiting Time]")
        output_content.append(f"   Maksimum: {max_wait:.4f}")
        output_content.append(f"   Ortalama: {avg_wait:.4f}")
        output_content.append("")
        
        # c) Tamamlanma Süresi
        output_content.append("c) Maksimum ve Ortalama Tamamlanma Süresi [Turnaround Time]")
        output_content.append(f"   Maksimum: {max_turnaround:.4f}")
        output_content.append(f"   Ortalama: {avg_turnaround:.4f}")
        output_content.append("")
        
        # d) Throughput
        output_content.append("d) T=[50, 100, 150, 200] için İş Tamamlama Sayısı [Throughput]")
        for t in check_points:
            output_content.append(f"   T={t}: {throughput_results[t]}")
        output_content.append("")
        
        # e) CPU Verimliliği
        output_content.append("e) Ortalama CPU Verimliliği")
        output_content.append(f"   {cpu_efficiency:.4%}")
        output_content.append("")

        # f) Bağlam Değiştirme
        output_content.append("f) Toplam Bağlam Değiştirme Sayısı")
        output_content.append(f"   {total_context_switches}")
        
        # Dosyaya Yazma
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(output_content))
            
        print(f"İşlem Tamamlandı. Sonuçlar '{output_filename}' dosyasına yazıldı.")

    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()
