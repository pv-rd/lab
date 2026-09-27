import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import pandas as pd
from datetime import datetime

# Настройка стиля графиков
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

# Константы
ALPHA = 4.28e-3  # температурный коэффициент сопротивления меди, град^-1
T_KELVIN_OFFSET = 273.15  # перевод в Кельвины
R_273 = None  # будет вычислено из данных

# Коэффициенты пересчёта сопротивления в температуру для установок
# T(R) = a * R + b
CALIB_COEFFS = {
    'setup1': {'a': 14.583955001619313455, 'b': 39.35514018691588785},
    'setup2': {'a': 14.377980252039598845, 'b': 39.35514018691588785}
}

# Масса образцов (кг) - примерные значения, уточнить по лабораторной установке
MASS_CALORIMETER = 0.150  # масса пустого калориметра, кг
MASS_IRON = 0.100  # масса железного образца, кг
MASS_ALUMINUM = 0.100  # масса алюминиевого образца, кг

# Теоретические удельные теплоёмкости, Дж/(кг·К)
C_THEORETICAL = {
    'iron': 450,      # железо
    'aluminum': 902,   # алюминий
    'calorimeter': 385  # медь (калориметр)
}


def parse_time_to_seconds(time_str):
    """Преобразует строку времени в секунды от начала"""
    try:
        t = datetime.strptime(time_str.strip('"'), '%H : %M : %S')
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


def smooth_data(x, y, window=5):
    """Сглаживание данных скользящим средним"""
    if len(y) < window:
        return y
    kernel = np.ones(window) / window
    y_smooth = np.convolve(y, kernel, mode='same')
    return y_smooth


def exponential_decay(t, T0, Tk, tau):
    """Экспоненциальная функция для охлаждения: T(t) = (T0 - Tk) * exp(-t/tau) + Tk"""
    return (T0 - Tk) * np.exp(-t / tau) + Tk


def exponential_growth(t, P_lambda, Tk, tau):
    """Экспоненциальная функция для нагревания: T(t) = P/λ * (1 - exp(-t/τ)) + Tk"""
    return P_lambda * (1 - np.exp(-t / tau)) + Tk


def find_cooling_linear_region(T_cool, Tk, time, threshold=0.8):
    """
    Находит линейную область на графике ln(T - Tk) от времени
    Возвращает индексы начала и конца линейной области
    """
    y = np.log(T_cool - Tk)
    # Производная
    dy = np.gradient(y, time)
    # Находим область, где производная стабильна
    dy_smooth = smooth_data(time, dy, window=10)
    # Ищем область, где производная меняется не более чем на 10%
    dy_mean = np.mean(dy_smooth[50:])  # пропускаем начало
    mask = np.abs(dy_smooth - dy_mean) / dy_mean < 0.1
    
    # Находим непрерывную область
    indices = np.where(mask)[0]
    if len(indices) > 0:
        start_idx = indices[0]
        end_idx = indices[-1]
        return start_idx, end_idx
    return len(time) // 4, len(time) // 2


def process_experiment(data_resistance, data_room, start_time, end_time, experiment_type, T_room_avg):
    """
    Обрабатывает данные эксперимента (нагревание или охлаждение)
    """
    # Фильтруем данные по времени
    mask = (data_resistance[:, 0] >= start_time) & (data_resistance[:, 0] <= end_time)
    time_exp = data_resistance[mask, 0] - start_time
    R_exp = data_resistance[mask, 1]
    
    # Находим комнатную температуру в этот период
    mask_room = (data_room[:, 0] >= start_time) & (data_room[:, 0] <= end_time)
    T_room_values = data_room[mask_room, 1]
    T_room = np.mean(T_room_values) if len(T_room_values) > 0 else T_room_avg
    
    # Находим сопротивление при комнатной температуре
    R_room = np.mean(R_exp[:min(20, len(R_exp))])
    
    # Пересчитываем сопротивление в температуру
    T_exp = resistance_to_temperature(R_exp, T_room, R_room)
    
    return time_exp, T_exp, T_room


def main():
    print("Загрузка данных...")
    
    # Загрузка данных
    data_calorimeter = load_data('калориметр.csv')
    data_room = load_data('комната.csv')
    
    # Считываем временные метки событий
    events = {}
    with open('time.txt', 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                if len(parts) >= 2:
                    time_str = parts[0]
                    event = ' '.join(parts[1:])
                    time_parts = time_str.split(':')
                    time_sec = int(time_parts[0]) * 3600 + int(time_parts[1]) * 60
                    events[event] = time_sec
    
    # Находим время начала записи (первое измерение)
    start_record = data_calorimeter[0, 0]
    data_calorimeter[:, 0] -= start_record
    data_room[:, 0] -= start_record
    
    # Корректируем времена событий
    for key in events:
        events[key] -= start_record
    
    # Средняя комнатная температура за весь эксперимент
    T_room_avg = np.mean(data_room[:, 1])
    print(f"Средняя комнатная температура: {T_room_avg:.2f} °C")
    
    # Создаём графики
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # ==================== 1. Кривые нагревания и охлаждения ====================
    ax1 = axes[0, 0]
    
    # Пустой калориметр
    heat_start = events.get('включение нагревателя без образца', 0)
    heat_end = events.get('выключение', 0)
    cool_end = events.get('охлаждение', 0) + 1200  # ~20 минут охлаждения
    
    if heat_start > 0 and heat_end > 0:
        time_heat, T_heat, _ = process_experiment(data_calorimeter, data_room, 
                                                   heat_start, heat_end, 'heat', T_room_avg)
        ax1.plot(time_heat, T_heat, 'r-', linewidth=1.5, label='Нагревание (пустой)')
        
        time_cool, T_cool, _ = process_experiment(data_calorimeter, data_room,
                                                   heat_end, cool_end, 'cool', T_room_avg)
        ax1.plot(time_cool, T_cool, 'b-', linewidth=1.5, label='Охлаждение (пустой)')
    
    # Образец железа
    iron_start = events.get('включение с образцом железа', 0)
    iron_end = events.get('выключение', 0)
    
    # Нужно найти второе выключение
    iron_end = max([v for k, v in events.items() if 'выключение' in k][1:] + [0])
    
    if iron_start > 0 and iron_end > 0:
        time_iron_heat, T_iron_heat, _ = process_experiment(data_calorimeter, data_room,
                                                             iron_start, iron_end, 'heat', T_room_avg)
        ax1.plot(time_iron_heat, T_iron_heat, 'orange', linewidth=1.5, label='Нагревание (Fe)')
        
        iron_cool_end = events.get('охлаждение', iron_end + 1200)
        time_iron_cool, T_iron_cool, _ = process_experiment(data_calorimeter, data_room,
                                                             iron_end, iron_cool_end, 'cool', T_room_avg)
        ax1.plot(time_iron_cool, T_iron_cool, 'cyan', linewidth=1.5, label='Охлаждение (Fe)')
    
    # Образец алюминия
    al_start = events.get('включение с образцом алюминия', 0)
    al_end = events.get('выключение', 0)
    al_end = max([v for k, v in events.items() if 'выключение' in k][-1:] + [0])
    
    if al_start > 0 and al_end > 0:
        time_al_heat, T_al_heat, _ = process_experiment(data_calorimeter, data_room,
                                                         al_start, al_end, 'heat', T_room_avg)
        ax1.plot(time_al_heat, T_al_heat, 'green', linewidth=1.5, label='Нагревание (Al)')
    
    # Комнатная температура
    time_room = data_room[:, 0]
    T_room = data_room[:, 1]
    ax1.plot(time_room, T_room, 'k--', linewidth=1, alpha=0.7, label='Комнатная температура')
    
    ax1.axhline(y=T_room_avg, color='k', linestyle=':', alpha=0.5, label=f'Tк = {T_room_avg:.1f}°C')
    ax1.set_xlabel('Время, с')
    ax1.set_ylabel('Температура, °C')
    ax1.set_title('Кривые нагревания и охлаждения')
    ax1.legend(loc='best', fontsize=8)
    ax1.grid(True, alpha=0.3)
    
    # ==================== 2. Кривая охлаждения в спрямлённых координатах ====================
    ax2 = axes[0, 1]
    
    # Находим данные для охлаждения пустого калориметра
    cool_start = events.get('выключение', 0)
    cool_end = events.get('охлаждение', cool_start + 1800)
    
    mask_cool = (data_calorimeter[:, 0] >= cool_start) & (data_calorimeter[:, 0] <= cool_end)
    time_cool_all = data_calorimeter[mask_cool, 0] - cool_start
    R_cool = data_calorimeter[mask_cool, 1]
    
    # Находим комнатную температуру для этого периода
    mask_room_cool = (data_room[:, 0] >= cool_start) & (data_room[:, 0] <= cool_end)
    Tk_cool = np.mean(data_room[mask_room_cool, 1]) if len(data_room[mask_room_cool]) > 0 else T_room_avg
    R_room_cool = np.mean(R_cool[:min(30, len(R_cool))])
    
    T_cool_all = resistance_to_temperature(R_cool, Tk_cool, R_room_cool)
    
    # Вычисляем ln(T - Tk)
    y_ln = np.log(T_cool_all - Tk_cool)
    x_ln = time_cool_all
    
    # Находим линейную область
    start_idx, end_idx = find_cooling_linear_region(T_cool_all, Tk_cool, time_cool_all)
    
    # Аппроксимация линейной области
    coeffs = np.polyfit(x_ln[start_idx:end_idx], y_ln[start_idx:end_idx], 1)
    slope, intercept = coeffs
    tau = -1 / slope  # постоянная времени τ = C/λ
    
    ax2.plot(x_ln, y_ln, 'b.', markersize=2, alpha=0.5, label='Экспериментальные данные')
    ax2.plot(x_ln[start_idx:end_idx], np.polyval(coeffs, x_ln[start_idx:end_idx]), 
             'r-', linewidth=2, label=f'Линейная аппроксимация\ny = {slope:.4f}t + {intercept:.2f}')
    ax2.axhline(y=np.log(0.5), color='k', linestyle='--', alpha=0.5, label='Уровень 1/2')
    
    ax2.set_xlabel('Время, с')
    ax2.set_ylabel('ln(T - Tk)')
    ax2.set_title('Кривая охлаждения в спрямлённых координатах')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    print(f"\nОхлаждение пустого калориметра:")
    print(f"  Наклон: {slope:.4f} с^-1")
    print(f"  Постоянная времени τ = C/λ = {tau:.1f} с")
    
    # ==================== 3. Аппроксимация кривых нагревания ====================
    ax3 = axes[1, 0]
    
    # Пустой калориметр - нагревание
    if heat_start > 0 and heat_end > 0:
        mask_heat = (data_calorimeter[:, 0] >= heat_start) & (data_calorimeter[:, 0] <= heat_end)
        time_heat_all = data_calorimeter[mask_heat, 0] - heat_start
        R_heat = data_calorimeter[mask_heat, 1]
        
        mask_room_heat = (data_room[:, 0] >= heat_start) & (data_room[:, 0] <= heat_end)
        Tk_heat = np.mean(data_room[mask_room_heat, 1]) if len(data_room[mask_room_heat]) > 0 else T_room_avg
        R_room_heat = np.mean(R_heat[:min(30, len(R_heat))])
        
        T_heat_all = resistance_to_temperature(R_heat, Tk_heat, R_room_heat)
        
        # Аппроксимация экспоненциальным ростом
        # T(t) = P/λ * (1 - exp(-t/τ)) + Tk
        # где τ = C/λ из кривой охлаждения
        T0 = T_heat_all[0]
        T_inf = T_heat_all[-1]
        
        try:
            # Фиксируем τ из кривой охлаждения
            popt, _ = curve_fit(lambda t, P_lambda: exponential_growth(t, P_lambda, Tk_heat, tau),
                                time_heat_all, T_heat_all, p0=[T_inf - Tk_heat])
            P_lambda = popt[0]
            lambda_ = None  # будет вычислено позже
            
            ax3.plot(time_heat_all, T_heat_all, 'b.', markersize=2, alpha=0.5, label='Эксперимент (пустой)')
            ax3.plot(time_heat_all, exponential_growth(time_heat_all, P_lambda, Tk_heat, tau),
                    'r-', linewidth=2, label=f'Аппроксимация\nP/λ = {P_lambda:.2f}°C')
            
            print(f"\nНагревание пустого калориметра:")
            print(f"  P/λ = {P_lambda:.2f} °C")
            
        except Exception as e:
            print(f"Ошибка аппроксимации: {e}")
            ax3.plot(time_heat_all, T_heat_all, 'b-', linewidth=1, label='Эксперимент (пустой)')
    
    # Образец железа
    if iron_start > 0 and iron_end > 0:
        mask_iron = (data_calorimeter[:, 0] >= iron_start) & (data_calorimeter[:, 0] <= iron_end)
        time_iron_all = data_calorimeter[mask_iron, 0] - iron_start
        R_iron = data_calorimeter[mask_iron, 1]
        
        mask_room_iron = (data_room[:, 0] >= iron_start) & (data_room[:, 0] <= iron_end)
        Tk_iron = np.mean(data_room[mask_room_iron, 1]) if len(data_room[mask_room_iron]) > 0 else T_room_avg
        R_room_iron = np.mean(R_iron[:min(30, len(R_iron))])
        
        T_iron_all = resistance_to_temperature(R_iron, Tk_iron, R_room_iron)
        ax3.plot(time_iron_all, T_iron_all, 'g.', markersize=2, alpha=0.5, label='Эксперимент (Fe)')
    
    # Образец алюминия
    if al_start > 0 and al_end > 0:
        mask_al = (data_calorimeter[:, 0] >= al_start) & (data_calorimeter[:, 0] <= al_end)
        time_al_all = data_calorimeter[mask_al, 0] - al_start
        R_al = data_calorimeter[mask_al, 1]
        
        mask_room_al = (data_room[:, 0] >= al_start) & (data_room[:, 0] <= al_end)
        Tk_al = np.mean(data_room[mask_room_al, 1]) if len(data_room[mask_room_al]) > 0 else T_room_avg
        R_room_al = np.mean(R_al[:min(30, len(R_al))])
        
        T_al_all = resistance_to_temperature(R_al, Tk_al, R_room_al)
        ax3.plot(time_al_all, T_al_all, 'orange', markersize=2, alpha=0.5, label='Эксперимент (Al)')
    
    ax3.set_xlabel('Время, с')
    ax3.set_ylabel('Температура, °C')
    ax3.set_title('Кривые нагревания с экспоненциальной аппроксимацией')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # ==================== 4. Производные кривых (дифференциальный метод) ====================
    ax4 = axes[1, 1]
    
    # Вычисляем производные для пустого калориметра
    if heat_start > 0 and heat_end > 0:
        dT_dt_heat = np.gradient(T_heat_all, time_heat_all)
        dT_dt_smooth = smooth_data(time_heat_all, dT_dt_heat, window=10)
        
        ax4.plot(time_heat_all, dT_dt_smooth, 'b-', linewidth=1, label='dT/dt (нагревание, пустой)')
        
        # Находим точку, где T = Tk
        idx_Tk = np.argmin(np.abs(T_heat_all - Tk_heat))
        if idx_Tk < len(time_heat_all):
            dT_at_Tk = dT_dt_smooth[idx_Tk]
            C_est = None  # P / (dT/dt) при T=Tk
            ax4.plot(time_heat_all[idx_Tk], dT_at_Tk, 'ro', markersize=8, 
                    label=f'Точка T=Tk\ndT/dt = {dT_at_Tk:.3f}°C/с')
    
    # Вычисляем производные для охлаждения
    if cool_start > 0:
        dT_dt_cool = -np.gradient(T_cool_all, time_cool_all)
        dT_dt_cool_smooth = smooth_data(time_cool_all, dT_dt_cool, window=10)
        ax4.plot(time_cool_all, dT_dt_cool_smooth, 'r-', linewidth=1, label='dT/dt (охлаждение, пустой)')
    
    ax4.set_xlabel('Время, с')
    ax4.set_ylabel('dT/dt, °C/с')
    ax4.set_title('Производные кривых нагревания и охлаждения')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('lab_2_1_4_graphs.png', dpi=150, bbox_inches='tight')
    plt.show()
    
    # ==================== Расчёт теплоёмкостей ====================
    print("\n" + "="*60)
    print("РЕЗУЛЬТАТЫ РАСЧЁТА ТЕПЛОЁМКОСТЕЙ")
    print("="*60)
    
    # Интегральный метод: C = λ * τ
    # Для пустого калориметра
    lambda_cal = None  # будет вычислено из P/λ и τ
    # P/λ из аппроксимации, τ = C/λ
    # λ = P / (P/λ) = P / (ΔT_max)
    
    # Оценка мощности нагревателя (из данных)
    # Примерное значение, нужно уточнить по экспериментальным данным
    P_heater = 5.0  # Вт, примерное значение
    
    if tau > 0:
        C_cal_integral = P_heater * tau / (T_heat_all[-1] - Tk_heat)  # приблизительно
        print(f"\nПустой калориметр (интегральный метод):")
        print(f"  Теплоёмкость: {C_cal_integral:.2f} Дж/К")
        print(f"  Удельная теплоёмкость: {C_cal_integral / MASS_CALORIMETER:.2f} Дж/(кг·К)")
        print(f"  Теоретическое значение (медь): {C_THEORETICAL['calorimeter']:.0f} Дж/(кг·К)")
    
    # Дифференциальный метод (по формуле 16)
    if 'dT_at_Tk' in locals():
        C_cal_diff = P_heater / dT_at_Tk
        print(f"\nПустой калориметр (дифференциальный метод):")
        print(f"  Теплоёмкость: {C_cal_diff:.2f} Дж/К")
        print(f"  Удельная теплоёмкость: {C_cal_diff / MASS_CALORIMETER:.2f} Дж/(кг·К)")
    
    print("\n" + "="*60)
    print("ПРИМЕЧАНИЯ:")
    print("1. Мощность нагревателя (P) необходимо уточнить по данным измерений")
    print("2. Массы образцов следует скорректировать по данным лабораторной установки")
    print("3. Для точных расчётов используйте программную обработку с индивидуальными параметрами")
    print("="*60)


if __name__ == "__main__":
    main()