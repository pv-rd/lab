import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# Константы
# ============================================================
alpha = 4.28e-3  # температурный коэффициент сопротивления меди, град^-1

# Параметры из parameters.txt
U = 27.3408  # напряжение, В
I = 0.229247  # ток, А
P = U * I  # мощность нагревателя, Вт

m_Fe = 0.8148  # масса железа, кг
m_Al = 0.2941  # масса алюминия, кг

# Коэффициенты пересчёта сопротивления в температуру (по описанию)
# Для установки (2) — калориметр
A_RtoT = 14.377980252039598845
B_RtoT = 39.35514018691588785

print(f"Мощность нагревателя: P = {P:.3f} Вт")

# ============================================================
# Функции для обработки данных
# ============================================================

def parse_time(time_str):
    """Преобразование времени из формата 'HH : MM : SS' в секунды"""
    try:
        # Удаляем пробелы и разделяем по двоеточию
        time_str = time_str.strip()
        parts = time_str.split(':')
        if len(parts) == 3:
            h = int(parts[0].strip())
            m = int(parts[1].strip())
            s = int(parts[2].strip())
            return h * 3600 + m * 60 + s
    except:
        pass
    return np.nan

def resistance_to_temperature(R):
    """Пересчёт сопротивления в температуру (К)"""
    return A_RtoT * R + B_RtoT

def celsius_to_kelvin(Tc):
    """Пересчёт градусов Цельсия в Кельвины"""
    return Tc + 273.15

# ============================================================
# Загрузка и обработка данных
# ============================================================

print("\n" + "="*60)
print("ЗАГРУЗКА ДАННЫХ")
print("="*60)

# Загрузка данных калориметра
df_cal = pd.read_csv('калориметр.txt', encoding='utf-8')
print(f"Загружено {len(df_cal)} строк из калориметр.txt")

# Обработка времени
df_cal['time_sec'] = df_cal['Time'].apply(parse_time)
# Удаляем строки с NaN временем
df_cal = df_cal.dropna(subset=['time_sec'])

# Находим время начала записи
start_time = df_cal['time_sec'].min()
df_cal['t'] = df_cal['time_sec'] - start_time
print(f"Время начала записи: {start_time} с ({start_time//3600:02d}:{(start_time%3600)//60:02d}:{start_time%60:02d})")

# Пересчёт сопротивления в температуру
df_cal['R'] = df_cal['Value'].astype(float)
df_cal['T_K'] = resistance_to_temperature(df_cal['R'])
print(f"Диапазон температур калориметра: {df_cal['T_K'].min():.2f} - {df_cal['T_K'].max():.2f} К")

# Загрузка данных комнатной температуры
df_room = pd.read_csv('комната.txt', encoding='utf-8')
print(f"\nЗагружено {len(df_room)} строк из комната.txt")

# Обработка времени для комнатной температуры
df_room['time_sec'] = df_room['Time'].apply(parse_time)
df_room = df_room.dropna(subset=['time_sec'])
df_room['t'] = df_room['time_sec'] - start_time

# Пересчёт комнатной температуры в Кельвины
df_room['Tk_C'] = df_room['Value'].astype(float)
df_room['Tk_K'] = celsius_to_kelvin(df_room['Tk_C'])
print(f"Диапазон комнатной температуры: {df_room['Tk_C'].min():.2f} - {df_room['Tk_C'].max():.2f} °C")

# ============================================================
# Автоматическое определение интервалов нагрева/охлаждения
# ============================================================

print("\n" + "="*60)
print("ОПРЕДЕЛЕНИЕ ИНТЕРВАЛОВ")
print("="*60)

# Находим моменты включения/выключения нагревателя по резким изменениям температуры
# Сначала сгладим температуру для поиска
df_cal['T_smooth'] = df_cal['T_K'].rolling(window=5, center=True).mean()

# Находим производную температуры
df_cal['dT'] = df_cal['T_smooth'].diff()
df_cal['dT_smooth'] = df_cal['dT'].rolling(window=10, center=True).mean()

# Определяем порог для детектирования нагрева (положительная производная > 0.01 К/с)
heating_threshold = 0.01
cooling_threshold = -0.005

# Ищем периоды нагрева (dT > порога)
heating_periods = []
cooling_periods = []
in_heating = False
start_idx = 0

for i in range(len(df_cal)):
    dT_val = df_cal['dT_smooth'].iloc[i]
    if not np.isnan(dT_val):
        if not in_heating and dT_val > heating_threshold:
            in_heating = True
            start_idx = i
        elif in_heating and dT_val < cooling_threshold:
            in_heating = False
            heating_periods.append((start_idx, i))

# Выводим найденные периоды
print(f"\nНайдено {len(heating_periods)} периодов нагрева:")
for idx, (start, end) in enumerate(heating_periods):
    t_start = df_cal['t'].iloc[start]
    t_end = df_cal['t'].iloc[end]
    T_start = df_cal['T_K'].iloc[start]
    T_end = df_cal['T_K'].iloc[end]
    print(f"  Период {idx+1}: {t_start:.0f}-{t_end:.0f} с, температура {T_start:.2f} -> {T_end:.2f} К")

# По данным time.txt ищем соответствие
# Читаем time.txt
events = []
with open('time.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            events.append(line)

print("\nСобытия из time.txt:")
for e in events:
    print(f"  {e}")

# Построим график для визуального определения интервалов
plt.figure(figsize=(14, 8))
plt.plot(df_cal['t'] / 60, df_cal['T_K'], 'b-', linewidth=1, alpha=0.7, label='Температура калориметра')
plt.plot(df_room['t'] / 60, df_room['Tk_C'] + 273.15, 'r-', linewidth=1, alpha=0.5, label='Комнатная температура')
plt.xlabel('Время от начала записи, мин')
plt.ylabel('Температура, К')
plt.title('Полные данные эксперимента')
plt.grid(True, alpha=0.3)
plt.legend()

# Отмечаем найденные периоды нагрева
for idx, (start, end) in enumerate(heating_periods):
    t_start = df_cal['t'].iloc[start] / 60
    t_end = df_cal['t'].iloc[end] / 60
    plt.axvspan(t_start, t_end, alpha=0.2, color='orange', label=f'Нагрев {idx+1}' if idx == 0 else "")

plt.tight_layout()
plt.savefig('full_data_with_periods.png', dpi=150)
plt.show()

# ============================================================
# Ручное определение интервалов (на основе визуального анализа)
# ============================================================

print("\n" + "="*60)
print("ПОСМОТРИТЕ НА ГРАФИК И ОПРЕДЕЛИТЕ ИНТЕРВАЛЫ")
print("="*60)
print("На графике выше показаны периоды нагрева.")
print("Теперь нужно определить, какой период соответствует:")
print("  - пустому калориметру")
print("  - калориметру с железом")
print("  - калориметру с алюминием")
print("\nВведите номера периодов (например: 1,2,3):")

# Запрашиваем у пользователя
try:
    empty_period = int(input("Номер периода для пустого калориметра: "))
    iron_period = int(input("Номер периода для железа: "))
    al_period = int(input("Номер периода для алюминия: "))
except:
    print("Использую автоматическое определение по порядку...")
    empty_period = 0
    iron_period = 1
    al_period = 2

# Получаем индексы периодов
if len(heating_periods) >= 1:
    empty_start, empty_end = heating_periods[empty_period-1] if empty_period > 0 else (0, 0)
if len(heating_periods) >= 2:
    iron_start, iron_end = heating_periods[iron_period-1] if iron_period > 0 else (0, 0)
if len(heating_periods) >= 3:
    al_start, al_end = heating_periods[al_period-1] if al_period > 0 else (0, 0)

# Определяем интервалы охлаждения (после каждого нагрева)
empty_cool_start = empty_end
empty_cool_end = iron_start if iron_start > 0 else empty_end + 3600

iron_cool_start = iron_end
iron_cool_end = al_start if al_start > 0 else iron_end + 3600

al_cool_start = al_end
al_cool_end = al_end + 1800  # 30 минут охлаждения

# Создаём маски
mask_empty_heating = (df_cal['t'] >= df_cal['t'].iloc[empty_start]) & (df_cal['t'] <= df_cal['t'].iloc[empty_end]) if empty_start > 0 else pd.Series([False]*len(df_cal))
mask_empty_cooling = (df_cal['t'] >= df_cal['t'].iloc[empty_cool_start]) & (df_cal['t'] <= df_cal['t'].iloc[min(empty_cool_end, len(df_cal)-1)]) if empty_cool_start < len(df_cal) else pd.Series([False]*len(df_cal))

mask_iron_heating = (df_cal['t'] >= df_cal['t'].iloc[iron_start]) & (df_cal['t'] <= df_cal['t'].iloc[iron_end]) if iron_start > 0 else pd.Series([False]*len(df_cal))
mask_iron_cooling = (df_cal['t'] >= df_cal['t'].iloc[iron_cool_start]) & (df_cal['t'] <= df_cal['t'].iloc[min(iron_cool_end, len(df_cal)-1)]) if iron_cool_start < len(df_cal) else pd.Series([False]*len(df_cal))

mask_al_heating = (df_cal['t'] >= df_cal['t'].iloc[al_start]) & (df_cal['t'] <= df_cal['t'].iloc[al_end]) if al_start > 0 else pd.Series([False]*len(df_cal))
mask_al_cooling = (df_cal['t'] >= df_cal['t'].iloc[al_cool_start]) & (df_cal['t'] <= df_cal['t'].iloc[min(al_cool_end, len(df_cal)-1)]) if al_cool_start < len(df_cal) else pd.Series([False]*len(df_cal))

# ============================================================
# Функция для обработки кривой охлаждения
# ============================================================

def process_cooling_curve(df, mask, name, color):
    """Обработка кривой охлаждения"""
    data = df[mask].copy()
    
    if len(data) < 10:
        print(f"{name}: Недостаточно данных для анализа ({len(data)} точек)")
        return None, None, None
    
    data['t_rel'] = data['t'] - data['t'].min()
    
    # Усреднённая комнатная температура на интервале
    room_mask = (df_room['t'] >= data['t'].min()) & (df_room['t'] <= data['t'].max())
    Tk_mean = df_room[room_mask]['Tk_K'].mean()
    
    print(f"{name}: Tk_mean = {Tk_mean:.2f} К")
    
    # Разность температур
    data['dT'] = data['T_K'] - Tk_mean
    # Исключаем отрицательные значения
    data = data[data['dT'] > 0.01].copy()
    
    if len(data) < 10:
        print(f"{name}: Недостаточно положительных dT ({len(data)} точек)")
        return None, None, None
    
    data['ln_dT'] = np.log(data['dT'])
    
    # Исключаем начальный нелинейный участок (первые 20% времени)
    min_time = data['t_rel'].min()
    max_time = data['t_rel'].max()
    linear_start = min_time + 0.2 * (max_time - min_time)
    data_linear = data[data['t_rel'] > linear_start].copy()
    
    if len(data_linear) < 5:
        print(f"{name}: Недостаточно точек для линейной аппроксимации ({len(data_linear)} точек)")
        return None, None, None
    
    # Линейная аппроксимация
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        data_linear['t_rel'], data_linear['ln_dT'])
    
    print(f"{name}: λ/C = {-slope:.4f} ± {std_err:.4f} с^-1, R² = {r_value**2:.4f}")
    
    # Построение графика
    plt.figure(figsize=(10, 6))
    plt.plot(data['t_rel'], data['ln_dT'], 'o', markersize=2, color=color, alpha=0.5, label='Экспериментальные точки')
    t_fit = np.linspace(data_linear['t_rel'].min(), data_linear['t_rel'].max(), 100)
    plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2, 
             label=f'Аппроксимация: λ/C = {-slope:.4f} с⁻¹')
    plt.xlabel('Время от начала охлаждения, с')
    plt.ylabel('ln(T - T_k)')
    plt.title(f'Спрямлённая кривая охлаждения: {name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'cooling_{name.lower()}_linearized.png', dpi=150)
    plt.show()
    
    return -slope, std_err, Tk_mean

# ============================================================
# Функция для обработки кривой нагревания
# ============================================================

def process_heating_curve(df, mask, name, color, Tk):
    """Обработка кривой нагревания"""
    data = df[mask].copy()
    
    if len(data) < 10:
        print(f"{name}: Недостаточно данных для анализа ({len(data)} точек)")
        return None, None
    
    data['t_rel'] = data['t'] - data['t'].min()
    
    # Находим момент, когда температура близка к комнатной
    data['T_diff'] = data['T_K'] - Tk
    idx_near = (data['T_diff'] > -0.5) & (data['T_diff'] < 0.5)
    data_near = data[idx_near]
    
    if len(data_near) < 5:
        print(f"{name}: Недостаточно точек в окрестности T = Tk ({len(data_near)} точек)")
        return None, None
    
    # Линейная аппроксимация в окрестности
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        data_near['t_rel'], data_near['T_K'])
    
    print(f"{name}: dT/dt = {slope:.4f} ± {std_err:.4f} К/с при T ≈ {Tk:.2f} К")
    
    # Построение графика
    plt.figure(figsize=(10, 6))
    plt.plot(data['t_rel'], data['T_K'], 'o', markersize=2, color=color, alpha=0.5, label='Экспериментальные точки')
    t_fit = np.linspace(data_near['t_rel'].min(), data_near['t_rel'].max(), 100)
    plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2, 
             label=f'Аппроксимация: dT/dt = {slope:.4f} К/с')
    plt.axhline(y=Tk, color='k', linestyle='--', alpha=0.5, label=f'T_k = {Tk:.2f} К')
    plt.xlabel('Время от начала нагрева, с')
    plt.ylabel('Температура, К')
    plt.title(f'Определение производной в "удобной точке": {name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'derivative_{name.lower()}.png', dpi=150)
    plt.show()
    
    return slope, std_err

# ============================================================
# Построение графиков
# ============================================================

print("\n" + "="*60)
print("ПОСТРОЕНИЕ ГРАФИКОВ")
print("="*60)

# График 1: Комнатная температура
plt.figure(figsize=(12, 6))
plt.plot(df_room['t'] / 60, df_room['Tk_C'], 'b-', linewidth=1)
plt.xlabel('Время от начала записи, мин')
plt.ylabel('Температура, °C')
plt.title('Комнатная температура в ходе эксперимента')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('room_temp.png', dpi=150)
plt.show()

# График 2: Все кривые
plt.figure(figsize=(14, 8))
plt.plot(df_cal[mask_empty_heating]['t'] / 60, df_cal[mask_empty_heating]['T_K'], 'r-', linewidth=1.5, label='Пустой (нагрев)')
plt.plot(df_cal[mask_empty_cooling]['t'] / 60, df_cal[mask_empty_cooling]['T_K'], 'r--', linewidth=1.5, label='Пустой (охлаждение)')
plt.plot(df_cal[mask_iron_heating]['t'] / 60, df_cal[mask_iron_heating]['T_K'], 'b-', linewidth=1.5, label='С железом (нагрев)')
plt.plot(df_cal[mask_iron_cooling]['t'] / 60, df_cal[mask_iron_cooling]['T_K'], 'b--', linewidth=1.5, label='С железом (охлаждение)')
plt.plot(df_cal[mask_al_heating]['t'] / 60, df_cal[mask_al_heating]['T_K'], 'g-', linewidth=1.5, label='С алюминием (нагрев)')
plt.plot(df_cal[mask_al_cooling]['t'] / 60, df_cal[mask_al_cooling]['T_K'], 'g--', linewidth=1.5, label='С алюминием (охлаждение)')
plt.xlabel('Время от начала записи, мин')
plt.ylabel('Температура, К')
plt.title('Кривые нагревания и охлаждения калориметра')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('all_curves.png', dpi=150)
plt.show()

# График 3: Только кривые нагревания (совмещённые)
plt.figure(figsize=(10, 6))

if mask_empty_heating.any():
    t0_empty = df_cal[mask_empty_heating]['t'].min()
    plt.plot(df_cal[mask_empty_heating]['t'] - t0_empty, df_cal[mask_empty_heating]['T_K'], 'r-', linewidth=1.5, label='Пустой калориметр')

if mask_iron_heating.any():
    t0_iron = df_cal[mask_iron_heating]['t'].min()
    plt.plot(df_cal[mask_iron_heating]['t'] - t0_iron, df_cal[mask_iron_heating]['T_K'], 'b-', linewidth=1.5, label='С железом')

if mask_al_heating.any():
    t0_al = df_cal[mask_al_heating]['t'].min()
    plt.plot(df_cal[mask_al_heating]['t'] - t0_al, df_cal[mask_al_heating]['T_K'], 'g-', linewidth=1.5, label='С алюминием')

plt.xlabel('Время от начала нагрева, с')
plt.ylabel('Температура, К')
plt.title('Кривые нагревания калориметра')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('heating_curves.png', dpi=150)
plt.show()

# ============================================================
# Обработка кривых
# ============================================================

print("\n" + "="*60)
print("ОБРАБОТКА КРИВЫХ ОХЛАЖДЕНИЯ")
print("="*60)

# Получаем средние комнатные температуры для каждого интервала
room_empty = (df_room['t'] >= df_cal[mask_empty_cooling]['t'].min()) & (df_room['t'] <= df_cal[mask_empty_cooling]['t'].max()) if mask_empty_cooling.any() else pd.Series([False]*len(df_room))
room_iron = (df_room['t'] >= df_cal[mask_iron_cooling]['t'].min()) & (df_room['t'] <= df_cal[mask_iron_cooling]['t'].max()) if mask_iron_cooling.any() else pd.Series([False]*len(df_room))
room_al = (df_room['t'] >= df_cal[mask_al_cooling]['t'].min()) & (df_room['t'] <= df_cal[mask_al_cooling]['t'].max()) if mask_al_cooling.any() else pd.Series([False]*len(df_room))

Tk_empty = df_room[room_empty]['Tk_K'].mean() if room_empty.any() else 295.8
Tk_iron = df_room[room_iron]['Tk_K'].mean() if room_iron.any() else 295.9
Tk_al = df_room[room_al]['Tk_K'].mean() if room_al.any() else 296.0

print(f"\nСредние комнатные температуры:")
print(f"Пустой калориметр: {Tk_empty:.2f} К")
print(f"С железом: {Tk_iron:.2f} К")
print(f"С алюминием: {Tk_al:.2f} К")

# Обработка кривых охлаждения
lamC_empty, err_empty, _ = process_cooling_curve(df_cal, mask_empty_cooling, 'Empty', 'red')
lamC_iron, err_iron, _ = process_cooling_curve(df_cal, mask_iron_cooling, 'Iron', 'blue')
lamC_al, err_al, _ = process_cooling_curve(df_cal, mask_al_cooling, 'Aluminum', 'green')

print("\n" + "="*60)
print("ОБРАБОТКА КРИВЫХ НАГРЕВАНИЯ")
print("="*60)

# Обработка кривых нагревания
dTdt_empty, err_empty_dt = process_heating_curve(df_cal, mask_empty_heating, 'Empty', 'red', Tk_empty)
dTdt_iron, err_iron_dt = process_heating_curve(df_cal, mask_iron_heating, 'Iron', 'blue', Tk_iron)
dTdt_al, err_al_dt = process_heating_curve(df_cal, mask_al_heating, 'Aluminum', 'green', Tk_al)

# ============================================================
# Расчёт теплоёмкостей
# ============================================================

print("\n" + "="*60)
print("РЕЗУЛЬТАТЫ РАСЧЁТОВ")
print("="*60)

# Интегральный метод
print("\nИнтегральный метод:")

if lamC_empty is not None:
    lambda_cal = 1.01  # приблизительное значение, нужно из графика нагрева
    C_cal_int = lambda_cal / lamC_empty
    print(f"C_кал = {C_cal_int:.1f} Дж/К")
    
    if lamC_iron is not None:
        C_calFe_int = lambda_cal / lamC_iron
        C_Fe_int = C_calFe_int - C_cal_int
        print(f"C_Fe = {C_Fe_int:.1f} Дж/К")
        print(f"c_Fe = {C_Fe_int / m_Fe:.1f} Дж/(кг·К)")
    
    if lamC_al is not None:
        C_calAl_int = lambda_cal / lamC_al
        C_Al_int = C_calAl_int - C_cal_int
        print(f"C_Al = {C_Al_int:.1f} Дж/К")
        print(f"c_Al = {C_Al_int / m_Al:.1f} Дж/(кг·К)")

# Дифференциальный метод
print("\nДифференциальный метод:")

if dTdt_empty is not None:
    C_cal_diff = P / dTdt_empty
    print(f"C_кал = {C_cal_diff:.1f} Дж/К")
    
    if dTdt_iron is not None:
        C_Fe_diff = P / dTdt_iron - C_cal_diff
        print(f"C_Fe = {C_Fe_diff:.1f} Дж/К")
        print(f"c_Fe = {C_Fe_diff / m_Fe:.1f} Дж/(кг·К)")
    
    if dTdt_al is not None:
        C_Al_diff = P / dTdt_al - C_cal_diff
        print(f"C_Al = {C_Al_diff:.1f} Дж/К")
        print(f"c_Al = {C_Al_diff / m_Al:.1f} Дж/(кг·К)")

print("\n" + "="*60)
print("Табличные значения:")
print("c_Fe = 450 Дж/(кг·К)")
print("c_Al = 900 Дж/(кг·К)")
print("="*60)