import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Настройка стиля графиков
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

# Константы
ALPHA = 4.28e-3  # температурный коэффициент сопротивления меди, град^-1
T_KELVIN_OFFSET = 273.15  # перевод в Кельвины

# Коэффициенты пересчёта сопротивления в температуру для установок
CALIB_COEFFS = {
    'setup1': {'a': 14.583955001619313455, 'b': 39.35514018691588785},
    'setup2': {'a': 14.377980252039598845, 'b': 39.35514018691588785}
}

# Масса образцов (кг) - примерные значения
MASS_CALORIMETER = 0.150  # масса пустого калориметра, кг
MASS_IRON = 0.100  # масса железного образца, кг
MASS_ALUMINUM = 0.100  # масса алюминиевого образца, кг

# Теоретические удельные теплоёмкости, Дж/(кг·К)
C_THEORETICAL = {
    'iron': 450,      # железо
    'aluminum': 902,   # алюминий
    'calorimeter': 385  # медь (калориметр)
}

# Мощность нагревателя (из данных - нужно уточнить)
P_HEATER = 5.0  # Вт


def parse_time_to_seconds(time_str):
    """Преобразует строку времени в секунды от начала"""
    try:
        # Убираем кавычки и пробелы
        time_str = time_str.strip().strip('"')
        # Парсим время
        t = datetime.strptime(time_str, '%H : %M : %S')
        return t.hour * 3600 + t.minute * 60 + t.second
    except:
        return 0


def load_data(filename):
    """Загружает данные из CSV файла"""
    data = []
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Пропускаем заголовок
    for line in lines[1:]:
        if line.strip() and ',' in line:
            parts = line.strip().split(',')
            if len(parts) >= 2:
                time_str = parts[0].strip()
                value_str = parts[1].strip()
                try:
                    time_sec = parse_time_to_seconds(time_str)
                    value = float(value_str)
                    data.append([time_sec, value])
                except:
                    continue
    return np.array(data)


def resistance_to_temperature(R, T_room, R_room, alpha=ALPHA):
    """
    Пересчёт сопротивления в температуру по формуле:
    T = 273 + (R / (alpha * R_room)) * (1 + alpha * (T_room - 273)) - 1/alpha
    """
    T_room_kelvin = T_room + T_KELVIN_OFFSET
    T = 273 + (R / (alpha * R_room)) * (1 + alpha * (T_room_kelvin - 273)) - 1/alpha
    return T - T_KELVIN_OFFSET  # возвращаем в градусах Цельсия


def smooth_data(y, window=5):
    """Сглаживание данных скользящим средним"""
    if len(y) < window:
        return y
    kernel = np.ones(window) / window
    y_smooth = np.convolve(y, kernel, mode='same')
    return y_smooth


def find_segments(time, temp, T_room, threshold=0.5):
    """
    Автоматически находит участки нагревания и охлаждения
    Возвращает словарь с сегментами
    """
    # Вычисляем производную
    dt = np.diff(time)
    dt = np.append(dt, dt[-1])
    dT = np.gradient(temp, time)
    
    # Сглаживаем производную
    dT_smooth = smooth_data(dT, window=10)
    
    # Находим участки
    heating_segments = []
    cooling_segments = []
    
    i = 0
    while i < len(dT_smooth) - 10:
        if dT_smooth[i] > threshold:
            # Начало нагревания
            start = i
            while i < len(dT_smooth) - 1 and dT_smooth[i] > 0:
                i += 1
            end = i
            if end - start > 50:  # Минимальная длина сегмента
                heating_segments.append((start, end))
        elif dT_smooth[i] < -threshold:
            # Начало охлаждения
            start = i
            while i < len(dT_smooth) - 1 and dT_smooth[i] < 0:
                i += 1
            end = i
            if end - start > 50:
                cooling_segments.append((start, end))
        else:
            i += 1
    
    return heating_segments, cooling_segments


def exponential_decay(t, T0, Tk, tau):
    """Экспоненциальная функция для охлаждения: T(t) = (T0 - Tk) * exp(-t/tau) + Tk"""
    return (T0 - Tk) * np.exp(-t / tau) + Tk


def exponential_growth(t, P_lambda, Tk, tau):
    """Экспоненциальная функция для нагревания: T(t) = P/λ * (1 - exp(-t/τ)) + Tk"""
    return P_lambda * (1 - np.exp(-t / tau)) + Tk


def process_experiment(data_resistance, data_room, start_idx, end_idx, T_room_avg):
    """Обрабатывает данные эксперимента"""
    if start_idx >= end_idx:
        return None, None, None
    
    time_exp = data_resistance[start_idx:end_idx, 0] - data_resistance[start_idx, 0]
    R_exp = data_resistance[start_idx:end_idx, 1]
    
    # Находим комнатную температуру в этот период
    time_room = data_room[:, 0]
    mask_room = (time_room >= data_resistance[start_idx, 0]) & (time_room <= data_resistance[end_idx-1, 0])
    if np.any(mask_room):
        T_room = np.mean(data_room[mask_room, 1])
    else:
        T_room = T_room_avg
    
    # Находим сопротивление при комнатной температуре (первые 30 точек)
    R_room = np.mean(R_exp[:min(30, len(R_exp))])
    
    # Пересчитываем сопротивление в температуру
    T_exp = resistance_to_temperature(R_exp, T_room, R_room)
    
    return time_exp, T_exp, T_room


def main():
    print("Загрузка данных...")
    
    # Загрузка данных
    data_calorimeter = load_data('калориметр.csv')
    data_room = load_data('комната.csv')
    
    if len(data_calorimeter) == 0 or len(data_room) == 0:
        print("Ошибка: не удалось загрузить данные. Проверьте файлы.")
        return
    
    print(f"Загружено {len(data_calorimeter)} точек для калориметра")
    print(f"Загружено {len(data_room)} точек для комнатной температуры")
    
    # Нормализуем время относительно начала записи
    start_record = data_calorimeter[0, 0]
    data_calorimeter[:, 0] -= start_record
    data_room[:, 0] -= start_record
    
    # Средняя комнатная температура за весь эксперимент
    T_room_avg = np.mean(data_room[:, 1])
    print(f"Средняя комнатная температура: {T_room_avg:.2f} °C")
    
    # Пересчитываем всё сопротивление в температуру
    T_all = np.zeros(len(data_calorimeter))
    for i in range(len(data_calorimeter)):
        T_all[i] = resistance_to_temperature(data_calorimeter[i, 1], T_room_avg, 
                                              data_calorimeter[0, 1])
    
    # Автоматически находим сегменты нагревания и охлаждения
    heating_segments, cooling_segments = find_segments(data_calorimeter[:, 0], T_all, T_room_avg)
    
    print(f"\nНайдено сегментов нагревания: {len(heating_segments)}")
    print(f"Найдено сегментов охлаждения: {len(cooling_segments)}")
    
    # Создаём графики
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # ==================== 1. Кривые нагревания и охлаждения ====================
    ax1 = axes[0, 0]
    
    colors = ['r', 'orange', 'green']
    labels = ['Пустой калориметр', 'С образцом Fe', 'С образцом Al']
    
    # Рисуем все найденные сегменты
    for i, (start, end) in enumerate(heating_segments[:3]):
        if start < end:
            time_seg = data_calorimeter[start:end, 0] - data_calorimeter[start, 0]
            T_seg = T_all[start:end]
            ax1.plot(time_seg, T_seg, colors[i % len(colors)], linewidth=1.5, 
                    label=f'Нагревание ({labels[i] if i < len(labels) else i})')
    
    for i, (start, end) in enumerate(cooling_segments[:3]):
        if start < end:
            time_seg = data_calorimeter[start:end, 0] - data_calorimeter[start, 0]
            T_seg = T_all[start:end]
            ax1.plot(time_seg, T_seg, 'b--' if i == 0 else 'c--', linewidth=1.5, 
                    label=f'Охлаждение ({labels[i] if i < len(labels) else i})')
    
    # Рисуем комнатную температуру
    ax1.axhline(y=T_room_avg, color='k', linestyle=':', alpha=0.7, 
                label=f'Tк = {T_room_avg:.1f}°C')
    
    ax1.set_xlabel('Время, с')
    ax1.set_ylabel('Температура, °C')
    ax1.set_title('Кривые нагревания и охлаждения')
    ax1.legend(loc='best', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # ==================== 2. Кривая охлаждения в спрямлённых координатах ====================
    ax2 = axes[0, 1]
    
    # Берём первый сегмент охлаждения
    if len(cooling_segments) > 0:
        start_cool, end_cool = cooling_segments[0]
        
        if start_cool < end_cool:
            time_cool = data_calorimeter[start_cool:end_cool, 0] - data_calorimeter[start_cool, 0]
            T_cool = T_all[start_cool:end_cool]
            
            # Убираем точки, где T_cool <= T_room_avg
            valid = T_cool > T_room_avg + 0.1
            time_cool = time_cool[valid]
            T_cool = T_cool[valid]
            
            if len(time_cool) > 10:
                # Вычисляем ln(T - Tk)
                y_ln = np.log(T_cool - T_room_avg)
                
                # Находим линейную область (после начального переходного процесса)
                start_idx = len(time_cool) // 5  # пропускаем первые 20%
                end_idx = len(time_cool)
                
                # Аппроксимация линейной области
                coeffs = np.polyfit(time_cool[start_idx:end_idx], y_ln[start_idx:end_idx], 1)
                slope, intercept = coeffs
                tau = -1 / slope if slope < 0 else 100  # постоянная времени τ = C/λ
                
                ax2.plot(time_cool, y_ln, 'b.', markersize=2, alpha=0.5, 
                        label='Экспериментальные данные')
                ax2.plot(time_cool[start_idx:end_idx], np.polyval(coeffs, time_cool[start_idx:end_idx]), 
                        'r-', linewidth=2, label=f'Линейная аппроксимация\ny = {slope:.4f}t + {intercept:.2f}')
                
                ax2.set_xlabel('Время, с')
                ax2.set_ylabel('ln(T - Tk)')
                ax2.set_title('Кривая охлаждения в спрямлённых координатах')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
                
                print(f"\nОхлаждение пустого калориметра:")
                print(f"  Наклон: {slope:.4f} с^-1")
                print(f"  Постоянная времени τ = C/λ = {tau:.1f} с")
    
    # ==================== 3. Кривые нагревания с аппроксимацией ====================
    ax3 = axes[1, 0]
    
    # Берём первый сегмент нагревания
    if len(heating_segments) > 0:
        start_heat, end_heat = heating_segments[0]
        
        if start_heat < end_heat:
            time_heat = data_calorimeter[start_heat:end_heat, 0] - data_calorimeter[start_heat, 0]
            T_heat = T_all[start_heat:end_heat]
            
            ax3.plot(time_heat, T_heat, 'b.', markersize=2, alpha=0.5, 
                    label='Эксперимент (пустой)')
            
            # Экспоненциальная аппроксимация
            try:
                # Находим параметры аппроксимации
                T0 = T_heat[0]
                T_inf = T_heat[-1]
                
                # Если tau уже определён из охлаждения
                if 'tau' in locals() and tau > 0:
                    def fit_func(t, P_lambda):
                        return exponential_growth(t, P_lambda, T_room_avg, tau)
                    
                    popt, _ = curve_fit(fit_func, time_heat, T_heat, p0=[T_inf - T_room_avg])
                    P_lambda = popt[0]
                    ax3.plot(time_heat, fit_func(time_heat, P_lambda), 'r-', linewidth=2,
                            label=f'Аппроксимация\nP/λ = {P_lambda:.2f}°C')
                    
                    print(f"\nНагревание пустого калориметра:")
                    print(f"  P/λ = {P_lambda:.2f} °C")
            except Exception as e:
                print(f"Ошибка аппроксимации: {e}")
    
    # Рисуем остальные сегменты нагревания
    for i, (start, end) in enumerate(heating_segments[1:3]):
        if start < end:
            time_heat = data_calorimeter[start:end, 0] - data_calorimeter[start, 0]
            T_heat = T_all[start:end]
            ax3.plot(time_heat, T_heat, 'g.' if i == 0 else 'orange', 
                    markersize=2, alpha=0.5, 
                    label='С образцом Fe' if i == 0 else 'С образцом Al')
    
    ax3.set_xlabel('Время, с')
    ax3.set_ylabel('Температура, °C')
    ax3.set_title('Кривые нагревания')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # ==================== 4. Производные кривых ====================
    ax4 = axes[1, 1]
    
    # Вычисляем производную для первого сегмента нагревания
    if len(heating_segments) > 0:
        start, end = heating_segments[0]
        if start < end:
            time_heat = data_calorimeter[start:end, 0] - data_calorimeter[start, 0]
            T_heat = T_all[start:end]
            
            dT_dt = np.gradient(T_heat, time_heat)
            dT_dt_smooth = smooth_data(dT_dt, window=10)
            
            ax4.plot(time_heat, dT_dt_smooth, 'b-', linewidth=1, 
                    label='dT/dt (нагревание, пустой)')
            
            # Находим точку, где T ≈ T_room_avg
            idx_Tk = np.argmin(np.abs(T_heat - T_room_avg))
            if 0 < idx_Tk < len(dT_dt_smooth):
                dT_at_Tk = dT_dt_smooth[idx_Tk]
                ax4.plot(time_heat[idx_Tk], dT_at_Tk, 'ro', markersize=8,
                        label=f'Точка T=Tk\ndT/dt = {dT_at_Tk:.3f}°C/с')
                
                # Расчёт теплоёмкости дифференциальным методом
                C_diff = P_HEATER / dT_at_Tk
                print(f"\nДифференциальный метод (формула 16):")
                print(f"  C = P/(dT/dt) = {P_HEATER:.1f} / {dT_at_Tk:.4f} = {C_diff:.1f} Дж/К")
    
    # Вычисляем производную для первого сегмента охлаждения
    if len(cooling_segments) > 0:
        start, end = cooling_segments[0]
        if start < end:
            time_cool = data_calorimeter[start:end, 0] - data_calorimeter[start, 0]
            T_cool = T_all[start:end]
            
            dT_dt_cool = np.gradient(T_cool, time_cool)
            dT_dt_cool_smooth = smooth_data(-dT_dt_cool, window=10)
            
            ax4.plot(time_cool, -dT_dt_cool_smooth, 'r-', linewidth=1, 
                    label='dT/dt (охлаждение, пустой)')
    
    ax4.set_xlabel('Время, с')
    ax4.set_ylabel('|dT/dt|, °C/с')
    ax4.set_title('Производные кривых нагревания и охлаждения')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lab_2_1_4_graphs.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    print("\n" + "="*60)
    print("Графики сохранены в файл lab_2_1_4_graphs.png")
    print("="*60)
    print("\nПРИМЕЧАНИЯ:")
    print("1. Мощность нагревателя (P = 5 Вт) является приблизительной")
    print("2. Для точных расчётов уточните P, массы образцов и R_273")
    print("3. Температурный коэффициент α = 4.28·10⁻³ град⁻¹")
    print("="*60)


if __name__ == "__main__":
    main()