import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# 1. ЗАГРУЗКА ДАННЫХ
# ============================================================
# Данные из файла: температура (°C) и разность высот (в сотых долях мм)
data_text = """22.0	2762
23.1	2973
24.1	3089
25.1	3345
26.1	3426
27.1	3708
28.1	3909
29.1	4118
30.1	4429
31.0	4667
32.0	4953
33.0	5176
34.0	5483
35.0	5796
36.0	6101
37.0	6433
38.0	6780
39.0	7136
40.0	7541
39.0	7333
38.0	6862
37.0	6553
36.0	6319
35.0	5887
34.0	5652
33.0	5371
32.0	5049
31.0	4880
30.0	4580
29.0	4357
28.0	4112
27.0	3825
26.0	3613"""

# Парсим текстовые данные в массивы
lines = data_text.strip().split('\n')
t_data = []
dh_data = []

for line in lines:
    parts = line.split('\t')
    t_data.append(float(parts[0]))
    dh_data.append(float(parts[1]))

# Преобразуем в numpy массивы
t = np.array(t_data)
dh_hundredths = np.array(dh_data)

# ============================================================
# 2. РАЗДЕЛЕНИЕ НА НАГРЕВ И ОХЛАЖДЕНИЕ
# ============================================================
# Первые 19 точек (с 22.0 до 40.0) - нагрев, остальные - охлаждение
n_heat = 19
t_heat = t[:n_heat]
t_cool = t[n_heat:]
dh_heat = dh_hundredths[:n_heat]
dh_cool = dh_hundredths[n_heat:]

# ============================================================
# 3. РАСЧЁТ ДАВЛЕНИЯ
# ============================================================
# Константы
rho_Hg = 13546          # кг/м³ при 0°C
g = 9.81                # м/с²
mmHg_to_Pa = 133.322    # 1 мм рт. ст. = 133.322 Па

# Перевод разности высот из сотых долей мм в метры
dh_m_heat = dh_heat * 1e-5
dh_m_cool = dh_cool * 1e-5
dh_m_all = dh_hundredths * 1e-5

# Расчёт давления в Паскалях и мм рт. ст. для всех точек
P_Pa_all = rho_Hg * g * dh_m_all
P_mmHg_all = P_Pa_all / mmHg_to_Pa

# Для нагрева и охлаждения отдельно
P_Pa_heat = rho_Hg * g * dh_m_heat
P_mmHg_heat = P_Pa_heat / mmHg_to_Pa

P_Pa_cool = rho_Hg * g * dh_m_cool
P_mmHg_cool = P_Pa_cool / mmHg_to_Pa

# Перевод температуры в Кельвины
T_K_all = t + 273.15
T_K_heat = t_heat + 273.15
T_K_cool = t_cool + 273.15

# ============================================================
# 4. ПОДГОТОВКА ДАННЫХ ДЛЯ ЛИНЕАРИЗОВАННОГО ГРАФИКА
# ============================================================
ln_P_all = np.log(P_mmHg_all)
inv_T_all = 1 / T_K_all
inv_T_1000_all = inv_T_all * 1000  # для удобства (10³/К)

ln_P_heat = np.log(P_mmHg_heat)
inv_T_1000_heat = (1 / T_K_heat) * 1000

ln_P_cool = np.log(P_mmHg_cool)
inv_T_1000_cool = (1 / T_K_cool) * 1000

# ============================================================
# 5. МЕТОД НАИМЕНЬШИХ КВАДРАТОВ (МНК) вручную
# ============================================================
# Расчёт коэффициентов линейной регрессии y = a*x + b
# где x = inv_T_all, y = ln_P_all
x_all = inv_T_all
y_all = ln_P_all
n = len(x_all)

# Средние значения
x_mean = np.mean(x_all)
y_mean = np.mean(y_all)

# Расчёт коэффициентов
numerator = np.sum((x_all - x_mean) * (y_all - y_mean))
denominator = np.sum((x_all - x_mean)**2)
slope = numerator / denominator  # наклон (a)
intercept = y_mean - slope * x_mean  # свободный член (b)

# Расчёт коэффициента детерминации R²
y_pred_lin = slope * x_all + intercept
ss_res = np.sum((y_all - y_pred_lin)**2)
ss_tot = np.sum((y_all - y_mean)**2)
r_squared = 1 - (ss_res / ss_tot)

# Расчёт стандартной ошибки наклона
residuals = y_all - y_pred_lin
residual_variance = np.sum(residuals**2) / (n - 2)
std_err = np.sqrt(residual_variance / denominator)

# Расчёт теплоты испарения
L_calc = -slope * 8.314  # Дж/моль
L_calc_kJ = L_calc / 1000  # кДж/моль

print("="*60)
print("РЕЗУЛЬТАТЫ МНК-АНАЛИЗА (линеаризованный график)")
print("="*60)
print(f"Уравнение регрессии: ln(P) = ({slope:.2f} ± {std_err:.2f}) * (1/T) + {intercept:.3f}")
print(f"Коэффициент детерминации R² = {r_squared:.6f}")
print(f"Стандартная ошибка наклона: {std_err:.4f}")
print(f"\nМолярная теплота испарения:")
print(f"L = {L_calc:.1f} Дж/моль")
print(f"L = {L_calc_kJ:.2f} кДж/моль")
print("="*60)

# ============================================================
# 6. ЭКСПОНЕНЦИАЛЬНАЯ АППРОКСИМАЦИЯ ДЛЯ ГРАФИКА P(T)
# ============================================================
# Из линейной регрессии получаем параметры экспоненты:
# P = exp(intercept) * exp(slope / T) = A * exp(B/T)
# где B = slope, A = exp(intercept)

A = np.exp(intercept)
B = slope

print("\n" + "="*60)
print("ЭКСПОНЕНЦИАЛЬНАЯ АППРОКСИМАЦИЯ P(T)")
print("="*60)
print(f"P = {A:.4f} * exp({B:.2f} / T)")
print(f"где T - температура в Кельвинах, P - в мм рт. ст.")

# Расчёт теоретической кривой для графика P(T)
T_fit = np.linspace(min(T_K_all), max(T_K_all), 200)
P_fit_exp = A * np.exp(B / T_fit)

# Оценка качества экспоненциальной аппроксимации
P_pred_exp = A * np.exp(B / T_K_all)
ss_res_exp = np.sum((P_mmHg_all - P_pred_exp)**2)
ss_tot_exp = np.sum((P_mmHg_all - np.mean(P_mmHg_all))**2)
r_squared_exp = 1 - (ss_res_exp / ss_tot_exp)
rmse_exp = np.sqrt(np.mean((P_mmHg_all - P_pred_exp)**2))

print(f"\nКачество экспоненциальной аппроксимации:")
print(f"R² = {r_squared_exp:.6f}")
print(f"RMSE = {rmse_exp:.2f} мм рт. ст.")

# ============================================================
# 7. ПОСТРОЕНИЕ ГРАФИКОВ
# ============================================================

# Устанавливаем стиль для графиков
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.linewidth'] = 1.5
plt.rcParams['lines.linewidth'] = 2
plt.rcParams['lines.markersize'] = 6

# -------------------------------------------------------------------
# ГРАФИК 1: Зависимость P(T) с экспоненциальной аппроксимацией
# -------------------------------------------------------------------
fig1, ax1 = plt.subplots(figsize=(8, 6))

# Точки нагрева и охлаждения разными маркерами
ax1.plot(T_K_heat, P_mmHg_heat, 
         's', color='red', label='Нагревание (эксперимент)', markersize=6, 
         markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='red')
ax1.plot(T_K_cool, P_mmHg_cool, 
         '^', color='blue', label='Охлаждение (эксперимент)', markersize=6, 
         markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='blue')

# Экспоненциальная аппроксимация
ax1.plot(T_fit, P_fit_exp, 'g-', linewidth=2, 
         label=f'Эксп. аппроксимация: P = {A:.2f}·exp({B:.0f}/T)')

# Настройка осей
ax1.set_xlabel('Температура $T$, К', fontsize=12)
ax1.set_ylabel('Давление $P$, мм рт. ст.', fontsize=12)

# Сетка (только вспомогательные линии)
ax1.grid(True, which='both', linestyle=':', linewidth=0.5, color='gray')

# Легенда
ax1.legend(loc='upper left', frameon=True, fancybox=False, edgecolor='black')

# Убираем лишние верхнюю и правую границы
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)

# Название
ax1.set_title('Рис. 1. Зависимость давления насыщенного пара воды от температуры\nс экспоненциальной аппроксимацией', 
              fontsize=12, pad=10)

plt.tight_layout()

# -------------------------------------------------------------------
# ГРАФИК 2: Линеаризованный график ln(P) от 1/T
# -------------------------------------------------------------------
fig2, ax2 = plt.subplots(figsize=(8, 6))

# Точки нагрева и охлаждения
ax2.plot(inv_T_1000_heat, ln_P_heat, 
         's', color='red', label='Нагревание', markersize=6, 
         markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='red')
ax2.plot(inv_T_1000_cool, ln_P_cool, 
         '^', color='blue', label='Охлаждение', markersize=6, 
         markerfacecolor='white', markeredgewidth=1.5, markeredgecolor='blue')

# Линия регрессии
x_fit = np.linspace(min(inv_T_1000_all), max(inv_T_1000_all), 100)
y_fit = slope * (x_fit / 1000) + intercept  # обратное преобразование масштаба
ax2.plot(x_fit, y_fit, 'k-', linewidth=2, label=f'МНК: ln P = {slope:.2f}/T + {intercept:.3f}')

# Настройка осей
ax2.set_xlabel('$10^3/T$, $10^3$·К$^{-1}$', fontsize=12)
ax2.set_ylabel('$\ln P$', fontsize=12)

# Сетка
ax2.grid(True, which='both', linestyle=':', linewidth=0.5, color='gray')

# Легенда
ax2.legend(loc='upper right', frameon=True, fancybox=False, edgecolor='black')

# Убираем лишние границы
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)

# Название
ax2.set_title('Рис. 2. Линеаризованный график для определения теплоты испарения', 
              fontsize=12, pad=10)

plt.tight_layout()

# -------------------------------------------------------------------
# ГРАФИК 3: Сравнение аппроксимаций (остатки)
# -------------------------------------------------------------------
fig3, ax3 = plt.subplots(figsize=(8, 4))

# Остатки линейной аппроксимации (на линеаризованном графике)
residuals_plot = y_all - y_pred_lin
ax3.plot(T_K_all, residuals_plot, 'o', color='purple', 
         markersize=4, markerfacecolor='white', markeredgewidth=1)
ax3.axhline(y=0, color='black', linestyle='-', linewidth=1)

ax3.set_xlabel('Температура $T$, К', fontsize=12)
ax3.set_ylabel('Остатки $\ln(P)$', fontsize=12)
ax3.set_title('Рис. 3. Остатки линейной регрессии', fontsize=12, pad=10)
ax3.grid(True, which='both', linestyle=':', linewidth=0.5, color='gray')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)

plt.tight_layout()

# ============================================================
# 8. ВЫВОД ТАБЛИЦЫ ДАННЫХ В КОНСОЛЬ
# ============================================================
print("\n" + "="*100)
print("ТАБЛИЦА ЭКСПЕРИМЕНТАЛЬНЫХ ДАННЫХ")
print("="*100)
print(f"{'Режим':<10} {'t, °C':<8} {'T, K':<10} {'Δh, 0.01 мм':<14} {'P, Па':<12} {'P, мм рт.ст.':<14} {'ln P':<10} {'P теор':<10}")
print("-"*120)

P_theor = A * np.exp(B / T_K_all)

for i in range(n_heat):
    print(f"{'Нагрев':<10} {t_heat[i]:<8.1f} {T_K_heat[i]:<10.2f} {dh_heat[i]:<14.0f} {P_Pa_heat[i]:<12.1f} {P_mmHg_heat[i]:<14.2f} {ln_P_heat[i]:<10.4f} {P_theor[i]:<10.2f}")

for i in range(len(t_cool)):
    j = i + n_heat
    print(f"{'Охл':<10} {t_cool[i]:<8.1f} {T_K_cool[i]:<10.2f} {dh_cool[i]:<14.0f} {P_Pa_cool[i]:<12.1f} {P_mmHg_cool[i]:<14.2f} {ln_P_cool[i]:<10.4f} {P_theor[j]:<10.2f}")

print("="*100)

# ============================================================
# 9. ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ДЛЯ ОТЧЁТА
# ============================================================
print("\n" + "="*60)
print("КОНТРОЛЬ КАЧЕСТВА АППРОКСИМАЦИИ")
print("="*60)

# Остатки регрессии
rmse = np.sqrt(np.mean(residuals**2))
print(f"Среднеквадратичная ошибка аппроксимации (RMSE) для ln(P): {rmse:.4f}")
print(f"Максимальное отклонение от прямой: {np.max(np.abs(residuals)):.4f}")

# Доверительный интервал для теплоты испарения (95%)
t_value = 2.0  # приближение для 95% при n>30
slope_ci = t_value * std_err
L_ci = 8.314 * slope_ci / 1000  # в кДж/моль

print(f"\n95% доверительный интервал для наклона: [{slope - slope_ci:.2f}, {slope + slope_ci:.2f}]")
print(f"95% доверительный интервал для L: [{L_calc_kJ - L_ci:.2f}, {L_calc_kJ + L_ci:.2f}] кДж/моль")

# Сравнение с табличным значением
L_table_25C = 44.0  # кДж/моль при 25°C
L_table_100C = 40.7  # кДж/моль при 100°C
print(f"\nСравнение с табличными данными:")
print(f"Эксперимент (22-40°C): L = {L_calc_kJ:.2f} кДж/моль")
print(f"Табличное значение (25°C): {L_table_25C:.1f} кДж/моль")
print(f"Табличное значение (100°C): {L_table_100C:.1f} кДж/моль")
print("="*60)

# Показываем графики
plt.show()