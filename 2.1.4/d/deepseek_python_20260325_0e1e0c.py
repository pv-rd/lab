import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# КОНСТАНТЫ
# ============================================================

# Параметры из parameters.txt
U = 27.3408      # напряжение, В
I = 0.229247     # ток, А
P = U * I        # мощность нагревателя = 6.268 Вт

m_Fe = 0.8148    # масса железа, кг
m_Al = 0.2941    # масса алюминия, кг

# Коэффициенты пересчёта сопротивления в температуру
A_RtoT = 14.377980252039598845
B_RtoT = 39.35514018691588785

# Время старта записи (из файла калориметр.txt)
START_HOUR = 22
START_MIN = 35
START_SEC = 38
START_SECONDS = START_HOUR * 3600 + START_MIN * 60 + START_SEC

# Времена событий из time.txt (реальное время)
# и их перевод в секунды от старта записи
# Предполагаем, что компьютерное время на 12 часов впереди реального
# 22:35:38 (комп) = 10:35:38 (реал)
# Поэтому реальное время + 12 часов = компьютерное

def real_to_computer(hour, minute, second):
    """Перевод реального времени в компьютерное (от старта записи)"""
    computer_hour = hour + 12
    if computer_hour >= 24:
        computer_hour -= 24
    computer_seconds = computer_hour * 3600 + minute * 60 + second
    return computer_seconds - START_SECONDS

# События из time.txt
events = {
    'temp_start': (10, 40, 0),      # температура растёт
    'heater_on_empty': (10, 46, 0), # включение без образца
    'heater_off_empty': (11, 6, 0), # выключение
    'cooling_empty_end': (11, 20, 0), # охлаждение (начало роста)
    'temp_rise': (11, 26, 0),       # рост температуры
    'heater_on_iron': (11, 31, 0),  # включение с железом
    'heater_off_iron': (11, 50, 0), # выключение
    'cooling_iron_end': (12, 8, 0), # охлаждение (начало роста)
    'heater_on_al': (12, 18, 0),    # включение с алюминием
    'heater_off_al': (12, 25, 0),   # выключение
}

# Вычисляем времена в секундах от старта
t_empty_on = real_to_computer(*events['heater_on_empty'])
t_empty_off = real_to_computer(*events['heater_off_empty'])
t_empty_cool_end = real_to_computer(*events['cooling_empty_end'])

t_iron_on = real_to_computer(*events['heater_on_iron'])
t_iron_off = real_to_computer(*events['heater_off_iron'])
t_iron_cool_end = real_to_computer(*events['cooling_iron_end'])

t_al_on = real_to_computer(*events['heater_on_al'])
t_al_off = real_to_computer(*events['heater_off_al'])

print("="*60)
print("ВРЕМЕННЫЕ ИНТЕРВАЛЫ (секунды от старта записи)")
print("="*60)
print(f"Пустой калориметр: нагрев {t_empty_on} - {t_empty_off} с")
print(f"                  охлаждение {t_empty_off} - {t_empty_cool_end} с")
print(f"Железо:           нагрев {t_iron_on} - {t_iron_off} с")
print(f"                  охлаждение {t_iron_off} - {t_iron_cool_end} с")
print(f"Алюминий:         нагрев {t_al_on} - {t_al_off} с")
print(f"                  охлаждение {t_al_off} - {t_al_off + 900} с (15 минут)")
print("="*60)

# ============================================================
# ЗАГРУЗКА ДАННЫХ
# ============================================================

print("\nЗагрузка данных...")

# Загрузка калориметра
df_cal = pd.read_csv('калориметр.txt', encoding='utf-8')

# Парсим время
def parse_time(time_str):
    try:
        time_str = time_str.strip()
        h = int(time_str[0:2])
        m = int(time_str[5:7])
        s = int(time_str[8:10])
        return h * 3600 + m * 60 + s
    except:
        return np.nan

df_cal['time_sec'] = df_cal['Time'].apply(parse_time)
df_cal = df_cal.dropna(subset=['time_sec'])
df_cal['t'] = df_cal['time_sec'] - START_SECONDS
df_cal['R'] = df_cal['Value'].astype(float)
df_cal['T_K'] = A_RtoT * df_cal['R'] + B_RtoT

# Загрузка комнатной температуры
df_room = pd.read_csv('комната.txt', encoding='utf-8')
df_room['time_sec'] = df_room['Time'].apply(parse_time)
df_room = df_room.dropna(subset=['time_sec'])
df_room['t'] = df_room['time_sec'] - START_SECONDS
df_room['Tk_C'] = df_room['Value'].astype(float)
df_room['Tk_K'] = df_room['Tk_C'] + 273.15

print(f"Загружено {len(df_cal)} точек калориметра")
print(f"Загружено {len(df_room)} точек комнатной температуры")

# ============================================================
# ВЫДЕЛЕНИЕ ИНТЕРВАЛОВ
# ============================================================

mask_empty_heat = (df_cal['t'] >= t_empty_on) & (df_cal['t'] <= t_empty_off)
mask_empty_cool = (df_cal['t'] >= t_empty_off) & (df_cal['t'] <= t_empty_cool_end)

mask_iron_heat = (df_cal['t'] >= t_iron_on) & (df_cal['t'] <= t_iron_off)
mask_iron_cool = (df_cal['t'] >= t_iron_off) & (df_cal['t'] <= t_iron_cool_end)

mask_al_heat = (df_cal['t'] >= t_al_on) & (df_cal['t'] <= t_al_off)
mask_al_cool = (df_cal['t'] >= t_al_off) & (df_cal['t'] <= t_al_off + 900)

# Комнатная температура для каждого интервала
room_empty = (df_room['t'] >= t_empty_on) & (df_room['t'] <= t_empty_cool_end)
room_iron = (df_room['t'] >= t_iron_on) & (df_room['t'] <= t_iron_cool_end)
room_al = (df_room['t'] >= t_al_on) & (df_room['t'] <= t_al_off + 900)

Tk_empty = df_room[room_empty]['Tk_K'].mean()
Tk_iron = df_room[room_iron]['Tk_K'].mean()
Tk_al = df_room[room_al]['Tk_K'].mean()

print(f"\nСредняя комнатная температура:")
print(f"  Пустой: {Tk_empty:.2f} К")
print(f"  Железо: {Tk_iron:.2f} К")
print(f"  Алюминий: {Tk_al:.2f} К")

# ============================================================
# ГРАФИК 1: Все кривые
# ============================================================

plt.figure(figsize=(14, 8))

plt.plot(df_cal[mask_empty_heat]['t']/60, df_cal[mask_empty_heat]['T_K'], 
         'r-', linewidth=2, label='Пустой (нагрев)')
plt.plot(df_cal[mask_empty_cool]['t']/60, df_cal[mask_empty_cool]['T_K'], 
         'r--', linewidth=2, label='Пустой (охлаждение)')

plt.plot(df_cal[mask_iron_heat]['t']/60, df_cal[mask_iron_heat]['T_K'], 
         'b-', linewidth=2, label='Железо (нагрев)')
plt.plot(df_cal[mask_iron_cool]['t']/60, df_cal[mask_iron_cool]['T_K'], 
         'b--', linewidth=2, label='Железо (охлаждение)')

plt.plot(df_cal[mask_al_heat]['t']/60, df_cal[mask_al_heat]['T_K'], 
         'g-', linewidth=2, label='Алюминий (нагрев)')
plt.plot(df_cal[mask_al_cool]['t']/60, df_cal[mask_al_cool]['T_K'], 
         'g--', linewidth=2, label='Алюминий (охлаждение)')

plt.axhline(y=Tk_empty, color='r', linestyle=':', alpha=0.5, label=f'T_k пустого = {Tk_empty:.1f} K')
plt.axhline(y=Tk_iron, color='b', linestyle=':', alpha=0.5, label=f'T_k железа = {Tk_iron:.1f} K')
plt.axhline(y=Tk_al, color='g', linestyle=':', alpha=0.5, label=f'T_k алюминия = {Tk_al:.1f} K')

plt.xlabel('Время от начала записи, мин')
plt.ylabel('Температура, K')
plt.title('Кривые нагревания и охлаждения калориметра')
plt.grid(True, alpha=0.3)
plt.legend(loc='best', fontsize=9)
plt.tight_layout()
plt.savefig('all_curves.png', dpi=150)
plt.show()

# ============================================================
# ГРАФИК 2: Комнатная температура
# ============================================================

plt.figure(figsize=(12, 5))
plt.plot(df_room['t']/60, df_room['Tk_C'], 'b-', linewidth=1)
plt.xlabel('Время от начала записи, мин')
plt.ylabel('Температура, °C')
plt.title('Комнатная температура в ходе эксперимента')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('room_temp.png', dpi=150)
plt.show()

# ============================================================
# ГРАФИК 3: Спрямлённые кривые охлаждения
# ============================================================

def plot_cooling_linearized(data, Tk, name, color):
    """Построение спрямлённой кривой охлаждения"""
    if len(data) < 10:
        print(f"{name}: недостаточно данных")
        return None
    
    t_rel = data['t'] - data['t'].min()
    dT = data['T_K'] - Tk
    dT = dT[dT > 0.01]  # убираем отрицательные
    t_rel = t_rel.iloc[:len(dT)]
    
    if len(dT) < 10:
        print(f"{name}: недостаточно положительных dT")
        return None
    
    ln_dT = np.log(dT)
    
    # Исключаем начальный нелинейный участок (первые 180 секунд)
    mask_linear = t_rel > 180
    t_linear = t_rel[mask_linear]
    ln_linear = ln_dT[mask_linear]
    
    if len(t_linear) < 5:
        print(f"{name}: недостаточно точек для аппроксимации")
        return None
    
    # Линейная аппроксимация
    slope, intercept, r, p, std_err = stats.linregress(t_linear, ln_linear)
    
    print(f"{name}: λ/C = {-slope:.4f} ± {std_err:.4f} с⁻¹, R² = {r**2:.4f}")
    
    # График
    plt.figure(figsize=(10, 6))
    plt.plot(t_rel, ln_dT, 'o', markersize=2, color=color, alpha=0.5, label='Эксперимент')
    t_fit = np.linspace(t_linear.min(), t_linear.max(), 100)
    plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2, 
             label=f'Аппроксимация: λ/C = {-slope:.4f} с⁻¹')
    plt.xlabel('Время от начала охлаждения, с')
    plt.ylabel('ln(T - T_k)')
    plt.title(f'Спрямлённая кривая охлаждения: {name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'cooling_{name}_linearized.png', dpi=150)
    plt.show()
    
    return -slope

print("\n" + "="*60)
print("ОБРАБОТКА КРИВЫХ ОХЛАЖДЕНИЯ")
print("="*60)

lamC_empty = plot_cooling_linearized(df_cal[mask_empty_cool], Tk_empty, 'empty', 'red')
lamC_iron = plot_cooling_linearized(df_cal[mask_iron_cool], Tk_iron, 'iron', 'blue')
lamC_al = plot_cooling_linearized(df_cal[mask_al_cool], Tk_al, 'aluminum', 'green')

# ============================================================
# ГРАФИК 4: Определение производной в точке T = Tk
# ============================================================

def plot_derivative(data, Tk, name, color):
    """Определение производной в точке T = Tk"""
    if len(data) < 10:
        print(f"{name}: недостаточно данных")
        return None
    
    t_rel = data['t'] - data['t'].min()
    T = data['T_K']
    
    # Находим точки вблизи Tk
    idx_near = (T > Tk - 0.5) & (T < Tk + 0.5)
    t_near = t_rel[idx_near]
    T_near = T[idx_near]
    
    if len(t_near) < 5:
        print(f"{name}: недостаточно точек вблизи Tk")
        return None
    
    # Линейная аппроксимация
    slope, intercept, r, p, std_err = stats.linregress(t_near, T_near)
    
    print(f"{name}: dT/dt = {slope:.4f} ± {std_err:.4f} К/с при T ≈ {Tk:.2f} K")
    
    # График
    plt.figure(figsize=(10, 6))
    plt.plot(t_rel, T, 'o', markersize=2, color=color, alpha=0.5, label='Эксперимент')
    t_fit = np.linspace(t_near.min(), t_near.max(), 100)
    plt.plot(t_fit, slope * t_fit + intercept, 'r-', linewidth=2,
             label=f'Аппроксимация: dT/dt = {slope:.4f} К/с')
    plt.axhline(y=Tk, color='k', linestyle='--', alpha=0.5, label=f'T_k = {Tk:.2f} K')
    plt.xlabel('Время от начала нагрева, с')
    plt.ylabel('Температура, K')
    plt.title(f'Определение производной в "удобной точке": {name}')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f'derivative_{name}.png', dpi=150)
    plt.show()
    
    return slope

print("\n" + "="*60)
print("ОБРАБОТКА КРИВЫХ НАГРЕВАНИЯ")
print("="*60)

dTdt_empty = plot_derivative(df_cal[mask_empty_heat], Tk_empty, 'empty', 'red')
dTdt_iron = plot_derivative(df_cal[mask_iron_heat], Tk_iron, 'iron', 'blue')
dTdt_al = plot_derivative(df_cal[mask_al_heat], Tk_al, 'aluminum', 'green')

# ============================================================
# ГРАФИК 5: Кривые нагревания (совмещённые)
# ============================================================

plt.figure(figsize=(10, 6))

t0_empty = df_cal[mask_empty_heat]['t'].min()
plt.plot(df_cal[mask_empty_heat]['t'] - t0_empty, df_cal[mask_empty_heat]['T_K'], 
         'r-', linewidth=2, label='Пустой калориметр')

t0_iron = df_cal[mask_iron_heat]['t'].min()
plt.plot(df_cal[mask_iron_heat]['t'] - t0_iron, df_cal[mask_iron_heat]['T_K'], 
         'b-', linewidth=2, label='С железом')

t0_al = df_cal[mask_al_heat]['t'].min()
plt.plot(df_cal[mask_al_heat]['t'] - t0_al, df_cal[mask_al_heat]['T_K'], 
         'g-', linewidth=2, label='С алюминием')

plt.xlabel('Время от начала нагрева, с')
plt.ylabel('Температура, K')
plt.title('Кривые нагревания калориметра')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig('heating_curves.png', dpi=150)
plt.show()

# ============================================================
# РАСЧЁТ ТЕПЛОЁМКОСТЕЙ
# ============================================================

print("\n" + "="*60)
print("РЕЗУЛЬТАТЫ РАСЧЁТОВ")
print("="*60)

# Для интегрального метода нужно определить λ из кривой нагрева
# Берём максимальную разность температур из графика
if mask_empty_heat.any():
    T_max_empty = df_cal[mask_empty_heat]['T_K'].max()
    deltaT_empty = T_max_empty - Tk_empty
    lambda_cal = P / deltaT_empty
    print(f"\nλ (из нагрева пустого) = {lambda_cal:.3f} Вт/К")

# Интегральный метод
print("\n--- Интегральный метод ---")

if lamC_empty and lambda_cal:
    C_cal = lambda_cal / lamC_empty
    print(f"C_кал = {C_cal:.1f} Дж/К")
    
    if lamC_iron:
        C_calFe = lambda_cal / lamC_iron
        C_Fe = C_calFe - C_cal
        print(f"C_Fe = {C_Fe:.1f} Дж/К")
        print(f"c_Fe = {C_Fe / m_Fe:.1f} Дж/(кг·К)")
    
    if lamC_al:
        C_calAl = lambda_cal / lamC_al
        C_Al = C_calAl - C_cal
        print(f"C_Al = {C_Al:.1f} Дж/К")
        print(f"c_Al = {C_Al / m_Al:.1f} Дж/(кг·К)")

# Дифференциальный метод
print("\n--- Дифференциальный метод (T = T_k) ---")

if dTdt_empty:
    C_cal_diff = P / dTdt_empty
    print(f"C_кал = {C_cal_diff:.1f} Дж/К")
    
    if dTdt_iron:
        C_Fe_diff = P / dTdt_iron - C_cal_diff
        print(f"C_Fe = {C_Fe_diff:.1f} Дж/К")
        print(f"c_Fe = {C_Fe_diff / m_Fe:.1f} Дж/(кг·К)")
    
    if dTdt_al:
        C_Al_diff = P / dTdt_al - C_cal_diff
        print(f"C_Al = {C_Al_diff:.1f} Дж/К")
        print(f"c_Al = {C_Al_diff / m_Al:.1f} Дж/(кг·К)")

print("\n" + "="*60)
print("Табличные значения:")
print("c_Fe = 450 Дж/(кг·К)")
print("c_Al = 900 Дж/(кг·К)")
print("="*60)